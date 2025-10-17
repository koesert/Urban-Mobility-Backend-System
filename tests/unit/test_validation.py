"""
Unit tests for validation.py module.

Tests all 16 validation functions with valid inputs, invalid inputs,
and edge cases.
"""

import pytest
from validation import (
    ValidationError,
    validate_username,
    validate_password,
    validate_email,
    validate_phone,
    validate_zipcode,
    validate_driving_license,
    validate_date,
    validate_name,
    validate_house_number,
    validate_city,
    validate_gender,
    validate_serial_number,
    validate_scooter_type,
    validate_battery_level,
    validate_location,
    VALID_CITIES,
)


# ============================================================================
# Username Validation Tests
# ============================================================================

@pytest.mark.unit
class TestUsernameValidation:
    """Test validate_username function"""

    def test_valid_usernames(self):
        """Test valid username inputs"""
        assert validate_username("john_doe") == "john_doe"
        assert validate_username("JANE.DOE") == "jane.doe"
        assert validate_username("user_123") == "user_123"
        assert validate_username("admin_usr") == "admin_usr"

    def test_super_admin_allowed(self):
        """Test that super_admin bypasses length rules"""
        assert validate_username("super_admin") == "super_admin"

    def test_username_case_insensitive(self):
        """Test that usernames are converted to lowercase"""
        assert validate_username("TestUser") == "testuser"
        assert validate_username("UPPERCASE") == "uppercase"

    def test_username_too_short(self):
        """Test usernames that are too short"""
        with pytest.raises(ValidationError, match="at least 8 characters"):
            validate_username("short")

    def test_username_too_long(self):
        """Test usernames that are too long"""
        with pytest.raises(ValidationError, match="at most 10 characters"):
            validate_username("toolongusername")

    def test_username_invalid_start(self):
        """Test usernames that don't start with letter or underscore"""
        with pytest.raises(ValidationError, match="must start with a letter or underscore"):
            validate_username("123start")

    def test_username_invalid_chars(self):
        """Test usernames with invalid characters"""
        with pytest.raises(ValidationError, match="can only contain"):
            validate_username("user@name")


# ============================================================================
# Password Validation Tests
# ============================================================================

@pytest.mark.unit
class TestPasswordValidation:
    """Test validate_password function"""

    def test_valid_passwords(self):
        """Test valid password inputs"""
        assert validate_password("MyPassword123!") == "MyPassword123!"
        assert validate_password("Secure@Pass2024") == "Secure@Pass2024"
        assert validate_password("ValidPass123#") == "ValidPass123#"

    def test_password_too_short(self):
        """Test passwords that are too short"""
        with pytest.raises(ValidationError, match="at least 12 characters"):
            validate_password("Short1!")

    def test_password_too_long(self):
        """Test passwords that are too long"""
        with pytest.raises(ValidationError, match="at most 30 characters"):
            validate_password("ThisIsAVeryLongPasswordThatExceeds30Characters!")

    def test_password_no_lowercase(self):
        """Test passwords without lowercase letters"""
        with pytest.raises(ValidationError, match="at least 1 lowercase letter"):
            validate_password("ALLUPPERCASE123!")

    def test_password_no_uppercase(self):
        """Test passwords without uppercase letters"""
        with pytest.raises(ValidationError, match="at least 1 uppercase letter"):
            validate_password("alllowercase123!")

    def test_password_no_digit(self):
        """Test passwords without digits"""
        with pytest.raises(ValidationError, match="at least 1 digit"):
            validate_password("NoDigitsHere!")

    def test_password_no_special_char(self):
        """Test passwords without special characters"""
        with pytest.raises(ValidationError, match="at least 1 special character"):
            validate_password("NoSpecial123")


# ============================================================================
# Email Validation Tests
# ============================================================================

@pytest.mark.unit
class TestEmailValidation:
    """Test validate_email function"""

    @pytest.mark.parametrize("email,expected", [
        ("user@example.com", "user@example.com"),
        ("UPPER@CASE.COM", "upper@case.com"),
        ("test.email+tag@domain.co.uk", "test.email+tag@domain.co.uk"),
        ("  spaces@example.com  ", "spaces@example.com"),
    ])
    def test_valid_emails(self, email, expected):
        """Test valid email inputs"""
        assert validate_email(email) == expected

    def test_email_too_long(self):
        """Test email that exceeds 50 characters"""
        long_email = "a" * 40 + "@example.com"
        with pytest.raises(ValidationError, match="cannot be longer than 50 characters"):
            validate_email(long_email)

    @pytest.mark.parametrize("invalid_email", [
        "invalid",
        "@example.com",
        "user@",
        "user@.com",
        "user.example.com",
    ])
    def test_invalid_email_format(self, invalid_email):
        """Test invalid email formats"""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email(invalid_email)


# ============================================================================
# Phone Validation Tests
# ============================================================================

@pytest.mark.unit
class TestPhoneValidation:
    """Test validate_phone function"""

    @pytest.mark.parametrize("phone,expected", [
        ("12345678", "+31-6-12345678"),
        ("87654321", "+31-6-87654321"),
        ("+31-6-12345678", "+31-6-12345678"),
        ("  12345678  ", "+31-6-12345678"),
    ])
    def test_valid_phones(self, phone, expected):
        """Test valid phone number inputs"""
        assert validate_phone(phone) == expected

    @pytest.mark.parametrize("invalid_phone", [
        "1234567",  # Too short
        "123456789",  # Too long
        "1234abcd",  # Contains letters
    ])
    def test_invalid_phones(self, invalid_phone):
        """Test invalid phone number formats"""
        with pytest.raises(ValidationError, match="must be exactly 8 digits"):
            validate_phone(invalid_phone)


# ============================================================================
# Zipcode Validation Tests
# ============================================================================

@pytest.mark.unit
class TestZipcodeValidation:
    """Test validate_zipcode function"""

    @pytest.mark.parametrize("zipcode,expected", [
        ("3011AB", "3011AB"),
        ("1234XY", "1234XY"),
        ("3011ab", "3011AB"),  # Converts to uppercase
        ("3011 AB", "3011AB"),  # Removes spaces
    ])
    def test_valid_zipcodes(self, zipcode, expected):
        """Test valid zipcode inputs"""
        assert validate_zipcode(zipcode) == expected

    @pytest.mark.parametrize("invalid_zipcode", [
        "301AB",  # Too short
        "3011ABC",  # Too long
        "ABCD12",  # Wrong format
        "3011A",  # Incomplete
    ])
    def test_invalid_zipcodes(self, invalid_zipcode):
        """Test invalid zipcode formats"""
        with pytest.raises(ValidationError, match="Invalid zipcode format"):
            validate_zipcode(invalid_zipcode)


# ============================================================================
# Driving License Validation Tests
# ============================================================================

@pytest.mark.unit
class TestDrivingLicenseValidation:
    """Test validate_driving_license function"""

    @pytest.mark.parametrize("license,expected", [
        ("AB1234567", "AB1234567"),
        ("X1234567", "X1234567"),
        ("ab1234567", "AB1234567"),  # Converts to uppercase
        ("AB 1234567", "AB1234567"),  # Removes spaces
    ])
    def test_valid_licenses(self, license, expected):
        """Test valid driving license inputs"""
        assert validate_driving_license(license) == expected

    @pytest.mark.parametrize("invalid_license", [
        "ABC123456",  # Too many letters
        "A123456",  # Too few digits
        "1234567",  # No letters
        "ABCDEFG",  # No digits
    ])
    def test_invalid_licenses(self, invalid_license):
        """Test invalid driving license formats"""
        with pytest.raises(ValidationError, match="Invalid driving license format"):
            validate_driving_license(invalid_license)


# ============================================================================
# Date Validation Tests
# ============================================================================

@pytest.mark.unit
class TestDateValidation:
    """Test validate_date function"""

    @pytest.mark.parametrize("date_str", [
        "15-03-1995",
        "01-01-2000",
        "31-12-2024",
        "29-02-2020",  # Leap year
    ])
    def test_valid_dates(self, date_str):
        """Test valid date inputs"""
        assert validate_date(date_str) == date_str

    @pytest.mark.parametrize("invalid_date", [
        "15/03/1995",  # Wrong separator
        "2024-03-15",  # Wrong format
        "32-01-2024",  # Invalid day
        "15-13-2024",  # Invalid month
        "29-02-2023",  # Not a leap year
    ])
    def test_invalid_dates(self, invalid_date):
        """Test invalid date inputs"""
        with pytest.raises(ValidationError):
            validate_date(invalid_date)


# ============================================================================
# Name Validation Tests
# ============================================================================

@pytest.mark.unit
class TestNameValidation:
    """Test validate_name function"""

    @pytest.mark.parametrize("name", [
        "John",
        "Mary-Jane",
        "O'Brien",
        "Van der Berg",
    ])
    def test_valid_names(self, name):
        """Test valid name inputs"""
        assert validate_name(name) == name

    def test_name_too_long(self):
        """Test name that exceeds 50 characters"""
        long_name = "A" * 51
        with pytest.raises(ValidationError, match="cannot be longer than 50 characters"):
            validate_name(long_name)

    def test_name_empty(self):
        """Test empty name"""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_name("")

    def test_name_invalid_chars(self):
        """Test name with invalid characters"""
        with pytest.raises(ValidationError, match="can only contain"):
            validate_name("John123")


# ============================================================================
# House Number Validation Tests
# ============================================================================

@pytest.mark.unit
class TestHouseNumberValidation:
    """Test validate_house_number function"""

    @pytest.mark.parametrize("house_number", [
        "42",
        "42A",
        "42-1",
        "123bis",
    ])
    def test_valid_house_numbers(self, house_number):
        """Test valid house number inputs"""
        assert validate_house_number(house_number) == house_number

    def test_house_number_too_long(self):
        """Test house number that exceeds 6 characters"""
        with pytest.raises(ValidationError, match="cannot be longer than 6 characters"):
            validate_house_number("1234567")

    def test_house_number_empty(self):
        """Test empty house number"""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_house_number("")

    def test_house_number_invalid_start(self):
        """Test house number that doesn't start with digit"""
        with pytest.raises(ValidationError, match="must start with a digit"):
            validate_house_number("A42")


# ============================================================================
# City Validation Tests
# ============================================================================

@pytest.mark.unit
class TestCityValidation:
    """Test validate_city function"""

    @pytest.mark.parametrize("city", VALID_CITIES)
    def test_valid_cities(self, city):
        """Test all valid cities"""
        assert validate_city(city) == city

    def test_invalid_city(self):
        """Test invalid city"""
        with pytest.raises(ValidationError, match="must be one of"):
            validate_city("InvalidCity")


# ============================================================================
# Gender Validation Tests
# ============================================================================

@pytest.mark.unit
class TestGenderValidation:
    """Test validate_gender function"""

    @pytest.mark.parametrize("gender", ["Male", "Female"])
    def test_valid_genders(self, gender):
        """Test valid gender inputs"""
        assert validate_gender(gender) == gender

    def test_invalid_gender(self):
        """Test invalid gender"""
        with pytest.raises(ValidationError, match="must be 'Male' or 'Female'"):
            validate_gender("Other")


# ============================================================================
# Serial Number Validation Tests
# ============================================================================

@pytest.mark.unit
class TestSerialNumberValidation:
    """Test validate_serial_number function"""

    @pytest.mark.parametrize("serial,expected", [
        ("ABC123", "ABC123"),
        ("abc123xyz", "ABC123XYZ"),  # Converts to uppercase
        ("  SERIAL2024  ", "SERIAL2024"),  # Strips whitespace
    ])
    def test_valid_serial_numbers(self, serial, expected):
        """Test valid serial number inputs"""
        assert validate_serial_number(serial) == expected

    def test_serial_too_short(self):
        """Test serial number that is too short"""
        with pytest.raises(ValidationError, match="at least 6 characters"):
            validate_serial_number("ABC12")

    def test_serial_too_long(self):
        """Test serial number that is too long"""
        with pytest.raises(ValidationError, match="at most 15 characters"):
            validate_serial_number("A" * 16)

    def test_serial_invalid_chars(self):
        """Test serial number with invalid characters"""
        with pytest.raises(ValidationError, match="can only contain letters and digits"):
            validate_serial_number("ABC-123")


# ============================================================================
# Scooter Type Validation Tests
# ============================================================================

@pytest.mark.unit
class TestScooterTypeValidation:
    """Test validate_scooter_type function"""

    @pytest.mark.parametrize("scooter_type", [
        "E-Scooter",
        "Model X",
        "Pro 2024",
    ])
    def test_valid_scooter_types(self, scooter_type):
        """Test valid scooter type inputs"""
        assert validate_scooter_type(scooter_type) == scooter_type

    def test_scooter_type_too_short(self):
        """Test scooter type that is too short"""
        with pytest.raises(ValidationError, match="at least 2 characters"):
            validate_scooter_type("A")

    def test_scooter_type_too_long(self):
        """Test scooter type that is too long"""
        with pytest.raises(ValidationError, match="at most 30 characters"):
            validate_scooter_type("A" * 31)


# ============================================================================
# Battery Level Validation Tests
# ============================================================================

@pytest.mark.unit
class TestBatteryLevelValidation:
    """Test validate_battery_level function"""

    @pytest.mark.parametrize("level,expected", [
        (0, 0),
        (50, 50),
        (100, 100),
        ("75", 75),  # String input
        ("  100  ", 100),  # String with spaces
    ])
    def test_valid_battery_levels(self, level, expected):
        """Test valid battery level inputs"""
        assert validate_battery_level(level) == expected

    def test_battery_level_negative(self):
        """Test negative battery level"""
        with pytest.raises(ValidationError, match="cannot be negative"):
            validate_battery_level(-1)

    def test_battery_level_too_high(self):
        """Test battery level above 100"""
        with pytest.raises(ValidationError, match="cannot exceed 100"):
            validate_battery_level(101)

    def test_battery_level_invalid_string(self):
        """Test non-numeric string"""
        with pytest.raises(ValidationError, match="must be a number"):
            validate_battery_level("abc")


# ============================================================================
# Location Validation Tests
# ============================================================================

@pytest.mark.unit
class TestLocationValidation:
    """Test validate_location function"""

    @pytest.mark.parametrize("location", [
        "Central Station",
        "Dam Square",
        "Location-5",
    ])
    def test_valid_locations(self, location):
        """Test valid location inputs"""
        assert validate_location(location) == location

    def test_location_too_short(self):
        """Test location that is too short"""
        with pytest.raises(ValidationError, match="at least 2 characters"):
            validate_location("A")

    def test_location_too_long(self):
        """Test location that is too long"""
        with pytest.raises(ValidationError, match="at most 50 characters"):
            validate_location("A" * 51)

    def test_location_invalid_chars(self):
        """Test location with invalid characters"""
        with pytest.raises(ValidationError, match="can only contain"):
            validate_location("Location@#$")
