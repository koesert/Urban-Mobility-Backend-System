import pytest
from unittest.mock import Mock, patch, MagicMock
from scooter import (
    is_valid_serial_number,
    is_valid_location,
    is_valid_iso_date,
    prompt_str,
    prompt_int,
    prompt_location,
    prompt_iso_date,
    add_new_scooter,
    delete_scooter,
    modify_scooter,
)


class TestScootersManagerUnit:
    """Unit tests for scooter management logic"""

    @pytest.fixture
    def mock_role_manager(self):
        mock = Mock()
        mock.get_available_permissions.return_value = [
            "add_scooter", "delete_scooter", "update_scooter_info", "manage_scooters"
        ]
        return mock

    def test_is_valid_serial_number_accepts_valid(self):
        assert is_valid_serial_number("ABC1234567")
        assert is_valid_serial_number("1234567890A")
        assert is_valid_serial_number("A1B2C3D4E5F6G7")

    def test_is_valid_serial_number_rejects_invalid(self):
        assert not is_valid_serial_number("short")
        assert not is_valid_serial_number("toolongserialnumber123")
        assert not is_valid_serial_number("invalid*chars!")

    def test_is_valid_location_accepts_valid(self):
        assert is_valid_location("51.92250")
        assert is_valid_location("-4.47917")

    def test_is_valid_location_rejects_invalid(self):
        assert not is_valid_location("51.9225")  # only 4 decimals
        assert not is_valid_location("abc")
        assert not is_valid_location("51.922500")  # 6 decimals

    def test_is_valid_iso_date_accepts_valid(self):
        assert is_valid_iso_date("2024-06-19")
        assert is_valid_iso_date("2000-01-01")

    def test_is_valid_iso_date_rejects_invalid(self):
        assert not is_valid_iso_date("19-06-2024")
        assert not is_valid_iso_date("2024/06/19")
        assert not is_valid_iso_date("2024-13-01")

    @patch("builtins.input", side_effect=["", "BrandX"])
    def test_prompt_str_retries_on_empty(self, mock_input):
        result = prompt_str("Brand")
        assert result == "BrandX"

    @patch("builtins.input", side_effect=["abc", "123"])
    def test_prompt_int_retries_on_invalid(self, mock_input):
        result = prompt_int("Top Speed")
        assert result == 123

    @patch("builtins.input", side_effect=["51.9225", "51.92250"])
    def test_prompt_location_retries_on_invalid(self, mock_input):
        result = prompt_location("Latitude")
        assert result == 51.92250

    @patch("builtins.input", side_effect=["2024/06/19", "2024-06-19"])
    def test_prompt_iso_date_retries_on_invalid(self, mock_input):
        result = prompt_iso_date("Last Maintenance Date")
        assert result == "2024-06-19"

    @patch("scooter.DatabaseContext")
    @patch("scooter.prompt_str", return_value="BrandX")
    @patch("scooter.prompt_int", return_value=25)
    @patch("scooter.prompt_location", return_value=51.92250)
    @patch("scooter.prompt_serial_number", return_value="ABC1234567")
    @patch("scooter.prompt_iso_date", return_value="2024-06-19")
    @patch("builtins.input", return_value="")
    def test_add_new_scooter_permission_denied(
        self, mock_input, mock_iso, mock_serial, mock_loc, mock_int, mock_str, mock_db
    ):
        mock_role_manager = Mock()
        mock_role_manager.get_available_permissions.return_value = []
        add_new_scooter(mock_role_manager)
        mock_db().insert_scooter.assert_not_called()

    @patch("scooter.DatabaseContext")
    @patch("builtins.input", side_effect=["1"])
    def test_delete_scooter_permission_denied(self, mock_input, mock_db):
        mock_role_manager = Mock()
        mock_role_manager.get_available_permissions.return_value = []
        delete_scooter(mock_role_manager)
        mock_db().delete_scooter_by_id.assert_not_called()

    @patch("scooter.DatabaseContext")
    @patch("builtins.input", side_effect=["1"])
    def test_delete_scooter_success(self, mock_input, mock_db):
        mock_role_manager = Mock()
        mock_role_manager.get_available_permissions.return_value = [
            "delete_scooter"]
        mock_db().show_all_scooters.return_value = [
            {"id": 1, "brand": "BrandX", "model": "ModelY",
                "serial_number": "ABC1234567", "out_of_service_status": ""}
        ]
        mock_db().delete_scooter_by_id.return_value = True
        delete_scooter(mock_role_manager)
        mock_db().delete_scooter_by_id.assert_called_with(1)

    @patch("scooter.DatabaseContext")
    @patch("builtins.input", side_effect=["1"])
    def test_modify_scooter_permission_denied(self, mock_input, mock_db):
        mock_role_manager = Mock()
        mock_role_manager.get_available_permissions.return_value = []
        modify_scooter(mock_role_manager)
        # Should not call update_scooter_by_id
        mock_db().update_scooter_by_id.assert_not_called()
