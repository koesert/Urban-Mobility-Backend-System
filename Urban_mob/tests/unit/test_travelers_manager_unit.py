import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
from managers.travelers_manager import TravelersManager


class TestTravelersManagerUnit:
    """Unit tests for TravelersManager - isolated component testing"""

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
    def travelers_manager(self, mock_auth_service):
        """Create TravelersManager with mocked dependencies"""
        with patch("managers.travelers_manager.encrypt_field") as mock_encrypt, patch(
            "managers.travelers_manager.decrypt_field"
        ) as mock_decrypt:

            # Mock encryption functions to return predictable values
            mock_encrypt.side_effect = lambda x: f"encrypted_{x}"
            mock_decrypt.side_effect = lambda x: x.replace("encrypted_", "")

            manager = TravelersManager(mock_auth_service)
            return manager

    def test_initialization_verifies_encryption_system(self, mock_auth_service):
        """Test that initialization verifies encryption system"""
        with patch("managers.travelers_manager.encrypt_field") as mock_encrypt, patch(
            "managers.travelers_manager.decrypt_field"
        ) as mock_decrypt:

            # Setup successful encryption test
            mock_encrypt.return_value = "encrypted_test"
            mock_decrypt.return_value = "test@example.com"

            # Act
            manager = TravelersManager(mock_auth_service)

            # Assert
            mock_encrypt.assert_called_once_with("test@example.com")
            mock_decrypt.assert_called_once_with("encrypted_test")
            assert manager.auth == mock_auth_service

    def test_initialization_raises_error_on_encryption_failure(self, mock_auth_service):
        """Test that initialization fails when encryption system is broken"""
        with patch("managers.travelers_manager.encrypt_field") as mock_encrypt, patch(
            "managers.travelers_manager.decrypt_field"
        ) as mock_decrypt:

            # Setup encryption failure
            mock_encrypt.side_effect = Exception("Encryption key not found")

            # Act & Assert
            with pytest.raises(
                Exception, match="Encryption system initialization failed"
            ):
                TravelersManager(mock_auth_service)

    def test_can_manage_travelers_returns_true_for_authorized_roles(
        self, travelers_manager
    ):
        """Test authorized roles can manage travelers"""
        authorized_roles = ["super_admin", "system_admin"]

        for role in authorized_roles:
            # Arrange
            travelers_manager.auth.current_user["role"] = role

            # Act & Assert
            assert travelers_manager.can_manage_travelers() is True

    def test_can_manage_travelers_returns_false_for_unauthorized_roles(
        self, travelers_manager
    ):
        """Test unauthorized roles cannot manage travelers"""
        unauthorized_scenarios = [
            {"role": "service_engineer"},
            {"role": "invalid_role"},
            None,  # No current user
        ]

        for scenario in unauthorized_scenarios:
            # Arrange
            travelers_manager.auth.current_user = scenario

            # Act & Assert
            assert travelers_manager.can_manage_travelers() is False

    def test_generate_customer_id_creates_sequential_ids(self, travelers_manager):
        """Test customer ID generation creates sequential IDs"""
        # Arrange
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (5,)  # 5 existing travelers

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        travelers_manager.db.get_connection.return_value = mock_conn

        # Act
        customer_id = travelers_manager._generate_customer_id()

        # Assert
        assert customer_id == "CUST000006"
        mock_cursor.execute.assert_called_once_with("SELECT COUNT(*) FROM travelers")

    def test_validate_email_accepts_valid_emails(self, travelers_manager):
        """Test email validation accepts valid email addresses"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "test123@test-domain.com",
            "user+tag@example.org",
            "simple@domain.nl",
        ]

        for email in valid_emails:
            # Act & Assert
            assert travelers_manager._validate_email(email) is True

    def test_validate_email_rejects_invalid_emails(self, travelers_manager):
        """Test email validation rejects invalid email addresses"""
        invalid_emails = [
            "invalid.email",
            "@domain.com",
            "user@",
            "user@domain",
            "user..double.dot@domain.com",
            "user name@domain.com",  # Space
            "",
            "user@domain..com",
        ]

        for email in invalid_emails:
            # Act & Assert
            assert travelers_manager._validate_email(email) is False

    def test_validate_date_accepts_valid_dates(self, travelers_manager):
        """Test date validation accepts valid DD-MM-YYYY format"""
        valid_dates = [
            "01-01-1990",
            "31-12-2000",
            "15-06-1985",
            "29-02-2020",  # Leap year
            "28-02-2021",  # Non-leap year
        ]

        for date in valid_dates:
            # Act & Assert
            assert travelers_manager._validate_date(date) is True

    def test_validate_date_rejects_invalid_dates(self, travelers_manager):
        """Test date validation rejects invalid dates"""
        invalid_dates = [
            "1990-01-01",  # Wrong format
            "32-01-1990",  # Invalid day
            "01-13-1990",  # Invalid month
            "29-02-2021",  # Invalid leap year
            "invalid-date",
            "",
            "1-1-90",  # Wrong format
        ]

        for date in invalid_dates:
            # Act & Assert
            assert travelers_manager._validate_date(date) is False

    def test_validate_dutch_zipcode_accepts_valid_codes(self, travelers_manager):
        """Test Dutch zipcode validation"""
        valid_zipcodes = [
            "1234AB",
            "9999ZZ",
            "0000AA",
            "1111bb",  # Should work with lowercase
        ]

        for zipcode in valid_zipcodes:
            # Act & Assert
            assert travelers_manager._validate_dutch_zipcode(zipcode) is True

    def test_validate_dutch_zipcode_rejects_invalid_codes(self, travelers_manager):
        """Test Dutch zipcode validation rejects invalid codes"""
        invalid_zipcodes = [
            "12345",  # Too short
            "1234ABC",  # Too long
            "ABCD12",  # Wrong format
            "12AB34",  # Mixed up
            "",
            "1234 AB",  # Space
        ]

        for zipcode in invalid_zipcodes:
            # Act & Assert
            assert travelers_manager._validate_dutch_zipcode(zipcode) is False

    def test_validate_dutch_mobile_accepts_valid_numbers(self, travelers_manager):
        """Test Dutch mobile phone validation"""
        valid_numbers = ["12345678", "87654321", "00000000", "99999999"]

        for number in valid_numbers:
            # Act & Assert
            assert travelers_manager._validate_dutch_mobile(number) is True

    def test_validate_dutch_mobile_rejects_invalid_numbers(self, travelers_manager):
        """Test Dutch mobile phone validation rejects invalid numbers"""
        invalid_numbers = [
            "1234567",  # Too short
            "123456789",  # Too long
            "12345abc",  # Contains letters
            "+31612345678",  # Includes prefix
            "",
            "12 34 56 78",  # Spaces
        ]

        for number in invalid_numbers:
            # Act & Assert
            assert travelers_manager._validate_dutch_mobile(number) is False

    def test_format_dutch_mobile_adds_prefix(self, travelers_manager):
        """Test Dutch mobile formatting adds correct prefix"""
        # Act
        formatted = travelers_manager._format_dutch_mobile("12345678")

        # Assert
        assert formatted == "+31 6 12345678"

    def test_validate_driving_license_accepts_valid_formats(self, travelers_manager):
        """Test driving license validation accepts valid formats"""
        valid_licenses = [
            "AB1234567",  # 2 letters + 7 digits
            "A1234567",  # 1 letter + 7 digits
            "XY9876543",
        ]

        for license_num in valid_licenses:
            # Act & Assert
            assert travelers_manager._validate_driving_license(license_num) is True

    def test_validate_driving_license_rejects_invalid_formats(self, travelers_manager):
        """Test driving license validation rejects invalid formats"""
        invalid_licenses = [
            "ABC123456",  # 3 letters
            "123456789",  # No letters
            "A123456",  # Too short
            "AB12345678",  # Too long
            "ab1234567",  # Lowercase (should work with .upper())
            "",
            "A12B3456",  # Mixed format
        ]

        # Note: lowercase should actually pass because the method calls .upper()
        for license_num in invalid_licenses:
            if license_num == "ab1234567":
                assert travelers_manager._validate_driving_license(license_num) is True
            else:
                assert travelers_manager._validate_driving_license(license_num) is False

    def test_validate_house_number_accepts_valid_numbers(self, travelers_manager):
        """Test house number validation"""
        valid_house_numbers = ["1", "123", "45a", "67B", "89-91", "100bis", "1234"]

        for house_num in valid_house_numbers:
            # Act & Assert
            assert travelers_manager._validate_house_number(house_num) is True

    def test_validate_house_number_rejects_invalid_numbers(self, travelers_manager):
        """Test house number validation rejects invalid numbers"""
        invalid_house_numbers = [
            "",
            "abc",  # No digits
            "0",  # Too low
            "10000",  # Too high
            "12345678901",  # Too long
            "-5",  # Negative
        ]

        for house_num in invalid_house_numbers:
            # Act & Assert
            assert travelers_manager._validate_house_number(house_num) is False

    @patch("builtins.input")
    def test_get_required_input_returns_value_on_first_try(
        self, mock_input, travelers_manager
    ):
        """Test _get_required_input returns value when user provides input"""
        # Arrange
        mock_input.return_value = "John"

        # Act
        result = travelers_manager._get_required_input("First Name")

        # Assert
        assert result == "John"
        mock_input.assert_called_once_with("First Name: ")

    @patch("builtins.input")
    def test_get_required_input_retries_on_empty_input(
        self, mock_input, travelers_manager
    ):
        """Test _get_required_input retries when user provides empty input"""
        # Arrange
        mock_input.side_effect = ["", "y", "John"]  # Empty, retry yes, then valid input

        # Act
        result = travelers_manager._get_required_input("First Name")

        # Assert
        assert result == "John"
        assert mock_input.call_count == 3

    @patch("builtins.input")
    def test_get_yes_no_input_accepts_valid_responses(
        self, mock_input, travelers_manager
    ):
        """Test _get_yes_no_input handles y/n responses correctly"""
        test_cases = [("y", True), ("n", False), ("Y", True), ("N", False)]

        for input_val, expected in test_cases:
            # Arrange
            mock_input.return_value = input_val

            # Act
            result = travelers_manager._get_yes_no_input("Continue?")

            # Assert
            assert result == expected

    @patch("builtins.input")
    def test_get_yes_no_input_retries_on_invalid_input(
        self, mock_input, travelers_manager
    ):
        """Test _get_yes_no_input retries on invalid input"""
        # Arrange
        mock_input.side_effect = ["maybe", "yes", "y"]  # Invalid, invalid, valid

        # Act
        result = travelers_manager._get_yes_no_input("Continue?")

        # Assert
        assert result is True
        assert mock_input.call_count == 3

    @patch("builtins.input")
    def test_get_city_selection_returns_valid_city(self, mock_input, travelers_manager):
        """Test city selection returns correct city"""
        # Arrange
        mock_input.return_value = "1"  # Rotterdam (first city)

        # Act
        result = travelers_manager._get_city_selection()

        # Assert
        assert result == "Rotterdam"

    @patch("builtins.input")
    def test_get_city_selection_handles_invalid_selection(
        self, mock_input, travelers_manager
    ):
        """Test city selection handles invalid input gracefully"""
        # Arrange
        mock_input.side_effect = ["11", "y", "1"]  # Invalid, retry, valid

        # Act
        result = travelers_manager._get_city_selection()

        # Assert
        assert result == "Rotterdam"

    def test_get_traveler_by_id_returns_traveler_data(self, travelers_manager):
        """Test _get_traveler_by_id returns correct traveler"""
        # Arrange
        expected_traveler = (1, "CUST000001", "John", "Doe", "01-01-1990")

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = expected_traveler

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        travelers_manager.db.get_connection.return_value = mock_conn

        # Act
        result = travelers_manager._get_traveler_by_id("CUST000001")

        # Assert
        assert result == expected_traveler
        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM travelers WHERE customer_id = ?", ("CUST000001",)
        )

    def test_get_traveler_by_id_returns_none_for_nonexistent(self, travelers_manager):
        """Test _get_traveler_by_id returns None for non-existent traveler"""
        # Arrange
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        travelers_manager.db.get_connection.return_value = mock_conn

        # Act
        result = travelers_manager._get_traveler_by_id("NONEXISTENT")

        # Assert
        assert result is None

    def test_get_traveler_by_id_handles_database_error(self, travelers_manager):
        """Test _get_traveler_by_id handles database errors gracefully"""
        # Arrange
        travelers_manager.db.get_connection.side_effect = Exception("Database error")

        # Act
        result = travelers_manager._get_traveler_by_id("CUST000001")

        # Assert
        assert result is None

    @patch("builtins.print")
    def test_display_traveler_details_shows_decrypted_data(
        self, mock_print, travelers_manager
    ):
        """Test _display_traveler_details shows properly decrypted sensitive data"""
        # Arrange
        traveler_data = (
            1,
            "CUST000001",
            "John",
            "Doe",
            "01-01-1990",
            "Male",
            "Main St",
            "123",
            "1234AB",
            "Amsterdam",
            "encrypted_john@example.com",  # email
            "encrypted_+31 6 12345678",  # phone
            "encrypted_AB1234567",  # license
            "2024-01-01T10:00:00",
        )

        # Act
        travelers_manager._display_traveler_details(traveler_data)

        # Assert - check that print was called with decrypted values
        print_calls = [call.args[0] for call in mock_print.call_args_list]

        # Should show decrypted email, phone, and license
        email_printed = any("john@example.com" in str(call) for call in print_calls)
        phone_printed = any("+31 6 12345678" in str(call) for call in print_calls)
        license_printed = any("AB1234567" in str(call) for call in print_calls)

        assert email_printed, "Email should be decrypted in display"
        assert phone_printed, "Phone should be decrypted in display"
        assert license_printed, "License should be decrypted in display"

    @patch("builtins.print")
    def test_display_traveler_details_handles_decryption_error(
        self, mock_print, travelers_manager
    ):
        """Test _display_traveler_details handles decryption errors gracefully"""
        # Arrange
        with patch("managers.travelers_manager.decrypt_field") as mock_decrypt:
            mock_decrypt.side_effect = Exception("Decryption failed")

            traveler_data = (
                1,
                "CUST000001",
                "John",
                "Doe",
                "01-01-1990",
                "Male",
                "Main St",
                "123",
                "1234AB",
                "Amsterdam",
                "corrupted_encrypted_data",  # email
                "corrupted_encrypted_data",  # phone
                "corrupted_encrypted_data",  # license
                "2024-01-01T10:00:00",
            )

            # Act
            travelers_manager._display_traveler_details(traveler_data)

            # Assert - should show [ENCRYPTED] for corrupted data
            print_calls = [call.args[0] for call in mock_print.call_args_list]
            encrypted_shown = any("[ENCRYPTED]" in str(call) for call in print_calls)
            assert encrypted_shown, "Should show [ENCRYPTED] for corrupted data"

    def test_display_traveler_details_handles_none_input(self, travelers_manager):
        """Test _display_traveler_details handles None input gracefully"""
        # Act & Assert - should not raise exception
        travelers_manager._display_traveler_details(None)

    @patch("builtins.input")
    @patch("builtins.print")
    def test_display_travelers_menu_shows_correct_options(
        self, mock_print, mock_input, travelers_manager
    ):
        """Test display_travelers_menu shows all management options"""
        # Arrange
        mock_input.return_value = "6"  # Back to main menu

        # Act
        choice = travelers_manager.display_travelers_menu()

        # Assert
        assert choice == "6"

        # Check that menu options were printed
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        menu_text = " ".join(str(call) for call in print_calls)

        expected_options = [
            "View All Travelers",
            "Search Traveler",
            "Add New Traveler",
            "Update Traveler",
            "Delete Traveler",
            "Back to Main Menu",
        ]

        for option in expected_options:
            assert option in menu_text

    @patch("builtins.print")
    def test_display_travelers_menu_denies_access_for_unauthorized_user(
        self, mock_print, travelers_manager
    ):
        """Test display_travelers_menu denies access for unauthorized users"""
        # Arrange
        travelers_manager.auth.current_user = {"role": "service_engineer"}

        # Act
        result = travelers_manager.display_travelers_menu()

        # Assert
        assert result is None
        mock_print.assert_called_with("Access denied: Insufficient permissions!")
