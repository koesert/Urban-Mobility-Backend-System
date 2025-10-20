"""
Unit tests for scooters.py module.

Tests scooter fleet management including CRUD operations,
role-based access control, and validation.
"""

import pytest
from unittest.mock import Mock, patch
from validation import ValidationError
from scooters import (
    add_scooter,
    update_scooter,
    delete_scooter,
    search_scooters,
    get_scooter_by_serial,
    list_all_scooters,
)


# ============================================================================
# Add Scooter Tests
# ============================================================================


@pytest.mark.unit
class TestAddScooter:
    """Test adding new scooters to fleet"""

    @patch("scooters.check_permission")
    def test_add_scooter_no_permission(self, mock_check_perm):
        """Test adding scooter without permission"""
        mock_check_perm.return_value = False

        success, msg = add_scooter("SC123", "Model X", 100, "available", "Amsterdam")

        assert success is False
        assert "access denied" in msg.lower()

    @patch("scooters.log_activity")
    @patch("scooters.get_connection")
    @patch("scooters.encrypt_username")
    @patch("scooters.get_current_user")
    @patch("scooters.check_permission")
    def test_add_scooter_success(
        self, mock_check_perm, mock_get_user, mock_encrypt, mock_conn, mock_log
    ):
        """Test successfully adding scooter"""
        mock_check_perm.return_value = True
        mock_get_user.return_value = {"username": "admin_001"}
        mock_encrypt.return_value = "encrypted_serial"

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None  # Serial doesn't exist
        mock_conn.return_value.cursor.return_value = mock_cursor

        success, msg = add_scooter(
            "SC123456", "Model X Pro", 85, "available", "Amsterdam Central"
        )

        assert success is True
        assert "added successfully" in msg.lower()
        mock_cursor.execute.assert_any_call(
            "SELECT id FROM scooters WHERE serial_number = ?", ("encrypted_serial",)
        )
        # Check INSERT was called
        insert_call = [
            call for call in mock_cursor.execute.call_args_list if "INSERT" in str(call)
        ]
        assert len(insert_call) == 1

    @patch("scooters.get_connection")
    @patch("scooters.encrypt_username")
    @patch("scooters.get_current_user")
    @patch("scooters.check_permission")
    def test_add_scooter_duplicate_serial(
        self, mock_check_perm, mock_get_user, mock_encrypt, mock_conn
    ):
        """Test adding scooter with existing serial number"""
        mock_check_perm.return_value = True
        mock_get_user.return_value = {"username": "admin_001"}
        mock_encrypt.return_value = "encrypted_serial"

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,)  # Serial exists
        mock_conn.return_value.cursor.return_value = mock_cursor

        success, msg = add_scooter("SC123456", "Model X", 85, "available", "Amsterdam")

        assert success is False
        assert "already exists" in msg.lower()

    @patch("scooters.check_permission")
    def test_add_scooter_invalid_serial_number(self, mock_check_perm):
        """Test adding scooter with invalid serial number"""
        mock_check_perm.return_value = True

        success, msg = add_scooter("ABC", "Model X", 85, "available", "Amsterdam")

        assert success is False
        assert "validation error" in msg.lower()

    @patch("scooters.check_permission")
    def test_add_scooter_invalid_battery_level(self, mock_check_perm):
        """Test adding scooter with invalid battery level"""
        mock_check_perm.return_value = True

        success, msg = add_scooter("SC123456", "Model X", 150, "available", "Amsterdam")

        assert success is False
        assert "validation error" in msg.lower()

    @patch("scooters.check_permission")
    def test_add_scooter_invalid_status(self, mock_check_perm):
        """Test adding scooter with invalid status"""
        mock_check_perm.return_value = True

        success, msg = add_scooter(
            "SC123456", "Model X", 85, "invalid_status", "Amsterdam"
        )

        assert success is False
        assert "validation error" in msg.lower()

    @patch("scooters.check_permission")
    def test_add_scooter_invalid_location(self, mock_check_perm):
        """Test adding scooter with invalid location"""
        mock_check_perm.return_value = True

        success, msg = add_scooter("SC123456", "Model X", 85, "available", "")

        assert success is False
        assert "validation error" in msg.lower()


# ============================================================================
# Update Scooter Tests
# ============================================================================


@pytest.mark.unit
class TestUpdateScooter:
    """Test updating scooter information"""

    @patch("scooters.check_permission")
    def test_update_scooter_no_permission(self, mock_check_perm):
        """Test updating scooter without permission"""
        mock_check_perm.return_value = False

        success, msg = update_scooter("SC123456", battery_level=90)

        assert success is False
        assert "access denied" in msg.lower()

    @patch("scooters.get_current_user")
    @patch("scooters.check_permission")
    def test_update_scooter_no_fields(self, mock_check_perm, mock_get_user):
        """Test updating scooter with no fields specified"""
        mock_check_perm.return_value = True
        mock_get_user.return_value = {"username": "admin_001"}

        success, msg = update_scooter("SC123456")

        assert success is False
        assert "no fields" in msg.lower()

    @patch("scooters.log_activity")
    @patch("scooters.get_connection")
    @patch("scooters.encrypt_username")
    @patch("scooters.get_current_user")
    @patch("scooters.check_permission")
    def test_update_scooter_admin_all_fields(
        self, mock_check_perm, mock_get_user, mock_encrypt, mock_conn, mock_log
    ):
        """Test system admin can update all fields"""
        mock_check_perm.return_value = True
        mock_get_user.return_value = {"username": "admin_001", "role": "system_admin"}
        mock_encrypt.return_value = "encrypted_serial"

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (
            1,
            "encrypted_serial",
            "Model X",
            85,
            "available",
            "Amsterdam",
            None,
            "2025-01-01",
        )
        mock_conn.return_value.cursor.return_value = mock_cursor

        success, msg = update_scooter(
            "SC123456", type="Model Y", battery_level=95, location="Rotterdam"
        )

        assert success is True
        assert "updated successfully" in msg.lower()
        # Check UPDATE was called
        update_call = [
            call for call in mock_cursor.execute.call_args_list if "UPDATE" in str(call)
        ]
        assert len(update_call) == 1

    @patch("scooters.log_activity")
    @patch("scooters.get_connection")
    @patch("scooters.encrypt_username")
    @patch("scooters.get_current_user")
    @patch("scooters.check_permission")
    def test_update_scooter_service_engineer_allowed_fields(
        self, mock_check_perm, mock_get_user, mock_encrypt, mock_conn, mock_log
    ):
        """Test service engineer can update allowed fields only"""
        mock_check_perm.return_value = True
        mock_get_user.return_value = {
            "username": "engineer1",
            "role": "service_engineer",
        }
        mock_encrypt.return_value = "encrypted_serial"

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (
            1,
            "encrypted_serial",
            "Model X",
            85,
            "available",
            "Amsterdam",
            None,
            "2025-01-01",
        )
        mock_conn.return_value.cursor.return_value = mock_cursor

        success, msg = update_scooter(
            "SC123456", battery_level=95, status="maintenance", location="Rotterdam"
        )

        assert success is True
        assert "updated successfully" in msg.lower()

    @patch("scooters.get_current_user")
    @patch("scooters.check_permission")
    def test_update_scooter_service_engineer_restricted_field(
        self, mock_check_perm, mock_get_user
    ):
        """Test service engineer cannot update type field"""
        mock_check_perm.return_value = True
        mock_get_user.return_value = {
            "username": "engineer1",
            "role": "service_engineer",
        }

        success, msg = update_scooter("SC123456", type="Model Y")

        assert success is False
        assert "cannot update field" in msg.lower()

    @patch("scooters.get_connection")
    @patch("scooters.encrypt_username")
    @patch("scooters.get_current_user")
    @patch("scooters.check_permission")
    def test_update_scooter_not_found(
        self, mock_check_perm, mock_get_user, mock_encrypt, mock_conn
    ):
        """Test updating non-existent scooter"""
        mock_check_perm.return_value = True
        mock_get_user.return_value = {"username": "admin_001", "role": "system_admin"}
        mock_encrypt.return_value = "encrypted_serial"

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.cursor.return_value = mock_cursor

        success, msg = update_scooter("SC999999", battery_level=90)

        assert success is False
        assert "not found" in msg.lower()

    @patch("scooters.get_connection")
    @patch("scooters.encrypt_username")
    @patch("scooters.get_current_user")
    @patch("scooters.check_permission")
    def test_update_scooter_invalid_battery_level(
        self, mock_check_perm, mock_get_user, mock_encrypt, mock_conn
    ):
        """Test updating scooter with invalid battery level"""
        mock_check_perm.return_value = True
        mock_get_user.return_value = {"username": "admin_001", "role": "system_admin"}
        mock_encrypt.return_value = "encrypted_serial"

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,) + ("data",) * 7
        mock_conn.return_value.cursor.return_value = mock_cursor

        success, msg = update_scooter("SC123456", battery_level=150)

        assert success is False
        assert "validation error" in msg.lower()

    @patch("scooters.get_connection")
    @patch("scooters.encrypt_username")
    @patch("scooters.get_current_user")
    @patch("scooters.check_permission")
    def test_update_scooter_invalid_status(
        self, mock_check_perm, mock_get_user, mock_encrypt, mock_conn
    ):
        """Test updating scooter with invalid status"""
        mock_check_perm.return_value = True
        mock_get_user.return_value = {"username": "admin_001", "role": "system_admin"}
        mock_encrypt.return_value = "encrypted_serial"

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,) + ("data",) * 7
        mock_conn.return_value.cursor.return_value = mock_cursor

        success, msg = update_scooter("SC123456", status="invalid_status")

        assert success is False
        assert "validation error" in msg.lower()


# ============================================================================
# Delete Scooter Tests
# ============================================================================


@pytest.mark.unit
class TestDeleteScooter:
    """Test deleting scooters"""

    @patch("scooters.get_current_user")
    def test_delete_scooter_service_engineer_denied(self, mock_get_user):
        """Test service engineer cannot delete scooters"""
        mock_get_user.return_value = {
            "username": "engineer1",
            "role": "service_engineer",
        }

        success, msg = delete_scooter("SC123456")

        assert success is False
        assert "cannot delete" in msg.lower()

    @patch("scooters.get_current_user")
    @patch("scooters.check_permission")
    def test_delete_scooter_no_permission(self, mock_check_perm, mock_get_user):
        """Test deleting scooter without permission"""
        mock_get_user.return_value = {"username": "user", "role": "system_admin"}
        mock_check_perm.return_value = False

        success, msg = delete_scooter("SC123456")

        assert success is False
        assert "access denied" in msg.lower()

    @patch("scooters.log_activity")
    @patch("scooters.get_connection")
    @patch("scooters.encrypt_username")
    @patch("scooters.get_current_user")
    @patch("scooters.check_permission")
    def test_delete_scooter_success(
        self, mock_check_perm, mock_get_user, mock_encrypt, mock_conn, mock_log
    ):
        """Test successfully deleting scooter"""
        mock_get_user.return_value = {"username": "admin_001", "role": "system_admin"}
        mock_check_perm.return_value = True
        mock_encrypt.return_value = "encrypted_serial"

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ("Model X", "Amsterdam")
        mock_conn.return_value.cursor.return_value = mock_cursor

        success, msg = delete_scooter("SC123456")

        assert success is True
        assert "deleted successfully" in msg.lower()
        # Check DELETE was called
        delete_call = [
            call for call in mock_cursor.execute.call_args_list if "DELETE" in str(call)
        ]
        assert len(delete_call) == 1

    @patch("scooters.get_connection")
    @patch("scooters.encrypt_username")
    @patch("scooters.get_current_user")
    @patch("scooters.check_permission")
    def test_delete_scooter_not_found(
        self, mock_check_perm, mock_get_user, mock_encrypt, mock_conn
    ):
        """Test deleting non-existent scooter"""
        mock_get_user.return_value = {"username": "admin_001", "role": "system_admin"}
        mock_check_perm.return_value = True
        mock_encrypt.return_value = "encrypted_serial"

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.cursor.return_value = mock_cursor

        success, msg = delete_scooter("SC999999")

        assert success is False
        assert "not found" in msg.lower()


# ============================================================================
# Search Scooters Tests
# ============================================================================


@pytest.mark.unit
class TestSearchScooters:
    """Test searching for scooters"""

    def test_search_scooters_empty_key(self):
        """Test searching with empty search key"""
        results = search_scooters("")

        assert results == []

    def test_search_scooters_short_key(self):
        """Test searching with too short search key"""
        results = search_scooters("a")

        assert results == []

    @patch("scooters.decrypt_username")
    @patch("scooters.get_connection")
    def test_search_scooters_success(self, mock_conn, mock_decrypt):
        """Test successfully searching scooters"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            (
                1,
                "encrypted_serial1",
                "Model X",
                85,
                "available",
                "Amsterdam Central",
                "01-01-2025",
                "2024-12-01",
            ),
            (
                2,
                "encrypted_serial2",
                "Model X Pro",
                90,
                "in_use",
                "Amsterdam West",
                "02-01-2025",
                "2024-12-02",
            ),
        ]
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_decrypt.side_effect = ["SC123456", "SC123457"]

        results = search_scooters("Model X")

        assert len(results) == 2
        assert results[0]["serial_number"] == "SC123456"
        assert results[0]["type"] == "Model X"
        assert results[1]["serial_number"] == "SC123457"
        assert results[1]["type"] == "Model X Pro"

    @patch("scooters.decrypt_username")
    @patch("scooters.get_connection")
    def test_search_scooters_by_location(self, mock_conn, mock_decrypt):
        """Test searching scooters by location"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            (
                1,
                "encrypted_serial",
                "Model X",
                85,
                "available",
                "Rotterdam Central",
                None,
                "2025-01-01",
            ),
        ]
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_decrypt.return_value = "SC123456"

        results = search_scooters("Rotterdam")

        assert len(results) == 1
        assert results[0]["location"] == "Rotterdam Central"

    @patch("scooters.decrypt_username")
    @patch("scooters.get_connection")
    def test_search_scooters_by_status(self, mock_conn, mock_decrypt):
        """Test searching scooters by status"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            (
                1,
                "encrypted_serial",
                "Model X",
                85,
                "maintenance",
                "Amsterdam",
                None,
                "2025-01-01",
            ),
        ]
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_decrypt.return_value = "SC123456"

        results = search_scooters("maintenance")

        assert len(results) == 1
        assert results[0]["status"] == "maintenance"

    @patch("scooters.get_connection")
    def test_search_scooters_no_results(self, mock_conn):
        """Test searching with no matching results"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_conn.return_value.cursor.return_value = mock_cursor

        results = search_scooters("nonexistent")

        assert results == []


# ============================================================================
# Get Scooter By Serial Tests
# ============================================================================


@pytest.mark.unit
class TestGetScooterBySerial:
    """Test getting scooter by serial number"""

    @patch("scooters.decrypt_username")
    @patch("scooters.encrypt_username")
    @patch("scooters.get_connection")
    def test_get_scooter_by_serial_success(self, mock_conn, mock_encrypt, mock_decrypt):
        """Test successfully getting scooter by serial"""
        mock_encrypt.return_value = "encrypted_serial"
        mock_decrypt.return_value = "SC123456"

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (
            1,
            "encrypted_serial",
            "Model X",
            85,
            "available",
            "Amsterdam",
            "01-01-2025",
            "2024-12-01",
        )
        mock_conn.return_value.cursor.return_value = mock_cursor

        scooter = get_scooter_by_serial("SC123456")

        assert scooter is not None
        assert scooter["serial_number"] == "SC123456"
        assert scooter["type"] == "Model X"
        assert scooter["battery_level"] == 85
        assert scooter["status"] == "available"
        assert scooter["location"] == "Amsterdam"

    @patch("scooters.encrypt_username")
    @patch("scooters.get_connection")
    def test_get_scooter_by_serial_not_found(self, mock_conn, mock_encrypt):
        """Test getting non-existent scooter"""
        mock_encrypt.return_value = "encrypted_serial"

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.cursor.return_value = mock_cursor

        scooter = get_scooter_by_serial("SC999999")

        assert scooter is None


# ============================================================================
# List All Scooters Tests
# ============================================================================


@pytest.mark.unit
class TestListAllScooters:
    """Test listing all scooters"""

    @patch("scooters.decrypt_username")
    @patch("scooters.get_connection")
    def test_list_all_scooters_success(self, mock_conn, mock_decrypt):
        """Test successfully listing all scooters"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            (
                1,
                "encrypted_serial1",
                "Model X",
                85,
                "available",
                "Amsterdam",
                "01-01-2025",
                "2024-12-01",
            ),
            (
                2,
                "encrypted_serial2",
                "Model Y",
                90,
                "in_use",
                "Rotterdam",
                "02-01-2025",
                "2024-12-02",
            ),
        ]
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_decrypt.side_effect = ["SC123456", "SC123457"]

        scooters = list_all_scooters()

        assert len(scooters) == 2
        assert scooters[0]["serial_number"] == "SC123456"
        assert scooters[0]["type"] == "Model X"
        assert scooters[1]["serial_number"] == "SC123457"
        assert scooters[1]["type"] == "Model Y"

    @patch("scooters.get_connection")
    def test_list_all_scooters_empty(self, mock_conn):
        """Test listing scooters when database is empty"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_conn.return_value.cursor.return_value = mock_cursor

        scooters = list_all_scooters()

        assert scooters == []

    @patch("scooters.decrypt_username")
    @patch("scooters.get_connection")
    def test_list_all_scooters_decrypts_serial_numbers(self, mock_conn, mock_decrypt):
        """Test that serial numbers are decrypted"""
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            (
                1,
                "encrypted_serial",
                "Model X",
                85,
                "available",
                "Amsterdam",
                None,
                "2025-01-01",
            ),
        ]
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_decrypt.return_value = "SC123456"

        scooters = list_all_scooters()

        assert len(scooters) == 1
        mock_decrypt.assert_called_once_with("encrypted_serial")
        assert scooters[0]["serial_number"] == "SC123456"
