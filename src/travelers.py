import uuid
from database import get_connection, encrypt_field, decrypt_field
from validation import (
    validate_name,
    validate_date,
    validate_gender,
    validate_house_number,
    validate_zipcode,
    validate_city,
    validate_email,
    validate_phone,
    validate_driving_license,
    ValidationError,
)
from auth import get_current_user, check_permission
from logging import log_activity


def add_traveler(
    first_name,
    last_name,
    birthday,
    gender,
    street_name,
    house_number,
    zip_code,
    city,
    email,
    mobile_phone,
    driving_license,
):
    """
    Create new traveler record.

    Validates all inputs, encrypts sensitive fields (email, phone, license),
    uses prepared statements, and logs activity.

    Args:
        first_name (str): First name
        last_name (str): Last name
        birthday (str): Birthday (DD-MM-YYYY)
        gender (str): Gender (Male/Female)
        street_name (str): Street name
        house_number (str): House number
        zip_code (str): Zip code (DDDDXX)
        city (str): City
        email (str): Email address
        mobile_phone (str): Mobile phone (8 digits)
        driving_license (str): Driving license (XDDDDDDD)

    Returns:
        tuple: (success: bool, message: str, customer_id: str or None)

    Example:
        success, msg, cid = add_traveler("John", "Doe", "15-03-1990", "Male", ...)
    """
    # Check permission
    if not check_permission("manage_travelers"):
        return False, "Access denied. Insufficient permissions to add travelers", None

    current_user = get_current_user()

    # Validate all inputs
    try:
        first_name = validate_name(first_name, "First name")
        last_name = validate_name(last_name, "Last name")
        birthday = validate_date(birthday, "Birthday")
        gender = validate_gender(gender)
        street_name = validate_name(street_name, "Street name")
        house_number = validate_house_number(house_number)
        zip_code = validate_zipcode(zip_code)
        city = validate_city(city)
        email = validate_email(email)
        mobile_phone = validate_phone(mobile_phone)
        driving_license = validate_driving_license(driving_license)
    except ValidationError as e:
        return False, f"Validation error: {e}", None

    # Generate unique customer ID
    customer_id = str(uuid.uuid4().int)[:10]

    # Encrypt sensitive fields
    encrypted_email = encrypt_field(email)
    encrypted_phone = encrypt_field(mobile_phone)
    encrypted_license = encrypt_field(driving_license)

    # Insert into database
    conn = get_connection()
    cursor = conn.cursor()

    # Prepared statement to prevent SQL injection
    cursor.execute(
        """
        INSERT INTO travelers (
            customer_id, first_name, last_name, birthday, gender,
            street_name, house_number, zip_code, city,
            email, mobile_phone, driving_license
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            customer_id,
            first_name,
            last_name,
            birthday,
            gender,
            street_name,
            house_number,
            zip_code,
            city,
            encrypted_email,
            encrypted_phone,
            encrypted_license,
        ),
    )

    conn.commit()
    conn.close()

    # Log activity
    log_activity(
        current_user["username"],
        "New traveler added",
        f"Customer ID: {customer_id}, Name: {first_name} {last_name}",
    )

    return True, f"Traveler '{first_name} {last_name}' added successfully", customer_id


def update_traveler(customer_id, **updates):
    """
    Update traveler information.

    Validates inputs, encrypts sensitive fields if updated,
    uses prepared statements, and logs activity.

    Args:
        customer_id (str): Customer ID
        **updates: Fields to update (first_name, last_name, email, etc.)

    Returns:
        tuple: (success: bool, message: str)

    Example:
        success, msg = update_traveler("1234567890", email="new@email.com")
    """
    # Check permission
    if not check_permission("manage_travelers"):
        return False, "Access denied. Insufficient permissions to update travelers"

    current_user = get_current_user()

    if not updates:
        return False, "No fields specified for update"

    # Get current traveler data
    conn = get_connection()
    cursor = conn.cursor()

    # Prepared statement
    cursor.execute("SELECT * FROM travelers WHERE customer_id = ?", (customer_id,))

    traveler = cursor.fetchone()

    if not traveler:
        conn.close()
        return False, f"Traveler with customer ID '{customer_id}' not found"

    # Validate and prepare updates
    update_fields = []
    params = []
    changes = []

    allowed_fields = {
        "first_name",
        "last_name",
        "birthday",
        "gender",
        "street_name",
        "house_number",
        "zip_code",
        "city",
        "email",
        "mobile_phone",
        "driving_license",
    }

    for field, value in updates.items():
        if field not in allowed_fields:
            conn.close()
            return False, f"Invalid field: {field}"

        try:
            # Validate based on field type
            if field in ["first_name", "last_name"]:
                value = validate_name(value, field.replace("_", " ").title())
            elif field == "birthday":
                value = validate_date(value, "Birthday")
            elif field == "gender":
                value = validate_gender(value)
            elif field == "street_name":
                value = validate_name(value, "Street name")
            elif field == "house_number":
                value = validate_house_number(value)
            elif field == "zip_code":
                value = validate_zipcode(value)
            elif field == "city":
                value = validate_city(value)
            elif field == "email":
                value = validate_email(value)
                value = encrypt_field(value)
            elif field == "mobile_phone":
                value = validate_phone(value)
                value = encrypt_field(value)
            elif field == "driving_license":
                value = validate_driving_license(value)
                value = encrypt_field(value)
        except ValidationError as e:
            conn.close()
            return False, f"Validation error for {field}: {e}"

        update_fields.append(f"{field} = ?")
        params.append(value)
        changes.append(field)

    params.append(customer_id)

    # Prepared statement for UPDATE
    cursor.execute(
        f"UPDATE travelers SET {', '.join(update_fields)} WHERE customer_id = ?",
        tuple(params),
    )

    conn.commit()
    conn.close()

    # Log activity
    log_activity(
        current_user["username"],
        "Traveler updated",
        f"Customer ID: {customer_id}, Updated fields: {', '.join(changes)}",
    )

    return True, f"Traveler updated successfully"


def delete_traveler(customer_id):
    """
    Delete traveler record.

    Uses prepared statements and logs activity.

    Args:
        customer_id (str): Customer ID to delete

    Returns:
        tuple: (success: bool, message: str)

    Example:
        success, msg = delete_traveler("1234567890")
    """
    # Check permission
    if not check_permission("manage_travelers"):
        return False, "Access denied. Insufficient permissions to delete travelers"

    current_user = get_current_user()

    # Check if traveler exists
    conn = get_connection()
    cursor = conn.cursor()

    # Prepared statement
    cursor.execute(
        "SELECT first_name, last_name FROM travelers WHERE customer_id = ?",
        (customer_id,),
    )

    traveler = cursor.fetchone()

    if not traveler:
        conn.close()
        return False, f"Traveler with customer ID '{customer_id}' not found"

    first_name, last_name = traveler

    # Prepared statement for DELETE
    cursor.execute("DELETE FROM travelers WHERE customer_id = ?", (customer_id,))

    conn.commit()
    conn.close()

    # Log activity
    log_activity(
        current_user["username"],
        "Traveler deleted",
        f"Customer ID: {customer_id}, Name: {first_name} {last_name}",
    )

    return True, f"Traveler '{first_name} {last_name}' deleted successfully"


def search_travelers(search_key):
    """
    Search travelers with partial key matching.

    Accepts partial keys in: customer_id, first_name, last_name.

    Args:
        search_key (str): Search term (e.g., "mik", "omso", "2328")

    Returns:
        list: Matching traveler dictionaries

    Example:
        results = search_travelers("john")
        # Finds: "John", "Johnny", etc.
    """
    if not search_key or len(search_key) < 2:
        return []

    conn = get_connection()
    cursor = conn.cursor()

    # Prepared statement with LIKE for partial matching
    search_pattern = f"%{search_key}%"

    cursor.execute(
        """
        SELECT * FROM travelers
        WHERE customer_id LIKE ?
           OR LOWER(first_name) LIKE LOWER(?)
           OR LOWER(last_name) LIKE LOWER(?)
        ORDER BY first_name, last_name
        """,
        (search_pattern, search_pattern, search_pattern),
    )

    results = cursor.fetchall()
    conn.close()

    travelers = []
    for row in results:
        travelers.append(
            {
                "id": row[0],
                "customer_id": row[1],
                "first_name": row[2],
                "last_name": row[3],
                "birthday": row[4],
                "gender": row[5],
                "street_name": row[6],
                "house_number": row[7],
                "zip_code": row[8],
                "city": row[9],
                "email": decrypt_field(row[10]),
                "mobile_phone": decrypt_field(row[11]),
                "driving_license": decrypt_field(row[12]),
                "registration_date": row[13],
            }
        )

    return travelers


def get_traveler_by_id(customer_id):
    """
    Get specific traveler by customer ID.

    Args:
        customer_id (str): Customer ID

    Returns:
        dict: Traveler information or None if not found

    Example:
        traveler = get_traveler_by_id("1234567890")
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Prepared statement
    cursor.execute("SELECT * FROM travelers WHERE customer_id = ?", (customer_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "customer_id": row[1],
        "first_name": row[2],
        "last_name": row[3],
        "birthday": row[4],
        "gender": row[5],
        "street_name": row[6],
        "house_number": row[7],
        "zip_code": row[8],
        "city": row[9],
        "email": decrypt_field(row[10]),
        "mobile_phone": decrypt_field(row[11]),
        "driving_license": decrypt_field(row[12]),
        "registration_date": row[13],
    }


def list_all_travelers():
    """
    Get all travelers.

    Returns:
        list: List of traveler dictionaries

    Example:
        travelers = list_all_travelers()
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM travelers ORDER BY first_name, last_name")

    results = cursor.fetchall()
    conn.close()

    travelers = []
    for row in results:
        travelers.append(
            {
                "id": row[0],
                "customer_id": row[1],
                "first_name": row[2],
                "last_name": row[3],
                "birthday": row[4],
                "gender": row[5],
                "street_name": row[6],
                "house_number": row[7],
                "zip_code": row[8],
                "city": row[9],
                "email": decrypt_field(row[10]),
                "mobile_phone": decrypt_field(row[11]),
                "driving_license": decrypt_field(row[12]),
                "registration_date": row[13],
            }
        )

    return travelers


# Testing and demonstration
if __name__ == "__main__":
    from auth import login, logout

    print("=" * 60)
    print("TRAVELER MANAGEMENT SYSTEM TESTING")
    print("=" * 60)

    # Login as super admin
    print("\n--- Logging in as Super Admin ---")
    login("super_admin", "Admin_123?")

    # Test 1: Add traveler
    print("\n--- Test 1: Add Traveler ---")
    success, msg, cid = add_traveler(
        first_name="John",
        last_name="Doe",
        birthday="15-03-1990",
        gender="Male",
        street_name="Main Street",
        house_number="42",
        zip_code="3011AB",
        city="Amsterdam",
        email="john.doe@example.com",
        mobile_phone="12345678",
        driving_license="AB1234567",
    )
    print(f"Result: {success}")
    print(f"Message: {msg}")
    print(f"Customer ID: {cid}")

    # Test 2: Add another traveler
    print("\n--- Test 2: Add Another Traveler ---")
    success, msg, cid2 = add_traveler(
        first_name="Jane",
        last_name="Smith",
        birthday="22-07-1985",
        gender="Female",
        street_name="Park Avenue",
        house_number="123",
        zip_code="1012AB",
        city="Rotterdam",
        email="jane.smith@example.com",
        mobile_phone="87654321",
        driving_license="XY7654321",
    )
    print(f"Result: {success}")
    print(f"Message: {msg}")

    # Test 3: List all travelers
    print("\n--- Test 3: List All Travelers ---")
    travelers = list_all_travelers()
    for t in travelers:
        print(
            f"  {t['customer_id']:12s} | {t['first_name']:10s} {t['last_name']:10s} | {t['email']:25s}"
        )

    # Test 4: Search travelers
    print("\n--- Test 4: Search Travelers (partial key: 'john') ---")
    results = search_travelers("john")
    print(f"Found {len(results)} travelers:")
    for t in results:
        print(f"  {t['customer_id']:12s} | {t['first_name']} {t['last_name']}")

    # Test 5: Update traveler
    print("\n--- Test 5: Update Traveler ---")
    success, msg = update_traveler(cid, email="john.updated@example.com")
    print(f"Result: {success}")
    print(f"Message: {msg}")

    # Test 6: Get specific traveler
    print("\n--- Test 6: Get Traveler By ID ---")
    traveler = get_traveler_by_id(cid)
    if traveler:
        print(f"  Name: {traveler['first_name']} {traveler['last_name']}")
        print(f"  Email: {traveler['email']}")
        print(f"  Phone: {traveler['mobile_phone']}")

    # Test 7: Delete traveler
    print("\n--- Test 7: Delete Traveler ---")
    success, msg = delete_traveler(cid2)
    print(f"Result: {success}")
    print(f"Message: {msg}")

    # Show logs
    print("\n--- Activity Logs ---")
    from logging import get_all_logs, display_logs

    logs = get_all_logs()
    display_logs(logs[-8:])

    logout()

    print("\n" + "=" * 60)
    print("✓ Traveler management system ready!")
    print("=" * 60)
