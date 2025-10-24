# ═══════════════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════════════
# Description: Input validation libraries
#
# External libraries: re (regex), datetime (date validation), logging (security monitoring)
# ═══════════════════════════════════════════════════════════════════════════

import re
from datetime import datetime
from activity_log import log_activity


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
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
# Description: Internal helper functions for validation
#
# Key components:
# - _check_null_bytes(): Check for null bytes in string input
# ═══════════════════════════════════════════════════════════════════════════


def _check_null_bytes(value, field_name):
    """
    Check for null bytes in string input.

    Null bytes should never be present in non-binary input and can indicate
    attack attempts (e.g., null-byte injection attacks).

    Args:
        value: The value to check (typically a string)
        field_name (str): Name of the field being validated (for logging)

    Raises:
        ValidationError: If null byte is detected
    """
    if isinstance(value, str) and "\0" in value:
        log_activity(
            username="SYSTEM",
            activity="Null-byte attack detected",
            additional_info=f"Field: {field_name}, Value: {repr(value[:50])}",
            suspicious=True,
        )
        raise ValidationError(f"{field_name} contains invalid null-byte character")


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

    _check_null_bytes(username, "Username")
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
        raise ValidationError(
            "Username must be at least 8 characters long. Expected: 8-10 characters (e.g., john_doe)"
        )
    if len(username) > 10:
        raise ValidationError(
            "Username must be at most 10 characters long. Expected: 8-10 characters (e.g., john_doe)"
        )

    if not re.match(r"^[a-zA-Z_]", username):
        raise ValidationError(
            "Username must start with a letter or underscore. Expected: starts with letter or _ (e.g., john_doe, _username)"
        )

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

    _check_null_bytes(password, "Password")

    if len(password) < 12:
        raise ValidationError(
            "Password must be at least 12 characters long. Expected: 12-30 characters (e.g., MySecure@Pass123)"
        )
    if len(password) > 30:
        raise ValidationError(
            "Password must be at most 30 characters long. Expected: 12-30 characters (e.g., MySecure@Pass123)"
        )

    if not re.search(r"[a-z]", password):
        raise ValidationError(
            "Password must contain at least 1 lowercase letter. Expected: includes a-z, A-Z, 0-9, special chars (e.g., MySecure@Pass123)"
        )

    if not re.search(r"[A-Z]", password):
        raise ValidationError(
            "Password must contain at least 1 uppercase letter. Expected: includes a-z, A-Z, 0-9, special chars (e.g., MySecure@Pass123)"
        )

    if not re.search(r"\d", password):
        raise ValidationError(
            "Password must contain at least 1 digit. Expected: includes a-z, A-Z, 0-9, special chars (e.g., MySecure@Pass123)"
        )

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

    _check_null_bytes(email, "Email")
    email = email.strip()

    if len(email) > 50:
        raise ValidationError(
            "Email cannot be longer than 50 characters. Expected: max 50 chars (e.g., user@example.com)"
        )

    email_pattern = r"^[a-zA-Z0-9._+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(email_pattern, email):
        raise ValidationError(
            "Invalid email format. Expected: user@domain.tld (e.g., john.doe@example.com)"
        )

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

    _check_null_bytes(phone, "Phone")

    # Remove all formatting characters
    phone_clean = phone.replace(" ", "").replace("-", "").replace("+", "")

    # Check if already formatted (+31-6-DDDDDDDD format)
    if phone_clean.startswith("316") and len(phone_clean) == 11:
        # Extract last 8 digits
        phone_clean = phone_clean[3:]

    # Validate: must be exactly 8 digits
    if not re.match(r"^\d{8}$", phone_clean):
        raise ValidationError(
            "Phone number must be exactly 8 digits. Expected: 8 digits (e.g., 12345678)"
        )

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

    _check_null_bytes(zipcode, "Zipcode")
    zipcode = zipcode.replace(" ", "").upper()

    if not re.match(r"^\d{4}[A-Z]{2}$", zipcode):
        raise ValidationError(
            "Invalid zipcode format. Expected: DDDDXX (4 digits + 2 letters, e.g., 3011AB)"
        )

    return zipcode


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

    _check_null_bytes(house_number, "House number")
    house_number = house_number.strip()

    if not house_number:
        raise ValidationError(
            "House number cannot be empty. Expected: max 6 chars, starts with digit (e.g., 42, 42A)"
        )

    if len(house_number) > 6:
        raise ValidationError(
            "House number cannot be longer than 6 characters. Expected: max 6 chars (e.g., 42, 42A, 42-1)"
        )

    if not re.match(r"^\d", house_number):
        raise ValidationError(
            "House number must start with a digit. Expected: starts with digit (e.g., 42A, 123-B)"
        )

    if not re.match(r"^[\d\w\-]+$", house_number):
        raise ValidationError(
            "House number contains invalid characters. Expected: digits, letters, hyphens (e.g., 42, 42A, 42-1)"
        )

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

    _check_null_bytes(city, "City")
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
# - validate_birthday(): Date in DD-MM-YYYY format with calendar validation
# - validate_date(): Date in ISO YYYY-MM-DD format
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

    _check_null_bytes(name, field_name)
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


def validate_birthday(date_str):
    """
    Validate birthday format and check if it's a valid calendar date.

    Format: DD-MM-YYYY
    Example: 15-03-1995, 01-12-2024

    Args:
        date_str (str): Birthday date string

    Returns:
        str: Validated birthday (DD-MM-YYYY)

    Raises:
        ValidationError: If birthday is invalid or in the future
    """
    if not isinstance(date_str, str):
        raise ValidationError("Birthday must be a string")

    _check_null_bytes(date_str, "Birthday")
    date_str = date_str.strip()

    if not re.match(r"^\d{2}-\d{2}-\d{4}$", date_str):
        raise ValidationError(
            "Invalid birthday format. Expected: DD-MM-YYYY (e.g., 15-03-1995)"
        )

    try:
        day, month, year = map(int, date_str.split("-"))
        date_obj = datetime(year, month, day)
    except ValueError:
        raise ValidationError("Invalid birthday. Please enter a valid calendar date")

    today = datetime.now()
    if date_obj > today:
        raise ValidationError(
            "Birthday cannot be in the future. Expected: date in the past (e.g., 15-03-1995)"
        )

    max_years_ago = 150
    earliest_allowed = datetime(today.year - max_years_ago, today.month, today.day)
    if date_obj < earliest_allowed:
        raise ValidationError(
            f"Birthday cannot be more than {max_years_ago} years in the past. Expected: within last {max_years_ago} years"
        )

    return date_str


def validate_date(date_str):
    """
    Validate date in ISO 8601 format and check if it's a valid calendar date.

    Format: YYYY-MM-DD
    Example: 2024-03-15, 1995-12-01

    Args:
        date_str (str): Date string in ISO 8601 format

    Returns:
        str: Validated date (YYYY-MM-DD)

    Raises:
        ValidationError: If date is invalid
    """
    if not isinstance(date_str, str):
        raise ValidationError("Date must be a string")

    _check_null_bytes(date_str, "Date")
    date_str = date_str.strip()

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        raise ValidationError(
            "Invalid date format. Expected: YYYY-MM-DD (e.g., 2024-03-15)"
        )

    try:
        year, month, day = map(int, date_str.split("-"))
        datetime(year, month, day)
    except ValueError:
        raise ValidationError("Invalid date. Please enter a valid calendar date")

    return date_str


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

    _check_null_bytes(gender, "Gender")
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

    _check_null_bytes(license_number, "Driving license")
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
# - validate_serial_number(): 10-17 alphanumeric characters
# - validate_scooter_type(): Scooter model/type (2-30 chars)
# - validate_state_of_charge(): Integer 0-100 (battery percentage)
# - validate_gps_location(): GPS coordinates for Rotterdam region
#
# Note: Serial numbers are automatically converted to uppercase
# ═══════════════════════════════════════════════════════════════════════════


def validate_serial_number(serial_number):
    """
    Validate scooter serial number format.

    Rules:
    - 10-17 alphanumeric characters
    - Alphanumeric only

    Args:
        serial_number (str): Serial number to validate

    Returns:
        str: Validated serial number (uppercase)

    Raises:
        ValidationError: If serial number is invalid
    """
    if not isinstance(serial_number, str):
        raise ValidationError("Serial number must be a string")

    _check_null_bytes(serial_number, "Serial number")
    serial_number = serial_number.strip().upper()

    if len(serial_number) < 10:
        raise ValidationError(
            "Serial number must be at least 10 characters long. Expected: 10-17 alphanumeric chars (e.g., ABC1234567XYZ)"
        )
    if len(serial_number) > 17:
        raise ValidationError(
            "Serial number must be at most 17 characters long. Expected: 10-17 alphanumeric chars (e.g., ABC1234567XYZ)"
        )

    if not re.match(r"^[A-Z0-9]+$", serial_number):
        raise ValidationError(
            "Serial number can only contain letters and digits. Expected: alphanumeric only (e.g., ABC1234567XYZ, SERIAL2024FLEET)"
        )

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

    _check_null_bytes(scooter_type, "Scooter type")
    scooter_type = scooter_type.strip()

    # Validate length
    if len(scooter_type) < 2:
        raise ValidationError(
            "Scooter type must be at least 2 characters long. Expected: 2-30 characters (e.g., E-Scooter Pro, Model X)"
        )
    if len(scooter_type) > 30:
        raise ValidationError(
            "Scooter type must be at most 30 characters long. Expected: 2-30 characters (e.g., E-Scooter Pro)"
        )

    # Validate format (letters, digits, spaces, hyphens)
    if not re.match(r"^[a-zA-Z0-9\s\-]+$", scooter_type):
        raise ValidationError(
            "Scooter type can only contain letters, digits, spaces, and hyphens. Expected: letters, digits, spaces, - (e.g., E-Scooter Pro, Model X2)"
        )

    return scooter_type


def validate_state_of_charge(soc):
    """
    Validate State of Charge (SoC) percentage.

    Must be integer between 0 and 100.

    Args:
        soc (int or str): State of Charge percentage to validate

    Returns:
        int: Validated SoC percentage

    Raises:
        ValidationError: If SoC is invalid
    """
    # Convert string to int if needed
    if isinstance(soc, str):
        try:
            soc = int(soc.strip())
        except ValueError:
            raise ValidationError(
                "State of Charge must be a number. Expected: integer 0-100 (e.g., 75, 100)"
            )

    if not isinstance(soc, int):
        raise ValidationError(
            "State of Charge must be an integer. Expected: integer 0-100 (e.g., 75, 100)"
        )

    if soc < 0:
        raise ValidationError(
            "State of Charge cannot be negative. Expected: 0-100 (e.g., 0, 50, 100)"
        )
    if soc > 100:
        raise ValidationError(
            "State of Charge cannot exceed 100. Expected: 0-100 (e.g., 0, 50, 100)"
        )

    return soc


def validate_gps_location(latitude, longitude):
    """
    Validate GPS coordinates for Rotterdam region.

    Format: 5 decimal places for 2-meter accuracy
    Rotterdam region bounds:
    - Latitude: 51.8000 to 52.0500
    - Longitude: 4.2500 to 4.6500

    Examples:
    - Rotterdam Centraal: 51.92481, 4.46910
    - Erasmusbrug: 51.91081, 4.48250
    - Markthal: 51.91988, 4.48548

    Args:
        latitude (float or str): Latitude coordinate
        longitude (float or str): Longitude coordinate

    Returns:
        tuple: (latitude, longitude) as floats with 5 decimal places

    Raises:
        ValidationError: If coordinates are invalid or outside Rotterdam region
    """
    # Check for null bytes in string inputs
    if isinstance(latitude, str):
        _check_null_bytes(latitude, "Latitude")
    if isinstance(longitude, str):
        _check_null_bytes(longitude, "Longitude")

    # Convert to float if string
    try:
        if isinstance(latitude, str):
            latitude = float(latitude.strip())
        if isinstance(longitude, str):
            longitude = float(longitude.strip())
    except (ValueError, AttributeError):
        raise ValidationError(
            "Coordinates must be valid numbers. Expected: latitude 51.8-52.05, longitude 4.25-4.65 (e.g., 51.92481, 4.46910)"
        )

    if not isinstance(latitude, (int, float)) or not isinstance(
        longitude, (int, float)
    ):
        raise ValidationError(
            "Coordinates must be numbers. Expected: latitude 51.8-52.05, longitude 4.25-4.65 (e.g., 51.92481, 4.46910)"
        )

    # Validate Rotterdam region bounds
    if latitude < 51.8000 or latitude > 52.0500:
        raise ValidationError(
            "Latitude must be within Rotterdam region. Expected: 51.8000 to 52.0500 (e.g., 51.92481 for Rotterdam Centraal)"
        )

    if longitude < 4.2500 or longitude > 4.6500:
        raise ValidationError(
            "Longitude must be within Rotterdam region. Expected: 4.2500 to 4.6500 (e.g., 4.46910 for Rotterdam Centraal)"
        )

    # Round to 5 decimal places for 2-meter accuracy
    latitude = round(latitude, 5)
    longitude = round(longitude, 5)

    return latitude, longitude


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 7: ADDITIONAL SCOOTER ATTRIBUTE VALIDATION
# ═══════════════════════════════════════════════════════════════════════════
# Description: Validate additional scooter fleet data
#
# Key components:
# - validate_brand(): Manufacturer name
# - validate_model(): Model name/number
# - validate_top_speed(): Maximum speed in km/h
# - validate_battery_capacity(): Total battery capacity in Wh
# - validate_target_range_soc(): Min/max battery percentage range
# - validate_out_of_service_status(): Availability status
# - validate_mileage(): Total distance travelled in km
# ═══════════════════════════════════════════════════════════════════════════


def validate_brand(brand):
    """
    Validate scooter brand/manufacturer name.

    Rules:
    - 2-50 characters
    - Can contain letters, digits, spaces, hyphens

    Args:
        brand (str): Brand name to validate

    Returns:
        str: Validated brand name

    Raises:
        ValidationError: If brand is invalid
    """
    if not isinstance(brand, str):
        raise ValidationError("Brand must be a string")

    _check_null_bytes(brand, "Brand")
    brand = brand.strip()

    if len(brand) < 2:
        raise ValidationError(
            "Brand must be at least 2 characters long. Expected: 2-50 characters (e.g., Segway, NIU)"
        )
    if len(brand) > 50:
        raise ValidationError(
            "Brand must be at most 50 characters long. Expected: 2-50 characters (e.g., Segway)"
        )

    if not re.match(r"^[a-zA-Z0-9\s\-]+$", brand):
        raise ValidationError(
            "Brand can only contain letters, digits, spaces, and hyphens. Expected: letters, digits, spaces, - (e.g., Segway, NIU, E-Rider)"
        )

    return brand


def validate_model(model):
    """
    Validate scooter model name/number.

    Rules:
    - 2-50 characters
    - Can contain letters, digits, spaces, hyphens

    Args:
        model (str): Model name to validate

    Returns:
        str: Validated model name

    Raises:
        ValidationError: If model is invalid
    """
    if not isinstance(model, str):
        raise ValidationError("Model must be a string")

    _check_null_bytes(model, "Model")
    model = model.strip()

    if len(model) < 2:
        raise ValidationError(
            "Model must be at least 2 characters long. Expected: 2-50 characters (e.g., ES2, Pro Max)"
        )
    if len(model) > 50:
        raise ValidationError(
            "Model must be at most 50 characters long. Expected: 2-50 characters (e.g., ES2)"
        )

    if not re.match(r"^[a-zA-Z0-9\s\-]+$", model):
        raise ValidationError(
            "Model can only contain letters, digits, spaces, and hyphens. Expected: letters, digits, spaces, - (e.g., ES2, Pro Max, X-100)"
        )

    return model


def validate_top_speed(speed):
    """
    Validate scooter top speed in km/h.

    Rules:
    - Must be number between 0 and 80 km/h
    - Can be integer or float

    Args:
        speed (int, float, or str): Top speed to validate

    Returns:
        float: Validated top speed

    Raises:
        ValidationError: If speed is invalid
    """
    # Convert string to float if needed
    if isinstance(speed, str):
        try:
            speed = float(speed.strip())
        except ValueError:
            raise ValidationError(
                "Top speed must be a number. Expected: 0-80 km/h (e.g., 25, 45.5)"
            )

    if not isinstance(speed, (int, float)):
        raise ValidationError(
            "Top speed must be a number. Expected: 0-80 km/h (e.g., 25, 45.5)"
        )

    if speed < 0:
        raise ValidationError(
            "Top speed cannot be negative. Expected: 0-80 km/h (e.g., 25, 45.5)"
        )
    if speed > 80:
        raise ValidationError(
            "Top speed cannot exceed 80 km/h. Expected: 0-80 km/h (e.g., 25, 45.5)"
        )

    return float(speed)


def validate_battery_capacity(capacity):
    """
    Validate battery capacity in watt-hours (Wh).

    Rules:
    - Must be integer between 0 and 10000 Wh
    - Typical e-scooter range: 250-1000 Wh

    Args:
        capacity (int or str): Battery capacity to validate

    Returns:
        int: Validated battery capacity

    Raises:
        ValidationError: If capacity is invalid
    """
    # Convert string to int if needed
    if isinstance(capacity, str):
        try:
            capacity = int(capacity.strip())
        except ValueError:
            raise ValidationError(
                "Battery capacity must be a number. Expected: 0-10000 Wh (e.g., 500, 750)"
            )

    if not isinstance(capacity, int):
        raise ValidationError(
            "Battery capacity must be an integer. Expected: 0-10000 Wh (e.g., 500, 750)"
        )

    if capacity < 0:
        raise ValidationError(
            "Battery capacity cannot be negative. Expected: 0-10000 Wh (e.g., 500, 750)"
        )
    if capacity > 10000:
        raise ValidationError(
            "Battery capacity cannot exceed 10000 Wh. Expected: 0-10000 Wh (e.g., 500, 750)"
        )

    return capacity


def validate_target_range_soc(min_soc, max_soc):
    """
    Validate target-range State of Charge (min/max percentages).

    Rules:
    - Both must be integers between 0 and 100
    - min_soc must be less than max_soc

    Args:
        min_soc (int or str): Minimum SoC percentage
        max_soc (int or str): Maximum SoC percentage

    Returns:
        tuple: (min_soc, max_soc) as integers

    Raises:
        ValidationError: If SoC range is invalid
    """
    # Convert strings to int if needed
    if isinstance(min_soc, str):
        try:
            min_soc = int(min_soc.strip())
        except ValueError:
            raise ValidationError(
                "Minimum SoC must be a number. Expected: 0-100 (e.g., 20)"
            )

    if isinstance(max_soc, str):
        try:
            max_soc = int(max_soc.strip())
        except ValueError:
            raise ValidationError(
                "Maximum SoC must be a number. Expected: 0-100 (e.g., 80)"
            )

    if not isinstance(min_soc, int):
        raise ValidationError(
            "Minimum SoC must be an integer. Expected: 0-100 (e.g., 20)"
        )

    if not isinstance(max_soc, int):
        raise ValidationError(
            "Maximum SoC must be an integer. Expected: 0-100 (e.g., 80)"
        )

    if min_soc < 0:
        raise ValidationError(
            "Minimum SoC cannot be negative. Expected: 0-100 (e.g., 20)"
        )
    if min_soc > 100:
        raise ValidationError(
            "Minimum SoC cannot exceed 100. Expected: 0-100 (e.g., 20)"
        )

    if max_soc < 0:
        raise ValidationError(
            "Maximum SoC cannot be negative. Expected: 0-100 (e.g., 80)"
        )
    if max_soc > 100:
        raise ValidationError(
            "Maximum SoC cannot exceed 100. Expected: 0-100 (e.g., 80)"
        )

    if min_soc >= max_soc:
        raise ValidationError(
            "Minimum SoC must be less than Maximum SoC. Expected: min < max (e.g., min=20, max=80)"
        )

    return min_soc, max_soc


def validate_out_of_service_status(status):
    """
    Validate out-of-service status.

    Accepts:
    - Boolean: True/False
    - String: "Yes"/"No", "yes"/"no", "True"/"False", "1"/"0"
    - Integer: 1/0

    Returns: Boolean (True = out of service, False = in service)

    Args:
        status (bool, str, or int): Out-of-service status

    Returns:
        bool: True if out of service, False if in service

    Raises:
        ValidationError: If status is invalid
    """
    if isinstance(status, bool):
        return status

    _check_null_bytes(status, "Status")
    if isinstance(status, str):
        status = status.strip().lower()
        if status in ["yes", "true", "1"]:
            return True
        if status in ["no", "false", "0"]:
            return False
        raise ValidationError(
            "Invalid out-of-service status. Expected: Yes/No, True/False, 1/0 (e.g., Yes, No)"
        )

    if isinstance(status, int):
        if status == 1:
            return True
        if status == 0:
            return False
        raise ValidationError(
            "Invalid out-of-service status. Expected: 1 (out of service) or 0 (in service)"
        )

    raise ValidationError(
        "Out-of-service status must be boolean, string, or integer. Expected: Yes/No, True/False, 1/0"
    )


def validate_mileage(mileage):
    """
    Validate scooter mileage in kilometres.

    Rules:
    - Must be number between 0 and 999999 km (6 figures max)
    - Can be integer or float

    Args:
        mileage (int, float, or str): Mileage to validate

    Returns:
        float: Validated mileage

    Raises:
        ValidationError: If mileage is invalid
    """
    # Convert string to float if needed
    if isinstance(mileage, str):
        try:
            mileage = float(mileage.strip())
        except ValueError:
            raise ValidationError(
                "Mileage must be a number. Expected: 0-999999 km (e.g., 1500, 2500.5)"
            )

    if not isinstance(mileage, (int, float)):
        raise ValidationError(
            "Mileage must be a number. Expected: 0-999999 km (e.g., 1500, 2500.5)"
        )

    if mileage < 0:
        raise ValidationError(
            "Mileage cannot be negative. Expected: 0-999999 km (e.g., 1500, 2500.5)"
        )
    if mileage > 999999:
        raise ValidationError(
            "Mileage cannot exceed 999999 km (6 figures). Expected: 0-999999 km (e.g., 1500)"
        )

    return float(mileage)
