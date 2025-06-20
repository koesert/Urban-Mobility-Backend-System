import pytest
import os
import tempfile
import json
import zipfile
import gc
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
from managers.backup_manager import BackupManager


class TestBackupManagerUnit:
    """Unit tests for BackupManager - isolated component testing"""

    @pytest.fixture
    def mock_auth_service(self):
        """Mock authentication service"""
        mock_auth = Mock()
        mock_auth.db = Mock()
        mock_auth.current_user = {
            "id": 1,
            "username": "super_admin",
            "role": "super_admin",
            "first_name": "Super",
            "last_name": "Admin",
        }
        return mock_auth

    @pytest.fixture
    def backup_manager(self, mock_auth_service):
        """Create BackupManager with mocked dependencies"""
        with patch("os.makedirs"):
            manager = BackupManager(mock_auth_service)
            manager.backup_dir = "/test/backups"  # Override for testing
            return manager

    def test_initialization(self, mock_auth_service):
        """Test BackupManager initialization"""
        with patch("os.makedirs") as mock_makedirs:
            # Act
            manager = BackupManager(mock_auth_service)

            # Assert
            assert manager.auth == mock_auth_service
            assert manager.db == mock_auth_service.db
            assert "backups" in manager.backup_dir
            assert manager.restore_codes == {}
            mock_makedirs.assert_called_once()

    def test_can_create_backup_super_admin(self, backup_manager):
        """Test super admin can create backups"""
        # Arrange
        backup_manager.auth.current_user["role"] = "super_admin"

        # Act & Assert
        assert backup_manager.can_create_backup() is True

    def test_can_create_backup_system_admin(self, backup_manager):
        """Test system admin can create backups"""
        # Arrange
        backup_manager.auth.current_user["role"] = "system_admin"

        # Act & Assert
        assert backup_manager.can_create_backup() is True

    def test_can_create_backup_service_engineer_denied(self, backup_manager):
        """Test service engineer cannot create backups"""
        # Arrange
        backup_manager.auth.current_user["role"] = "service_engineer"

        # Act & Assert
        assert backup_manager.can_create_backup() is False

    def test_can_create_backup_no_user_denied(self, backup_manager):
        """Test no logged in user cannot create backups"""
        # Arrange
        backup_manager.auth.current_user = None

        # Act & Assert
        assert backup_manager.can_create_backup() is False

    def test_can_restore_backup_super_admin_only(self, backup_manager):
        """Test only super admin can restore backups directly"""
        # Test super admin
        backup_manager.auth.current_user["role"] = "super_admin"
        assert backup_manager.can_restore_backup() is True

        # Test system admin
        backup_manager.auth.current_user["role"] = "system_admin"
        assert backup_manager.can_restore_backup() is False

        # Test service engineer
        backup_manager.auth.current_user["role"] = "service_engineer"
        assert backup_manager.can_restore_backup() is False

    def test_can_use_restore_code_authorized_roles(self, backup_manager):
        """Test authorized roles can use restore codes"""
        # Test super admin
        backup_manager.auth.current_user["role"] = "super_admin"
        assert backup_manager.can_use_restore_code() is True

        # Test system admin
        backup_manager.auth.current_user["role"] = "system_admin"
        assert backup_manager.can_use_restore_code() is True

        # Test service engineer (should be denied)
        backup_manager.auth.current_user["role"] = "service_engineer"
        assert backup_manager.can_use_restore_code() is False

    def test_can_manage_restore_codes_super_admin_only(self, backup_manager):
        """Test only super admin can manage restore codes"""
        # Test super admin
        backup_manager.auth.current_user["role"] = "super_admin"
        assert backup_manager.can_manage_restore_codes() is True

        # Test system admin
        backup_manager.auth.current_user["role"] = "system_admin"
        assert backup_manager.can_manage_restore_codes() is False

        # Test service engineer
        backup_manager.auth.current_user["role"] = "service_engineer"
        assert backup_manager.can_manage_restore_codes() is False

    @patch("builtins.print")
    def test_create_backup_permission_denied(self, mock_print, backup_manager):
        """Test backup creation denied for unauthorized users"""
        # Arrange
        backup_manager.auth.current_user["role"] = "service_engineer"

        # Act
        result = backup_manager.create_backup()

        # Assert
        assert result is None
        mock_print.assert_called_with(
            "Access denied: You don't have permission to create backups!"
        )

    @patch("managers.backup_manager.datetime")
    @patch("managers.backup_manager.zipfile.ZipFile")
    @patch("managers.backup_manager.os.path.join")
    @patch("builtins.print")
    def test_create_backup_success(
        self,
        mock_print,
        mock_join,
        mock_zipfile,
        mock_datetime,
        backup_manager,
    ):
        """Test successful backup creation with ZIP format"""

        # Arrange
        backup_manager.auth.current_user["role"] = "super_admin"
        mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
        mock_join.return_value = "/test/backups/backup_20240101_120000.zip"

        # Create comprehensive mock for database operations
        mock_cursor = Mock()

        # Set up the fetchall calls to return data in the correct sequence
        # The create_backup method makes these calls in order:
        # 1. SELECT * FROM users
        # 2. PRAGMA table_info(users)
        # 3. SELECT * FROM travelers
        # 4. PRAGMA table_info(travelers)
        # 5. SELECT * FROM scooters
        # 6. PRAGMA table_info(scooters)

        users_data = [
            (
                1,
                "super_admin",
                "hash",
                "super_admin",
                "Super",
                "Admin",
                "2024-01-01",
                1,
                1,
            )
        ]
        users_columns = [
            (0, "id", "INTEGER", 0, None, 1),
            (1, "username", "TEXT", 0, None, 0),
            (2, "password_hash", "TEXT", 0, None, 0),
            (3, "role", "TEXT", 0, None, 0),
            (4, "first_name", "TEXT", 0, None, 0),
            (5, "last_name", "TEXT", 0, None, 0),
            (6, "created_date", "TEXT", 0, None, 0),
            (7, "created_by", "INTEGER", 0, None, 0),
            (8, "is_active", "INTEGER", 0, None, 0),
        ]

        travelers_data = [
            (
                1,
                "CUST001",
                "John",
                "Doe",
                "01-01-1990",
                "Male",
                "Main St",
                "1",
                "1000AA",
                "Amsterdam",
                "encrypted_email",
                "encrypted_phone",
                "encrypted_license",
                "2024-01-01",
            )
        ]
        travelers_columns = [
            (0, "id", "INTEGER", 0, None, 1),
            (1, "customer_id", "TEXT", 0, None, 0),
            (2, "first_name", "TEXT", 0, None, 0),
            (3, "last_name", "TEXT", 0, None, 0),
            (4, "birthday", "TEXT", 0, None, 0),
            (5, "gender", "TEXT", 0, None, 0),
            (6, "street_name", "TEXT", 0, None, 0),
            (7, "house_number", "TEXT", 0, None, 0),
            (8, "zip_code", "TEXT", 0, None, 0),
            (9, "city", "TEXT", 0, None, 0),
            (10, "email", "TEXT", 0, None, 0),
            (11, "mobile_phone", "TEXT", 0, None, 0),
            (12, "driving_license", "TEXT", 0, None, 0),
            (13, "registration_date", "TEXT", 0, None, 0),
        ]

        scooters_data = [
            (
                1,
                "Brand",
                "Model",
                "encrypted_serial",
                25,
                1000,
                80,
                20,
                40,
                51.92250,
                4.47917,
                "",
                100.0,
                "2024-01-01",
                "2024-01-01",
            )
        ]
        scooters_columns = [
            (0, "id", "INTEGER", 0, None, 1),
            (1, "brand", "TEXT", 0, None, 0),
            (2, "model", "TEXT", 0, None, 0),
            (3, "serial_number", "TEXT", 0, None, 0),
            (4, "top_speed", "INTEGER", 0, None, 0),
            (5, "battery_capacity", "INTEGER", 0, None, 0),
            (6, "state_of_charge", "INTEGER", 0, None, 0),
            (7, "target_range_min", "INTEGER", 0, None, 0),
            (8, "target_range_max", "INTEGER", 0, None, 0),
            (9, "latitude", "REAL", 0, None, 0),
            (10, "longitude", "REAL", 0, None, 0),
            (11, "out_of_service_status", "TEXT", 0, None, 0),
            (12, "mileage", "REAL", 0, None, 0),
            (13, "last_maintenance_date", "TEXT", 0, None, 0),
            (14, "in_service_date", "TEXT", 0, None, 0),
        ]

        # Set up the fetchall calls in the correct sequence
        mock_cursor.fetchall.side_effect = [
            users_data,  # SELECT * FROM users
            users_columns,  # PRAGMA table_info(users)
            travelers_data,  # SELECT * FROM travelers
            travelers_columns,  # PRAGMA table_info(travelers)
            scooters_data,  # SELECT * FROM scooters
            scooters_columns,  # PRAGMA table_info(scooters)
        ]

        # Mock connection with proper context manager behavior
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        backup_manager.db.get_connection.return_value = mock_conn

        # Mock ZIP file operations with proper context manager support
        mock_zip_instance = Mock()
        mock_zip_instance.writestr = Mock()
        mock_zip_instance.__enter__ = Mock(return_value=mock_zip_instance)
        mock_zip_instance.__exit__ = Mock(return_value=None)
        mock_zipfile.return_value = mock_zip_instance

        # Act
        result = backup_manager.create_backup()

        # Assert
        assert result == "backup_20240101_120000.zip"  # ZIP extension

        # Verify database operations
        assert mock_cursor.execute.call_count == 6
        assert mock_cursor.fetchall.call_count == 6

        # Verify ZIP file operations
        mock_zipfile.assert_called_once_with(
            "/test/backups/backup_20240101_120000.zip", "w", zipfile.ZIP_DEFLATED
        )
        assert mock_zip_instance.writestr.call_count == 2  # JSON data + metadata

        # Verify success message was printed
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        success_messages = [
            call for call in print_calls if "Backup created successfully" in str(call)
        ]
        assert len(success_messages) > 0

    @patch("os.listdir")
    def test_list_backups_success(self, mock_listdir, backup_manager):
        """Test successful backup listing with ZIP files"""
        # Arrange
        mock_listdir.return_value = [
            "backup_20240101_120000.zip",  # ZIP files
            "backup_20240102_140000.zip",
            "other_file.txt",
            "backup_20240103_160000.zip",
        ]

        # Act
        result = backup_manager.list_backups()

        # Assert
        expected = [
            "backup_20240103_160000.zip",  # Newest first
            "backup_20240102_140000.zip",
            "backup_20240101_120000.zip",
        ]
        assert result == expected

    @patch("os.listdir")
    def test_list_backups_empty_directory(self, mock_listdir, backup_manager):
        """Test listing backups from empty directory"""
        # Arrange
        mock_listdir.return_value = []

        # Act
        result = backup_manager.list_backups()

        # Assert
        assert result == []

    @patch("os.listdir")
    @patch("builtins.print")
    def test_list_backups_error_handling(
        self, mock_print, mock_listdir, backup_manager
    ):
        """Test error handling in backup listing"""
        # Arrange
        mock_listdir.side_effect = OSError("Directory not found")

        # Act
        result = backup_manager.list_backups()

        # Assert
        assert result == []
        mock_print.assert_called_with("Error listing backups: Directory not found")

    @patch("os.path.exists")
    @patch("os.path.getsize")
    @patch("managers.backup_manager.zipfile.ZipFile")
    @patch("builtins.print")
    def test_show_backup_info_success(
        self, mock_print, mock_zipfile, mock_getsize, mock_exists, backup_manager
    ):
        """Test successful backup info display for ZIP file"""
        # Arrange
        mock_exists.return_value = True
        mock_getsize.return_value = 1024  # 1KB file

        # Mock backup data
        mock_backup_data = {
            "created_at": "2024-01-01T12:00:00",
            "created_by": "super_admin",
            "version": "1.0",
            "tables": {
                "users": {"data": [1, 2, 3]},
                "travelers": {"data": [1, 2]},
                "scooters": {"data": [1]},
            },
        }

        # Mock ZIP file reading with proper context manager support
        mock_zip_instance = Mock()
        mock_zip_instance.namelist.return_value = [
            "backup_20240101_120000.json",
            "backup_info.txt",
        ]
        mock_zip_instance.__enter__ = Mock(return_value=mock_zip_instance)
        mock_zip_instance.__exit__ = Mock(return_value=None)

        # Mock file objects with proper context manager support
        mock_json_file = Mock()
        mock_json_file.read.return_value = json.dumps(mock_backup_data).encode("utf-8")
        mock_json_file.__enter__ = Mock(return_value=mock_json_file)
        mock_json_file.__exit__ = Mock(return_value=None)

        mock_metadata_file = Mock()
        mock_metadata = {
            "backup_format": "urban_mobility_v1.0",
            "description": "Urban Mobility System Database Backup",
        }
        mock_metadata_file.read.return_value = json.dumps(mock_metadata).encode("utf-8")
        mock_metadata_file.__enter__ = Mock(return_value=mock_metadata_file)
        mock_metadata_file.__exit__ = Mock(return_value=None)

        def mock_open_side_effect(filename):
            if filename.endswith(".json"):
                return mock_json_file
            elif filename == "backup_info.txt":
                return mock_metadata_file
            return Mock()

        mock_zip_instance.open.side_effect = mock_open_side_effect
        mock_zipfile.return_value = mock_zip_instance

        # Act
        result = backup_manager.show_backup_info("backup_test.zip")

        # Assert
        assert result == mock_backup_data
        # Check that the print was called with the expected message
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert any("📋 BACKUP INFORMATION" in str(call) for call in print_calls)
        assert any("ZIP compressed backup" in str(call) for call in print_calls)

    @patch("os.path.exists")
    @patch("builtins.print")
    def test_show_backup_info_file_not_found(
        self, mock_print, mock_exists, backup_manager
    ):
        """Test backup info for non-existent file"""
        # Arrange
        mock_exists.return_value = False

        # Act
        result = backup_manager.show_backup_info("nonexistent.zip")

        # Assert
        assert result is None
        mock_print.assert_called_with("Backup file not found: nonexistent.zip")

    @patch("os.path.exists")
    @patch("managers.backup_manager.zipfile.ZipFile")
    @patch("builtins.print")
    def test_show_backup_info_invalid_zip(
        self, mock_print, mock_zipfile, mock_exists, backup_manager
    ):
        """Test backup info for invalid ZIP file"""
        # Arrange
        mock_exists.return_value = True
        mock_zipfile.side_effect = zipfile.BadZipFile("Not a zip file")

        # Act
        result = backup_manager.show_backup_info("corrupt.zip")

        # Assert
        assert result is None
        mock_print.assert_called_with("Error: corrupt.zip is not a valid ZIP file")

    def test_generate_secure_code(self, backup_manager):
        """Test secure code generation"""
        # Act
        code1 = backup_manager._generate_secure_code()
        code2 = backup_manager._generate_secure_code()

        # Assert
        assert len(code1) == 12
        assert len(code2) == 12
        assert code1 != code2  # Should be unique
        assert code1.isalnum()  # Should be alphanumeric
        assert code1.isupper()  # Should be uppercase

    def test_validate_restore_code_valid(self, backup_manager):
        """Test validation of valid restore code"""
        # Arrange
        test_code = "TEST12345678"
        backup_manager.restore_codes[test_code] = {
            "backup_file": "test_backup.zip",
            "created_at": "2024-01-01T12:00:00",
            "created_by": "super_admin",
            "used": False,
        }

        # Act & Assert
        assert backup_manager._validate_restore_code(test_code) is True

    def test_validate_restore_code_used(self, backup_manager):
        """Test validation of used restore code"""
        # Arrange
        test_code = "USED12345678"
        backup_manager.restore_codes[test_code] = {
            "backup_file": "test_backup.zip",
            "created_at": "2024-01-01T12:00:00",
            "created_by": "super_admin",
            "used": True,
        }

        # Act & Assert
        assert backup_manager._validate_restore_code(test_code) is False

    def test_validate_restore_code_nonexistent(self, backup_manager):
        """Test validation of non-existent restore code"""
        # Act & Assert
        assert backup_manager._validate_restore_code("NONEXISTENT") is False

    def test_invalidate_restore_code(self, backup_manager):
        """Test restore code invalidation"""
        # Arrange
        test_code = "VALID12345678"
        backup_manager.restore_codes[test_code] = {
            "backup_file": "test_backup.zip",
            "created_at": "2024-01-01T12:00:00",
            "created_by": "super_admin",
            "used": False,
        }

        # Act
        backup_manager._invalidate_restore_code(test_code)

        # Assert
        assert backup_manager.restore_codes[test_code]["used"] is True

    @patch("builtins.print")
    def test_generate_restore_code_permission_denied(self, mock_print, backup_manager):
        """Test restore code generation denied for unauthorized users"""
        # Arrange
        backup_manager.auth.current_user["role"] = "system_admin"

        # Act
        result = backup_manager.generate_restore_code("test_backup.zip")

        # Assert
        assert result is None
        mock_print.assert_called_with(
            "Access denied: Only Super Administrator can generate restore codes!"
        )

    @patch("os.path.exists")
    @patch("builtins.print")
    def test_generate_restore_code_backup_not_found(
        self, mock_print, mock_exists, backup_manager
    ):
        """Test restore code generation for non-existent backup"""
        # Arrange
        mock_exists.return_value = False

        # Act
        result = backup_manager.generate_restore_code("nonexistent.zip")

        # Assert
        assert result is None
        mock_print.assert_called_with("❌ Backup file not found: nonexistent.zip")

    @patch("os.path.exists")
    @patch("managers.backup_manager.zipfile.ZipFile")
    @patch("builtins.print")
    def test_generate_restore_code_success(
        self, mock_print, mock_zipfile, mock_exists, backup_manager
    ):
        """Test successful restore code generation for ZIP backup"""
        # Arrange
        mock_exists.return_value = True

        # Mock ZIP file validation with proper context manager support
        mock_zip_instance = Mock()
        mock_zip_instance.namelist.return_value = ["backup_20240101_120000.json"]
        mock_zip_instance.__enter__ = Mock(return_value=mock_zip_instance)
        mock_zip_instance.__exit__ = Mock(return_value=None)
        mock_zipfile.return_value = mock_zip_instance

        # Act
        result = backup_manager.generate_restore_code("test_backup.zip")

        # Assert
        assert result is not None
        assert len(result) == 12
        assert result in backup_manager.restore_codes
        assert backup_manager.restore_codes[result]["backup_file"] == "test_backup.zip"
        assert backup_manager.restore_codes[result]["used"] is False
        mock_print.assert_any_call("✅ Restore code generated successfully!")

    @patch("os.path.exists")
    @patch("managers.backup_manager.zipfile.ZipFile")
    @patch("builtins.print")
    def test_generate_restore_code_invalid_zip(
        self, mock_print, mock_zipfile, mock_exists, backup_manager
    ):
        """Test restore code generation for invalid ZIP file"""
        # Arrange
        mock_exists.return_value = True
        mock_zipfile.side_effect = zipfile.BadZipFile("Not a zip file")

        # Act
        result = backup_manager.generate_restore_code("invalid.zip")

        # Assert
        assert result is None
        mock_print.assert_called_with("❌ Invalid ZIP file: invalid.zip")

    @patch("builtins.print")
    def test_list_restore_codes_permission_denied(self, mock_print, backup_manager):
        """Test restore codes listing denied for unauthorized users"""
        # Arrange
        backup_manager.auth.current_user["role"] = "system_admin"

        # Act
        backup_manager.list_restore_codes()

        # Assert
        mock_print.assert_called_with(
            "Access denied: Only Super Administrator can view restore codes!"
        )

    @patch("builtins.print")
    def test_list_restore_codes_empty(self, mock_print, backup_manager):
        """Test listing empty restore codes"""
        # Act
        backup_manager.list_restore_codes()

        # Assert
        mock_print.assert_called_with("No active restore codes.")

    @patch("builtins.print")
    def test_list_restore_codes_with_codes(self, mock_print, backup_manager):
        """Test listing active restore codes for ZIP backups"""
        # Arrange
        backup_manager.restore_codes = {
            "CODE12345678": {
                "backup_file": "backup1.zip",
                "created_at": "2024-01-01T12:00:00",
                "used": False,
            },
            "USED87654321": {
                "backup_file": "backup2.zip",
                "created_at": "2024-01-02T14:00:00",
                "used": True,
            },
        }

        # Act
        backup_manager.list_restore_codes()

        # Assert
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert any("📋 ACTIVE RESTORE CODES" in str(call) for call in print_calls)
        # Should indicate ZIP format
        all_output = " ".join(str(call) for call in print_calls)
        assert "ZIP" in all_output

    @patch("builtins.print")
    def test_revoke_restore_code_permission_denied(self, mock_print, backup_manager):
        """Test restore code revocation denied for unauthorized users"""
        # Arrange
        backup_manager.auth.current_user["role"] = "system_admin"

        # Act
        result = backup_manager.revoke_restore_code("TEST12345678")

        # Assert
        assert result is False
        mock_print.assert_called_with(
            "Access denied: Only Super Administrator can revoke restore codes!"
        )

    @patch("builtins.print")
    def test_revoke_restore_code_success(self, mock_print, backup_manager):
        """Test successful restore code revocation"""
        # Arrange
        test_code = "REVOKE123456"
        backup_manager.restore_codes[test_code] = {
            "backup_file": "test.zip",
            "created_at": "2024-01-01T12:00:00",
            "used": False,
        }

        # Act
        result = backup_manager.revoke_restore_code(test_code)

        # Assert
        assert result is True
        assert test_code not in backup_manager.restore_codes
        mock_print.assert_called_with(
            f"✅ Restore code {test_code} revoked successfully!"
        )

    @patch("builtins.print")
    def test_revoke_restore_code_not_found(self, mock_print, backup_manager):
        """Test revocation of non-existent restore code"""
        # Act
        result = backup_manager.revoke_restore_code("NONEXISTENT")

        # Assert
        assert result is False
        mock_print.assert_called_with("❌ Restore code not found: NONEXISTENT")

    @patch("builtins.print")
    def test_restore_backup_permission_denied_no_code(self, mock_print, backup_manager):
        """Test restore without code denied for unauthorized users"""
        # Arrange
        backup_manager.auth.current_user["role"] = "system_admin"

        # Act
        result = backup_manager.restore_backup("test_backup.zip")

        # Assert
        assert result is False
        mock_print.assert_called_with(
            "Access denied: Only Super Administrator can restore without codes!"
        )

    @patch("builtins.print")
    def test_restore_backup_invalid_code(self, mock_print, backup_manager):
        """Test restore with invalid code"""
        # Arrange
        backup_manager.auth.current_user["role"] = "system_admin"

        # Act
        result = backup_manager.restore_backup("test_backup.zip", "INVALID123")

        # Assert
        assert result is False
        mock_print.assert_called_with("❌ Invalid or expired restore code!")

    @patch("os.path.exists")
    @patch("builtins.print")
    def test_restore_backup_file_not_found(
        self, mock_print, mock_exists, backup_manager
    ):
        """Test restore with non-existent backup file"""
        # Arrange
        mock_exists.return_value = False

        # Act
        result = backup_manager.restore_backup("nonexistent.zip")

        # Assert
        assert result is False
        mock_print.assert_called_with("❌ Backup file not found: nonexistent.zip")

    @patch("os.path.exists")
    @patch("builtins.input")
    @patch("managers.backup_manager.zipfile.ZipFile")
    @patch("builtins.print")
    def test_restore_backup_user_cancellation(
        self, mock_print, mock_zipfile, mock_input, mock_exists, backup_manager
    ):
        """Test restore cancellation by user"""
        # Arrange
        mock_exists.return_value = True
        mock_input.return_value = "CANCEL"

        # Mock backup data in ZIP format
        mock_backup_data = {
            "created_at": "2024-01-01T12:00:00",
            "created_by": "super_admin",
            "tables": {"users": {"columns": ["id"], "data": [[1]]}},
        }

        # Mock ZIP file reading with proper context manager support
        mock_zip_instance = Mock()
        mock_zip_instance.namelist.return_value = ["backup_20240101_120000.json"]
        mock_zip_instance.__enter__ = Mock(return_value=mock_zip_instance)
        mock_zip_instance.__exit__ = Mock(return_value=None)

        # Mock file object with proper context manager support
        mock_json_file = Mock()
        mock_json_file.read.return_value = json.dumps(mock_backup_data).encode("utf-8")
        mock_json_file.__enter__ = Mock(return_value=mock_json_file)
        mock_json_file.__exit__ = Mock(return_value=None)

        mock_zip_instance.open.return_value = mock_json_file
        mock_zipfile.return_value = mock_zip_instance

        # Act
        result = backup_manager.restore_backup("test_backup.zip")

        # Assert
        assert result is False
        mock_print.assert_called_with("Restore cancelled.")

    @patch("os.path.exists")
    @patch("builtins.input")
    @patch("managers.backup_manager.zipfile.ZipFile")
    @patch("builtins.print")
    def test_restore_backup_success_with_code(
        self,
        mock_print,
        mock_zipfile,
        mock_input,
        mock_exists,
        backup_manager,
    ):
        """Test successful restore with restore code from ZIP backup"""
        # Arrange
        mock_exists.return_value = True
        mock_input.return_value = "RESTORE"

        # Setup restore code
        test_code = "VALID12345678"
        backup_manager.restore_codes[test_code] = {
            "backup_file": "test_backup.zip",
            "created_at": "2024-01-01T12:00:00",
            "created_by": "super_admin",
            "used": False,
        }

        # Mock backup data in ZIP format
        mock_backup_data = {
            "created_at": "2024-01-01T12:00:00",
            "created_by": "super_admin",
            "tables": {
                "users": {"columns": ["id", "username"], "data": [[1, "test_user"]]}
            },
        }

        # Mock ZIP file operations with proper context manager support
        mock_zip_instance = Mock()
        mock_zip_instance.namelist.return_value = ["backup_20240101_120000.json"]
        mock_zip_instance.__enter__ = Mock(return_value=mock_zip_instance)
        mock_zip_instance.__exit__ = Mock(return_value=None)

        # Mock file object with proper context manager support
        mock_json_file = Mock()
        mock_json_file.read.return_value = json.dumps(mock_backup_data).encode("utf-8")
        mock_json_file.__enter__ = Mock(return_value=mock_json_file)
        mock_json_file.__exit__ = Mock(return_value=None)

        mock_zip_instance.open.return_value = mock_json_file
        mock_zipfile.return_value = mock_zip_instance

        # Mock database operations with proper context manager support
        mock_cursor = Mock()
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_conn.commit = Mock()

        backup_manager.db.get_connection.return_value = mock_conn
        backup_manager.auth.current_user["role"] = "system_admin"

        # Act
        result = backup_manager.restore_backup("test_backup.zip", test_code)

        # Assert
        assert result is True
        assert backup_manager.restore_codes[test_code]["used"] is True
        mock_print.assert_any_call("✅ Database restored successfully from ZIP backup!")
        mock_conn.commit.assert_called_once()

    @patch("os.path.exists")
    @patch("managers.backup_manager.zipfile.ZipFile")
    @patch("builtins.print")
    def test_restore_backup_invalid_zip_file(
        self, mock_print, mock_zipfile, mock_exists, backup_manager
    ):
        """Test restore with invalid ZIP file"""
        # Arrange
        mock_exists.return_value = True
        mock_zipfile.side_effect = zipfile.BadZipFile("Not a valid ZIP file")

        # Act
        result = backup_manager.restore_backup("corrupt.zip")

        # Assert
        assert result is False
        mock_print.assert_called_with("❌ Error: corrupt.zip is not a valid ZIP file")
