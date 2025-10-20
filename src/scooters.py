# ═══════════════════════════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════════════════════════
# Description: Scooter fleet management imports
#
# External modules: database, validation, auth, activity_log
# ═══════════════════════════════════════════════════════════════════════════

from database import get_connection, encrypt_username, decrypt_username
from validation import (
    ValidationError,
    validate_serial_number,
    validate_scooter_type,
    validate_battery_level,
    validate_location,
)
from auth import get_current_user, check_permission
from activity_log import log_activity


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: CREATE OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════
# Description: Add new scooters to fleet inventory
#
# Key components:
# - add_scooter(): Create new scooter record with validation and encryption
# ═══════════════════════════════════════════════════════════════════════════


def add_scooter(serial_number, scooter_type, battery_level, status, location):
    """
    Create new scooter record.

    Validates inputs using validation.py functions, encrypts serial number,
    uses prepared statements, and logs activity.

    Args:
        serial_number (str): Serial number (will be encrypted)
        scooter_type (str): Scooter type/model
        battery_level (int): Battery level (0-100)
        status (str): Status (available/in_use/maintenance)
        location (str): Current location

    Returns:
        tuple: (success: bool, message: str)

    Example:
        success, msg = add_scooter("SC123456", "Model X", 100, "available", "Amsterdam Central")
    """
    # Check permission
    if not check_permission("manage_scooters"):
        return False, "Access denied. Insufficient permissions to add scooters"

    current_user = get_current_user()

    # Validate inputs using validation.py functions
    try:
        # Validate serial number with proper format and length checks
        serial_number = validate_serial_number(serial_number)

        # Validate scooter type
        scooter_type = validate_scooter_type(scooter_type)

        # Validate battery level (handles int conversion and range)
        battery_level = validate_battery_level(battery_level)

        # Validate location
        location = validate_location(location)

        # Validate status (enum validation)
        valid_statuses = ["available", "in_use", "maintenance"]
        if status not in valid_statuses:
            raise ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")

    except ValidationError as e:
        return False, f"Validation error: {e}"

    encrypted_serial = encrypt_username(serial_number)

    # Check if serial number already exists
    conn = get_connection()
    cursor = conn.cursor()

    # Prepared statement
    cursor.execute(
        "SELECT id FROM scooters WHERE serial_number = ?", (encrypted_serial,)
    )

    if cursor.fetchone():
        conn.close()
        return False, f"Scooter with serial number '{serial_number}' already exists"

    # Prepared statement for INSERT
    cursor.execute(
        """
        INSERT INTO scooters (
            serial_number, type, battery_level, status, location
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (encrypted_serial, scooter_type, battery_level, status, location),
    )

    conn.commit()
    conn.close()

    # Log activity
    if current_user:
        log_activity(
            current_user["username"],
            "New scooter added",
            f"Serial: {serial_number}, Type: {scooter_type}",
        )

    return True, f"Scooter '{serial_number}' added successfully"


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: UPDATE OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════
# Description: Update scooter information with role-based field restrictions
#
# Key components:
# - update_scooter(): Update with role-based permissions (Service Engineers limited)
#
# Note: Service Engineers can only update battery, status, location, service date
# ═══════════════════════════════════════════════════════════════════════════


def update_scooter(serial_number, **updates):
    """
    Update scooter information with role-based field restrictions.

    Service Engineers can ONLY update:
    - battery_level (State of Charge)
    - status (Out-of-Service Status)
    - location
    - last_service_date (Last Maintenance Date)

    Super Admin / System Admin can update ALL fields.

    Args:
        serial_number (str): Serial number
        **updates: Fields to update

    Returns:
        tuple: (success: bool, message: str)

    Example:
        success, msg = update_scooter("SC123456", battery_level=85, location="Rotterdam")
    """
    # Check permission
    if not check_permission("manage_scooters"):
        return False, "Access denied. Insufficient permissions to update scooters"

    current_user = get_current_user()

    if not updates:
        return False, "No fields specified for update"

    # Define allowed fields per role
    service_engineer_fields = {
        "battery_level",
        "status",
        "location",
        "last_service_date",
    }
    all_fields = {
        "type",
        "battery_level",
        "status",
        "location",
        "last_service_date",
    }

    # Check field permissions based on role
    user_role = None
    if current_user:
        user_role = current_user["role"]
        if user_role == "service_engineer":
            allowed_fields = service_engineer_fields
        else:
            allowed_fields = all_fields
    else:
        allowed_fields = all_fields

    # Validate requested fields against permissions
    for field in updates.keys():
        if field not in allowed_fields:
            if user_role == "service_engineer":
                return (
                    False,
                    f"Access denied. Service Engineers cannot update field: {field}",
                )
            else:
                return False, f"Invalid field: {field}"

    # Get current scooter
    conn = get_connection()
    cursor = conn.cursor()

    encrypted_serial = encrypt_username(serial_number)

    # Prepared statement
    cursor.execute(
        "SELECT * FROM scooters WHERE serial_number = ?", (encrypted_serial,)
    )

    scooter = cursor.fetchone()

    if not scooter:
        conn.close()
        return False, f"Scooter with serial number '{serial_number}' not found"

    # Validate and prepare updates
    update_fields = []
    params = []
    changes = []

    for field, value in updates.items():
        try:
            # Validate based on field type using validation.py functions (L03)
            if field == "battery_level":
                value = validate_battery_level(value)
            elif field == "status":
                valid_statuses = ["available", "in_use", "maintenance"]
                if value not in valid_statuses:
                    raise ValidationError(
                        f"Status must be one of: {', '.join(valid_statuses)}"
                    )
            elif field == "type":
                value = validate_scooter_type(value)
            elif field == "location":
                value = validate_location(value)
            elif field == "last_service_date":
                # Basic date validation (DD-MM-YYYY format)
                if not value or len(value) != 10:
                    raise ValidationError("Date must be in DD-MM-YYYY format")

        except ValidationError as e:
            conn.close()
            return False, f"Validation error for {field}: {e}"

        update_fields.append(f"{field} = ?")
        params.append(value)
        changes.append(field)

    params.append(encrypted_serial)

    # Prepared statement for UPDATE
    cursor.execute(
        f"UPDATE scooters SET {', '.join(update_fields)} WHERE serial_number = ?",
        tuple(params),
    )

    conn.commit()
    conn.close()

    # Log activity
    if current_user:
        log_activity(
            current_user["username"],
            "Scooter updated",
            f"Serial: {serial_number}, Updated fields: {', '.join(changes)}",
        )

    return True, f"Scooter updated successfully"


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: DELETE OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════
# Description: Delete scooter records
#
# Key components:
# - delete_scooter(): Remove scooter (Super/System Admin only, not engineers)
# ═══════════════════════════════════════════════════════════════════════════


def delete_scooter(serial_number):
    """
    Delete scooter record (Super Admin or System Admin only).

    Uses prepared statements and logs activity.

    Args:
        serial_number (str): Serial number to delete

    Returns:
        tuple: (success: bool, message: str)

    Example:
        success, msg = delete_scooter("SC123456")
    """
    # Check permission (Service Engineers cannot delete)
    current_user = get_current_user()

    if current_user and current_user["role"] == "service_engineer":
        return False, "Access denied. Service Engineers cannot delete scooters"

    if not check_permission("manage_scooters"):
        return False, "Access denied. Insufficient permissions to delete scooters"

    # Check if scooter exists
    conn = get_connection()
    cursor = conn.cursor()

    encrypted_serial = encrypt_username(serial_number)

    # Prepared statement
    cursor.execute(
        "SELECT type, location FROM scooters WHERE serial_number = ?",
        (encrypted_serial,),
    )

    scooter = cursor.fetchone()

    if not scooter:
        conn.close()
        return False, f"Scooter with serial number '{serial_number}' not found"

    scooter_type, location = scooter

    # Prepared statement for DELETE
    cursor.execute("DELETE FROM scooters WHERE serial_number = ?", (encrypted_serial,))

    conn.commit()
    conn.close()

    # Log activity
    if current_user:
        log_activity(
            current_user["username"],
            "Scooter deleted",
            f"Serial: {serial_number}, Type: {scooter_type}",
        )

    return True, f"Scooter '{serial_number}' deleted successfully"


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: SEARCH & RETRIEVAL OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════
# Description: Search and retrieve scooter information
#
# Key components:
# - search_scooters(): Partial key search in type, location, status
# - get_scooter_by_serial(): Get specific scooter by serial number
# - list_all_scooters(): Get all scooters with decrypted serial numbers
#
# Note: Cannot search by serial number (encrypted)
# ═══════════════════════════════════════════════════════════════════════════


def search_scooters(search_key):
    """
    Search scooters with partial key matching.

    Accepts partial keys in: type, location, status.
    Note: Cannot search by serial_number (encrypted).

    Args:
        search_key (str): Search term

    Returns:
        list: Matching scooter dictionaries

    Example:
        results = search_scooters("Model X")
    """
    if not search_key or len(search_key) < 2:
        return []

    conn = get_connection()
    cursor = conn.cursor()

    # Prepared statement with LIKE for partial matching
    search_pattern = f"%{search_key}%"

    cursor.execute(
        """
        SELECT * FROM scooters
        WHERE LOWER(type) LIKE LOWER(?)
           OR LOWER(location) LIKE LOWER(?)
           OR LOWER(status) LIKE LOWER(?)
        ORDER BY type, location
        """,
        (search_pattern, search_pattern, search_pattern),
    )

    results = cursor.fetchall()
    conn.close()

    scooters = []
    for row in results:
        scooters.append(
            {
                "id": row[0],
                "serial_number": decrypt_username(row[1]),
                "type": row[2],
                "battery_level": row[3],
                "status": row[4],
                "location": row[5],
                "last_service_date": row[6],
                "added_date": row[7],
            }
        )

    return scooters


def get_scooter_by_serial(serial_number):
    """
    Get specific scooter by serial number.

    Args:
        serial_number (str): Serial number

    Returns:
        dict: Scooter information or None if not found

    Example:
        scooter = get_scooter_by_serial("SC123456")
    """
    conn = get_connection()
    cursor = conn.cursor()

    encrypted_serial = encrypt_username(serial_number)

    # Prepared statement
    cursor.execute(
        "SELECT * FROM scooters WHERE serial_number = ?", (encrypted_serial,)
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "serial_number": decrypt_username(row[1]),
        "type": row[2],
        "battery_level": row[3],
        "status": row[4],
        "location": row[5],
        "last_service_date": row[6],
        "added_date": row[7],
    }


def list_all_scooters():
    """
    Get all scooters.

    Returns:
        list: List of scooter dictionaries

    Example:
        scooters = list_all_scooters()
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM scooters ORDER BY type, location")

    results = cursor.fetchall()
    conn.close()

    scooters = []
    for row in results:
        scooters.append(
            {
                "id": row[0],
                "serial_number": decrypt_username(row[1]),
                "type": row[2],
                "battery_level": row[3],
                "status": row[4],
                "location": row[5],
                "last_service_date": row[6],
                "added_date": row[7],
            }
        )

    return scooters
