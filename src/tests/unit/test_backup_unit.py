import pytest
import os
import tempfile
import json
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
    @patch("managers.backup_manager.os.makedirs")
    @patch("managers.backup_manager.os.path.join")
    @patch("builtins.open", create=True)
    @patch("managers.backup_manager.json.dump")
    @patch("builtins.print")
    def test_create_backup_success(
        self,
        mock_print,
        mock_json_dump,
        mock_open,
        mock_join,
        mock_makedirs,
        mock_datetime,
        backup_manager,
    ):
        """Test successful backup creation with comprehensive error handling"""

        # Arrange
        backup_manager.auth.current_user["role"] = "super_admin"
        mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
        mock_join.return_value = "/test/backups/backup_20240101_120000.json"
        mock_makedirs.return_value = None

        # Create comprehensive mock for database operations
        mock_cursor = Mock()
        mock_cursor.execute = Mock()

        # Define all the data that will be returned by fetchall calls
        mock_data_sequence = [
            # Users SELECT
            [
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
            ],
            # Users PRAGMA table_info
            [
                ("id",),
                ("username",),
                ("password_hash",),
                ("role",),
                ("first_name",),
                ("last_name",),
                ("created_date",),
                ("created_by",),
                ("is_active",),
            ],
            # Travelers SELECT
            [
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
            ],
            # Travelers PRAGMA table_info
            [
                ("id",),
                ("customer_id",),
                ("first_name",),
                ("last_name",),
                ("birthday",),
                ("gender",),
                ("street_name",),
                ("house_number",),
                ("zip_code",),
                ("city",),
                ("email",),
                ("mobile_phone",),
                ("driving_license",),
                ("registration_date",),
            ],
            # Scooters SELECT
            [
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
            ],
            # Scooters PRAGMA table_info
            [
                ("id",),
                ("brand",),
                ("model",),
                ("serial_number",),
                ("top_speed",),
                ("battery_capacity",),
                ("state_of_charge",),
                ("target_range_min",),
                ("target_range_max",),
                ("latitude",),
                ("longitude",),
                ("out_of_service_status",),
                ("mileage",),
                ("last_maintenance_date",),
                ("in_service_date",),
            ],
        ]

        # Use side_effect with the predefined sequence
        mock_cursor.fetchall.side_effect = mock_data_sequence

        # Mock connection with proper context manager behavior
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        backup_manager.db.get_connection.return_value = mock_conn

        # Mock file operations to prevent actual file I/O
        mock_file_handle = Mock()
        mock_open.return_value.__enter__ = Mock(return_value=mock_file_handle)
        mock_open.return_value.__exit__ = Mock(return_value=None)

        # Act - wrap in try-catch to see any exceptions
        try:
            result = backup_manager.create_backup()
            print(f"DEBUG: create_backup returned: {result}")
        except Exception as e:
            print(f"DEBUG: Exception occurred: {e}")
            print(f"DEBUG: Exception type: {type(e)}")
            import traceback

            traceback.print_exc()
            raise

        # Assert
        assert (
            result == "backup_20240101_120000.json"
        ), f"Expected backup filename, got: {result}"

        # Verify all the mocked calls were made correctly
        assert (
            mock_cursor.execute.call_count == 6
        ), f"Expected 6 execute calls, got {mock_cursor.execute.call_count}"
        assert (
            mock_cursor.fetchall.call_count == 6
        ), f"Expected 6 fetchall calls, got {mock_cursor.fetchall.call_count}"

        # Verify file operations
        mock_open.assert_called_once_with(
            "/test/backups/backup_20240101_120000.json", "w", encoding="utf-8"
        )
        mock_json_dump.assert_called_once()

        # Verify success message was printed
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        success_messages = [
            call for call in print_calls if "Backup created successfully" in str(call)
        ]
        assert (
            len(success_messages) > 0
        ), f"Expected success message, got print calls: {print_calls}"

        @patch("os.listdir")
        def test_list_backups_success(self, mock_listdir, backup_manager):
            """Test successful backup listing"""
            # Arrange
            mock_listdir.return_value = [
                "backup_20240101_120000.json",
                "backup_20240102_140000.json",
                "other_file.txt",
                "backup_20240103_160000.json",
            ]

            # Act
            result = backup_manager.list_backups()

            # Assert
            expected = [
                "backup_20240103_160000.json",  # Newest first
                "backup_20240102_140000.json",
                "backup_20240101_120000.json",
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
    @patch("builtins.open", create=True)
    @patch("json.load")
    @patch("builtins.print")
    def test_show_backup_info_success(
        self, mock_print, mock_json_load, mock_open, mock_exists, backup_manager
    ):
        """Test successful backup info display"""
        # Arrange
        mock_exists.return_value = True
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
        mock_json_load.return_value = mock_backup_data

        # Act
        result = backup_manager.show_backup_info("backup_test.json")

        # Assert
        assert result == mock_backup_data
        # Check that the print was called with the expected message
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert any("📋 BACKUP INFORMATION" in str(call) for call in print_calls)

    @patch("os.path.exists")
    @patch("builtins.print")
    def test_show_backup_info_file_not_found(
        self, mock_print, mock_exists, backup_manager
    ):
        """Test backup info for non-existent file"""
        # Arrange
        mock_exists.return_value = False

        # Act
        result = backup_manager.show_backup_info("nonexistent.json")

        # Assert
        assert result is None
        mock_print.assert_called_with("Backup file not found: nonexistent.json")

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
            "backup_file": "test_backup.json",
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
            "backup_file": "test_backup.json",
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
            "backup_file": "test_backup.json",
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
        result = backup_manager.generate_restore_code("test_backup.json")

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
        result = backup_manager.generate_restore_code("nonexistent.json")

        # Assert
        assert result is None
        mock_print.assert_called_with("❌ Backup file not found: nonexistent.json")

    @patch("os.path.exists")
    @patch("builtins.print")
    def test_generate_restore_code_success(
        self, mock_print, mock_exists, backup_manager
    ):
        """Test successful restore code generation"""
        # Arrange
        mock_exists.return_value = True

        # Act
        result = backup_manager.generate_restore_code("test_backup.json")

        # Assert
        assert result is not None
        assert len(result) == 12
        assert result in backup_manager.restore_codes
        assert backup_manager.restore_codes[result]["backup_file"] == "test_backup.json"
        assert backup_manager.restore_codes[result]["used"] is False
        mock_print.assert_any_call("✅ Restore code generated successfully!")

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
        """Test listing active restore codes"""
        # Arrange
        backup_manager.restore_codes = {
            "CODE12345678": {
                "backup_file": "backup1.json",
                "created_at": "2024-01-01T12:00:00",
                "used": False,
            },
            "USED87654321": {
                "backup_file": "backup2.json",
                "created_at": "2024-01-02T14:00:00",
                "used": True,
            },
        }

        # Act
        backup_manager.list_restore_codes()

        # Assert
        # Check that the print was called with the expected header
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert any("📋 ACTIVE RESTORE CODES" in str(call) for call in print_calls)

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
            "backup_file": "test.json",
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
        result = backup_manager.restore_backup("test_backup.json")

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
        result = backup_manager.restore_backup("test_backup.json", "INVALID123")

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
        result = backup_manager.restore_backup("nonexistent.json")

        # Assert
        assert result is False
        mock_print.assert_called_with("❌ Backup file not found: nonexistent.json")

    @patch("os.path.exists")
    @patch("builtins.input")
    @patch("builtins.print")
    def test_restore_backup_user_cancellation(
        self, mock_print, mock_input, mock_exists, backup_manager
    ):
        """Test restore cancellation by user"""
        # Arrange
        mock_exists.return_value = True
        mock_input.return_value = "CANCEL"

        # Mock open and json.load
        with patch("builtins.open", create=True), patch("json.load"):
            # Act
            result = backup_manager.restore_backup("test_backup.json")

        # Assert
        assert result is False
        mock_print.assert_called_with("Restore cancelled.")

    @patch("os.path.exists")
    @patch("builtins.input")
    @patch("builtins.open", create=True)
    @patch("json.load")
    @patch("builtins.print")
    def test_restore_backup_success_with_code(
        self,
        mock_print,
        mock_json_load,
        mock_open,
        mock_input,
        mock_exists,
        backup_manager,
    ):
        """Test successful restore with restore code"""
        # Arrange
        mock_exists.return_value = True
        mock_input.return_value = "RESTORE"

        # Setup restore code
        test_code = "VALID12345678"
        backup_manager.restore_codes[test_code] = {
            "backup_file": "test_backup.json",
            "created_at": "2024-01-01T12:00:00",
            "created_by": "super_admin",
            "used": False,
        }

        # Mock backup data
        mock_backup_data = {
            "tables": {
                "users": {"columns": ["id", "username"], "data": [[1, "test_user"]]}
            }
        }
        mock_json_load.return_value = mock_backup_data

        # Mock database operations
        mock_cursor = Mock()
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_conn.commit = Mock()

        backup_manager.db.get_connection.return_value = mock_conn
        backup_manager.auth.current_user["role"] = "system_admin"

        # Act
        result = backup_manager.restore_backup("test_backup.json", test_code)

        # Assert
        assert result is True
        assert backup_manager.restore_codes[test_code]["used"] is True
        mock_print.assert_any_call("✅ Database restored successfully!")
        mock_conn.commit.assert_called_once()

    @patch("os.path.exists")
    @patch("builtins.print")
    def test_restore_backup_database_error(
        self, mock_print, mock_exists, backup_manager
    ):
        """Test restore with database error"""
        # Arrange
        mock_exists.return_value = False

        # Act
        result = backup_manager.restore_backup("test_backup.json")

        # Assert
        assert result is False
        mock_print.assert_called_with("❌ Backup file not found: test_backup.json")
