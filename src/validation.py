# ═══════════════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════════════
# Description: Input validation libraries
#
# External libraries: re (regex), datetime (date validation)
# ═══════════════════════════════════════════════════════════════════════════

import re
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: CUSTOM EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════════════
# Description: Custom exception for validation errors
#
# Key components:
# - ValidationError: Raised when input validation fails
# ═══════════════════════════════════════════════════════════════════════════


class ValidationError(Exception):
    """Custom exception for input validation failures."""

    pass


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: USER CREDENTIAL VALIDATION
# ═══════════════════════════════════════════════════════════════════════════
# Description: Validate username and password formats
#
# Key components:
# - validate_username(): 8-10 chars, specific character rules
# - validate_password(): 12-30 chars, complexity requirements
#
# Note: Strong validation ensures system security
# ═══════════════════════════════════════════════════════════════════════════


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
        if not re.match(r"^[a-zA-Z_]", username):  # pragma: no cover
            raise ValidationError("Username must start with a letter or underscore")
        if not re.match(r"^[a-zA-Z0-9_'.]+$", username):  # pragma: no cover
            raise ValidationError(
                "Username can only contain letters, digits, underscore, apostrophe, and period"
            )
        return username.lower()

    # Validate length for regular users
    if len(username) < 8:
        raise ValidationError("Username must be at least 8 characters long. Expected: 8-10 characters (e.g., john_doe)")
    if len(username) > 10:
        raise ValidationError("Username must be at most 10 characters long. Expected: 8-10 characters (e.g., john_doe)")

    if not re.match(r"^[a-zA-Z_]", username):
        raise ValidationError("Username must start with a letter or underscore. Expected: starts with letter or _ (e.g., john_doe, _username)")

    if not re.match(r"^[a-zA-Z0-9_'.]+$", username):
        raise ValidationError(
            "Username can only contain letters, digits, underscore, apostrophe, and period. Expected: alphanumeric plus _'. (e.g., john_doe, user.123)"
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
        raise ValidationError("Password must be at least 12 characters long. Expected: 12-30 characters (e.g., MySecure@Pass123)")
    if len(password) > 30:
        raise ValidationError("Password must be at most 30 characters long. Expected: 12-30 characters (e.g., MySecure@Pass123)")

    if not re.search(r"[a-z]", password):
        raise ValidationError("Password must contain at least 1 lowercase letter. Expected: includes a-z, A-Z, 0-9, special chars (e.g., MySecure@Pass123)")

    if not re.search(r"[A-Z]", password):
        raise ValidationError("Password must contain at least 1 uppercase letter. Expected: includes a-z, A-Z, 0-9, special chars (e.g., MySecure@Pass123)")

    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least 1 digit. Expected: includes a-z, A-Z, 0-9, special chars (e.g., MySecure@Pass123)")

    if not re.search(r"[~!@#$%&_\-+=`|\\(){}[\]:;'<>,.?/]", password):
        raise ValidationError(
            r"Password must contain at least 1 special character. Expected: includes ~!@#$%&_-+=`|\(){}[]:;'<>,.?/ (e.g., MySecure@Pass123)"
        )

    return password


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: CONTACT INFORMATION VALIDATION
# ═══════════════════════════════════════════════════════════════════════════
# Description: Validate email and phone number formats
#
# Key components:
# - validate_email(): RFC-compliant email format
# - validate_phone(): Dutch mobile format (+31-6-DDDDDDDD)
#
# Note: Phone numbers are automatically formatted
# ═══════════════════════════════════════════════════════════════════════════


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
        raise ValidationError("Email cannot be longer than 50 characters. Expected: max 50 chars (e.g., user@example.com)")

    email_pattern = r"^[a-zA-Z0-9._+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format. Expected: user@domain.tld (e.g., john.doe@example.com)")

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
        raise ValidationError("Phone number must be exactly 8 digits. Expected: 8 digits (e.g., 12345678)")

    return f"+31-6-{phone_clean}"


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: ADDRESS VALIDATION
# ═══════════════════════════════════════════════════════════════════════════
# Description: Validate address components (Dutch format)
#
# Key components:
# - validate_zipcode(): Dutch postal code (DDDDXX format)
# - validate_house_number(): House number with optional addition
# - validate_city(): City from predefined list
#
# Note: Zipcodes and cities follow Dutch standards
# ═══════════════════════════════════════════════════════════════════════════


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


def validate_date(date_str, field_name="Date", must_be_past=False):
    """
    Validate date format and check if it's a valid calendar date.

    Format: DD-MM-YYYY
    Example: 15-03-1995, 01-12-2024

    Args:
        date_str (str): Date string
        field_name (str): Field name for error messages
        must_be_past (bool): If True, date must be in the past (for birthdays)

    Returns:
        str: Validated date (DD-MM-YYYY)

    Raises:
        ValidationError: If date is invalid or in the future when must_be_past=True
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
        date_obj = datetime(year, month, day)
    except ValueError:
        raise ValidationError(
            f"Invalid {field_name.lower()}. Please enter a valid calendar date"
        )

    # Check if date must be in the past (e.g., for birthdays)
    if must_be_past:
        today = datetime.now()
        if date_obj > today:
            raise ValidationError(
                f"{field_name} cannot be in the future. Expected: date in the past (e.g., 15-03-1995)"
            )

        # Check if date is not more than 150 years in the past
        max_years_ago = 150
        earliest_allowed = datetime(today.year - max_years_ago, today.month, today.day)
        if date_obj < earliest_allowed:
            raise ValidationError(
                f"{field_name} cannot be more than {max_years_ago} years in the past. Expected: within last {max_years_ago} years"
            )

    return date_str


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
        raise ValidationError("House number cannot be empty. Expected: max 6 chars, starts with digit (e.g., 42, 42A)")

    if len(house_number) > 6:
        raise ValidationError("House number cannot be longer than 6 characters. Expected: max 6 chars (e.g., 42, 42A, 42-1)")

    if not re.match(r"^\d", house_number):
        raise ValidationError("House number must start with a digit. Expected: starts with digit (e.g., 42A, 123-B)")

    if not re.match(r"^[\d\w\-]+$", house_number):
        raise ValidationError("House number contains invalid characters. Expected: digits, letters, hyphens (e.g., 42, 42A, 42-1)")

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


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: PERSONAL INFORMATION VALIDATION
# ═══════════════════════════════════════════════════════════════════════════
# Description: Validate personal data (names, dates, gender, documents)
#
# Key components:
# - validate_name(): Names and street names (letters, spaces, hyphens, apostrophes)
# - validate_date(): Date in DD-MM-YYYY format with calendar validation
# - validate_gender(): Male or Female
# - validate_driving_license(): Dutch license format (X(X)DDDDDDD)
#
# Note: Date validation checks for valid calendar dates (e.g., no Feb 30)
# ═══════════════════════════════════════════════════════════════════════════


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


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: SCOOTER-SPECIFIC VALIDATION
# ═══════════════════════════════════════════════════════════════════════════
# Description: Validate scooter fleet data
#
# Key components:
# - validate_serial_number(): 6-15 alphanumeric characters
# - validate_scooter_type(): Scooter model/type (2-30 chars)
# - validate_battery_level(): Integer 0-100
# - validate_location(): Location string (2-50 chars)
#
# Note: Serial numbers are automatically converted to uppercase
# ═══════════════════════════════════════════════════════════════════════════


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
        raise ValidationError("Serial number must be at least 6 characters long. Expected: 6-15 alphanumeric chars (e.g., ABC123XYZ)")
    if len(serial_number) > 15:
        raise ValidationError("Serial number must be at most 15 characters long. Expected: 6-15 alphanumeric chars (e.g., ABC123XYZ)")

    # Validate format (alphanumeric only)
    if not re.match(r"^[A-Z0-9]+$", serial_number):
        raise ValidationError("Serial number can only contain letters and digits. Expected: alphanumeric only (e.g., ABC123XYZ, SERIAL2024)")

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
        raise ValidationError("Scooter type must be at least 2 characters long. Expected: 2-30 characters (e.g., E-Scooter Pro, Model X)")
    if len(scooter_type) > 30:
        raise ValidationError("Scooter type must be at most 30 characters long. Expected: 2-30 characters (e.g., E-Scooter Pro)")

    # Validate format (letters, digits, spaces, hyphens)
    if not re.match(r"^[a-zA-Z0-9\s\-]+$", scooter_type):
        raise ValidationError(
            "Scooter type can only contain letters, digits, spaces, and hyphens. Expected: letters, digits, spaces, - (e.g., E-Scooter Pro, Model X2)"
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
            raise ValidationError("Battery level must be a number. Expected: integer 0-100 (e.g., 75, 100)")

    if not isinstance(battery_level, int):
        raise ValidationError("Battery level must be an integer. Expected: integer 0-100 (e.g., 75, 100)")

    if battery_level < 0:
        raise ValidationError("Battery level cannot be negative. Expected: 0-100 (e.g., 0, 50, 100)")
    if battery_level > 100:
        raise ValidationError("Battery level cannot exceed 100. Expected: 0-100 (e.g., 0, 50, 100)")

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
        raise ValidationError("Location must be at least 2 characters long. Expected: 2-50 characters (e.g., Dam Square, Station 5)")
    if len(location) > 50:
        raise ValidationError("Location must be at most 50 characters long. Expected: 2-50 characters (e.g., Central Station)")

    # Validate format (allow letters, digits, spaces, and common punctuation)
    if not re.match(r"^[a-zA-Z0-9\s,.\-']+$", location):
        raise ValidationError(
            "Location can only contain letters, digits, spaces, and basic punctuation. Expected: letters, digits, spaces, ,.'-  (e.g., Dam Square, Station 5)"
        )

    return location
