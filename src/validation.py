import re
from datetime import datetime


class ValidationError(Exception):
    """Custom exception for input validation failures."""

    pass


def validate_username(username):
    """
    Validate username format.

    Rules:
    - 8-10 characters (except "super_admin" system account)
    - Start with letter or underscore
    - Can contain: letters, digits, underscore, apostrophe, period
    - Case-insensitive

    Args:
        username (str): Username to validate

    Returns:
        str: Validated username (lowercase)

    Raises:
        ValidationError: If username is invalid
    """
    if not isinstance(username, str):
        raise ValidationError("Username must be a string")

    username = username.strip()

    # Special case: allow "super_admin" system account (bypasses length rule)
    if username.lower() == "super_admin":
        if not re.match(r"^[a-zA-Z_]", username):
            raise ValidationError("Username must start with a letter or underscore")
        if not re.match(r"^[a-zA-Z0-9_'.]+$", username):
            raise ValidationError(
                "Username can only contain letters, digits, underscore, apostrophe, and period"
            )
        return username.lower()

    # Validate length for regular users
    if len(username) < 8:
        raise ValidationError("Username must be at least 8 characters long")
    if len(username) > 10:
        raise ValidationError("Username must be at most 10 characters long")

    if not re.match(r"^[a-zA-Z_]", username):
        raise ValidationError("Username must start with a letter or underscore")

    if not re.match(r"^[a-zA-Z0-9_'.]+$", username):
        raise ValidationError(
            "Username can only contain letters, digits, underscore, apostrophe, and period"
        )

    return username.lower()


def validate_password(password):
    """
    Validate password strength.

    Rules:
    - 12-30 characters
    - At least 1 lowercase, 1 uppercase, 1 digit
    - At least 1 special character: ~!@#$%&_-+=`|\\(){}[]:;'<>,.?/

    Args:
        password (str): Password to validate

    Returns:
        str: Validated password (unchanged)

    Raises:
        ValidationError: If password is invalid
    """
    if not isinstance(password, str):
        raise ValidationError("Password must be a string")

    if len(password) < 12:
        raise ValidationError("Password must be at least 12 characters long")
    if len(password) > 30:
        raise ValidationError("Password must be at most 30 characters long")

    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least 1 lowercase letter")

    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least 1 uppercase letter")

    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least 1 digit")

    if not re.search(r"[~!@#$%&_\-+=`|\\(){}[\]:;'<>,.?/]", password):
        raise ValidationError(
            r"Password must contain at least 1 special character (~!@#$%&_-+=`|\(){}[]:;'<>,.?/)"
        )

    return password


def validate_email(email):
    """
    Validate email format.

    Rules:
    - Max 50 characters
    - Pattern: user@domain.tld
    - Local part can contain: letters, digits, ., _, +, -

    Args:
        email (str): Email to validate

    Returns:
        str: Validated email (lowercase)

    Raises:
        ValidationError: If email is invalid
    """
    if not isinstance(email, str):
        raise ValidationError("Email must be a string")

    email = email.strip()

    if len(email) > 50:
        raise ValidationError("Email cannot be longer than 50 characters")

    email_pattern = r"^[a-zA-Z0-9._+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format. Expected: user@domain.tld")

    return email.lower()


def validate_phone(phone):
    """
    Validate and format Dutch mobile phone number.

    Accepts:
    - 8 digits (DDDDDDDD)
    - Already formatted (+31-6-DDDDDDDD)

    Output: +31-6-DDDDDDDD

    Args:
        phone (str): Phone number (8 digits or already formatted)

    Returns:
        str: Formatted phone (+31-6-DDDDDDDD)

    Raises:
        ValidationError: If phone is invalid
    """
    if not isinstance(phone, str):
        raise ValidationError("Phone number must be a string")

    # Remove all formatting characters
    phone_clean = phone.replace(" ", "").replace("-", "").replace("+", "")

    # Check if already formatted (+31-6-DDDDDDDD format)
    if phone_clean.startswith("316") and len(phone_clean) == 11:
        # Extract last 8 digits
        phone_clean = phone_clean[3:]
    
    # Validate: must be exactly 8 digits
    if not re.match(r"^\d{8}$", phone_clean):
        raise ValidationError("Phone number must be exactly 8 digits")

    return f"+31-6-{phone_clean}"


def validate_zipcode(zipcode):
    """
    Validate Dutch zipcode format.

    Format: DDDDXX (4 digits + 2 letters)
    Example: 3011AB, 1234XY

    Automatically converts letters to UPPERCASE.

    Args:
        zipcode (str): Zipcode to validate

    Returns:
        str: Validated zipcode in UPPERCASE format

    Raises:
        ValidationError: If zipcode is invalid
    """
    if not isinstance(zipcode, str):
        raise ValidationError("Zipcode must be a string")

    zipcode = zipcode.replace(" ", "").upper()

    if not re.match(r"^\d{4}[A-Z]{2}$", zipcode):
        raise ValidationError(
            "Invalid zipcode format. Expected: DDDDXX (4 digits + 2 letters, e.g., 3011AB)"
        )

    return zipcode


def validate_driving_license(license_number):
    """
    Validate Dutch driving license format.

    Format: XDDDDDDD or XXDDDDDDD (1-2 letters + 7 digits)
    Example: AB1234567, X1234567

    Automatically converts letters to UPPERCASE.

    Args:
        license_number (str): Driving license number

    Returns:
        str: Validated license in UPPERCASE format

    Raises:
        ValidationError: If license is invalid
    """
    if not isinstance(license_number, str):
        raise ValidationError("Driving license must be a string")

    license_number = license_number.replace(" ", "").upper()

    if not re.match(r"^[A-Z]{1,2}\d{7}$", license_number):
        raise ValidationError(
            "Invalid driving license format. Expected: XDDDDDDD or XXDDDDDDD (1-2 letters + 7 digits, e.g., AB1234567)"
        )

    return license_number


def validate_date(date_str, field_name="Date"):
    """
    Validate date format and check if it's a valid calendar date.

    Format: DD-MM-YYYY
    Example: 15-03-1995, 01-12-2024

    Args:
        date_str (str): Date string
        field_name (str): Field name for error messages

    Returns:
        str: Validated date (DD-MM-YYYY)

    Raises:
        ValidationError: If date is invalid
    """
    if not isinstance(date_str, str):
        raise ValidationError(f"{field_name} must be a string")

    date_str = date_str.strip()

    if not re.match(r"^\d{2}-\d{2}-\d{4}$", date_str):
        raise ValidationError(
            f"Invalid {field_name.lower()} format. Expected: DD-MM-YYYY (e.g., 15-03-1995)"
        )

    try:
        day, month, year = map(int, date_str.split("-"))
        datetime(year, month, day)
    except ValueError:
        raise ValidationError(
            f"Invalid {field_name.lower()}. Please enter a valid calendar date"
        )

    return date_str


def validate_name(name, field_name="Name"):
    """
    Validate names (first name, last name, street name).

    Rules:
    - 1-50 characters
    - Only letters, spaces, hyphens, apostrophes

    Args:
        name (str): Name to validate
        field_name (str): Field name for error messages

    Returns:
        str: Validated name

    Raises:
        ValidationError: If name is invalid
    """
    if not isinstance(name, str):
        raise ValidationError(f"{field_name} must be a string")

    name = name.strip()

    if not name:
        raise ValidationError(f"{field_name} cannot be empty")

    if len(name) > 50:
        raise ValidationError(f"{field_name} cannot be longer than 50 characters")

    if not re.match(r"^[a-zA-Z\s\-']+$", name):
        raise ValidationError(
            f"{field_name} can only contain letters, spaces, hyphens, and apostrophes"
        )

    return name


def validate_house_number(house_number):
    """
    Validate house number format.

    Rules:
    - Max 6 characters
    - Must start with a digit
    - Can include letters or additions

    Examples: 42, 42A, 42-1, 42bis

    Args:
        house_number (str): House number to validate

    Returns:
        str: Validated house number

    Raises:
        ValidationError: If house number is invalid
    """
    if not isinstance(house_number, str):
        raise ValidationError("House number must be a string")

    house_number = house_number.strip()

    if not house_number:
        raise ValidationError("House number cannot be empty")

    if len(house_number) > 6:
        raise ValidationError("House number cannot be longer than 6 characters")

    if not re.match(r"^\d", house_number):
        raise ValidationError("House number must start with a digit")

    if not re.match(r"^[\d\w\-]+$", house_number):
        raise ValidationError("House number contains invalid characters")

    return house_number


# Predefined list of valid Dutch cities
VALID_CITIES = [
    "Amsterdam",
    "Rotterdam",
    "Utrecht",
    "Den Haag",
    "Eindhoven",
    "Groningen",
    "Tilburg",
    "Almere",
    "Breda",
    "Nijmegen",
]


def validate_city(city):
    """
    Validate city against predefined list.

    Valid cities: Amsterdam, Rotterdam, Utrecht, Den Haag, Eindhoven,
                  Groningen, Tilburg, Almere, Breda, Nijmegen

    Args:
        city (str): City to validate

    Returns:
        str: Validated city

    Raises:
        ValidationError: If city is not in predefined list
    """
    if not isinstance(city, str):
        raise ValidationError("City must be a string")

    city = city.strip()

    if city not in VALID_CITIES:
        raise ValidationError(f"City must be one of: {', '.join(VALID_CITIES)}")

    return city


def validate_gender(gender):
    """
    Validate gender value.

    Must be "Male" or "Female".

    Args:
        gender (str): Gender to validate

    Returns:
        str: Validated gender

    Raises:
        ValidationError: If gender is invalid
    """
    if not isinstance(gender, str):
        raise ValidationError("Gender must be a string")

    gender = gender.strip()

    if gender not in ["Male", "Female"]:
        raise ValidationError("Gender must be 'Male' or 'Female'")

    return gender


def validate_serial_number(serial_number):
    """
    Validate scooter serial number format.

    Rules:
    - 6-15 characters
    - Alphanumeric only
    - Must start with letter or digit

    Args:
        serial_number (str): Serial number to validate

    Returns:
        str: Validated serial number (uppercase)

    Raises:
        ValidationError: If serial number is invalid
    """
    if not isinstance(serial_number, str):
        raise ValidationError("Serial number must be a string")

    serial_number = serial_number.strip().upper()

    # Validate length
    if len(serial_number) < 6:
        raise ValidationError("Serial number must be at least 6 characters long")
    if len(serial_number) > 15:
        raise ValidationError("Serial number must be at most 15 characters long")

    # Validate format (alphanumeric only)
    if not re.match(r"^[A-Z0-9]+$", serial_number):
        raise ValidationError("Serial number can only contain letters and digits")

    return serial_number


def validate_scooter_type(scooter_type):
    """
    Validate scooter type/model format.

    Rules:
    - 2-30 characters
    - Can contain letters, digits, spaces, hyphens

    Args:
        scooter_type (str): Scooter type to validate

    Returns:
        str: Validated scooter type

    Raises:
        ValidationError: If scooter type is invalid
    """
    if not isinstance(scooter_type, str):
        raise ValidationError("Scooter type must be a string")

    scooter_type = scooter_type.strip()

    # Validate length
    if len(scooter_type) < 2:
        raise ValidationError("Scooter type must be at least 2 characters long")
    if len(scooter_type) > 30:
        raise ValidationError("Scooter type must be at most 30 characters long")

    # Validate format (letters, digits, spaces, hyphens)
    if not re.match(r"^[a-zA-Z0-9\s\-]+$", scooter_type):
        raise ValidationError(
            "Scooter type can only contain letters, digits, spaces, and hyphens"
        )

    return scooter_type


def validate_battery_level(battery_level):
    """
    Validate battery level value.

    Must be integer between 0 and 100.

    Args:
        battery_level (int or str): Battery level to validate

    Returns:
        int: Validated battery level

    Raises:
        ValidationError: If battery level is invalid
    """
    # Convert string to int if needed
    if isinstance(battery_level, str):
        try:
            battery_level = int(battery_level.strip())
        except ValueError:
            raise ValidationError("Battery level must be a number")

    if not isinstance(battery_level, int):
        raise ValidationError("Battery level must be an integer")

    if battery_level < 0:
        raise ValidationError("Battery level cannot be negative")
    if battery_level > 100:
        raise ValidationError("Battery level cannot exceed 100")

    return battery_level


def validate_location(location):
    """
    Validate location string.

    Rules:
    - 2-50 characters
    - Can contain letters, digits, spaces, common punctuation

    Args:
        location (str): Location to validate

    Returns:
        str: Validated location

    Raises:
        ValidationError: If location is invalid
    """
    if not isinstance(location, str):
        raise ValidationError("Location must be a string")

    location = location.strip()

    # Validate length
    if len(location) < 2:
        raise ValidationError("Location must be at least 2 characters long")
    if len(location) > 50:
        raise ValidationError("Location must be at most 50 characters long")

    # Validate format (allow letters, digits, spaces, and common punctuation)
    if not re.match(r"^[a-zA-Z0-9\s,.\-']+$", location):
        raise ValidationError(
            "Location can only contain letters, digits, spaces, and basic punctuation"
        )

    return location


# Testing and demonstration
if __name__ == "__main__":
    print("=" * 60)
    print("VALIDATION TESTING")
    print("=" * 60)

    test_cases = [
        (
            "Username",
            validate_username,
            ["john_doe", "Jane.Doe", "user_123", "admin_usr", "super_admin"],
        ),
        (
            "Password",
            validate_password,
            ["MyPassword123!", "Secure@Pass2024", "ValidPass123#"],
        ),
        ("Email", validate_email, ["user@example.com", "john.doe@company.co.uk"]),
        ("Phone", validate_phone, ["12345678", "87654321"]),
        ("Zipcode", validate_zipcode, ["3011AB", "1234XY", "9876CD"]),
        ("License", validate_driving_license, ["AB1234567", "X1234567", "PQ9876543"]),
        ("Date", validate_date, ["15-03-1995", "01-12-2024"]),
        ("City", validate_city, ["Amsterdam", "Rotterdam", "Tilburg"]),
    ]

    for test_name, validator, valid_inputs in test_cases:
        print(f"\n--- Testing {test_name} ---")
        for input_val in valid_inputs:
            try:
                result = validator(input_val)
                print(f"✅ {input_val:20s} → {result}")
            except ValidationError as e:
                print(f"❌ {input_val:20s} → ERROR: {e}")

    print("\n" + "=" * 60)
    print("TESTING INVALID INPUTS (Should show errors)")
    print("=" * 60)

    invalid_tests = [
        ("Username", validate_username, ["john", "123john", "toolongusername"]),
        ("Password", validate_password, ["short", "nouppercase123!", "NoSpecial123"]),
        ("Email", validate_email, ["invalid", "@example.com", "user@.com"]),
        ("Phone", validate_phone, ["1234567", "123456789", "1234abcd"]),
        ("Zipcode", validate_zipcode, ["301AB", "3011ABC", "3011ab"]),
        ("License", validate_driving_license, ["ab1234567", "ABC123456", "A123456"]),
    ]

    for test_name, validator, invalid_inputs in invalid_tests:
        print(f"\n--- Testing {test_name} (Invalid) ---")
        for input_val in invalid_inputs:
            try:
                result = validator(input_val)
                print(f"⚠️  {input_val:20s} → {result} (SHOULD HAVE FAILED!)")
            except ValidationError as e:
                print(f"✅ {input_val:20s} → Correctly rejected: {e}")
