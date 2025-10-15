import secrets
import string
from database import (
    get_connection,
    encrypt_username,
    decrypt_username,
    hash_password,
)
from validation import validate_username, validate_name, ValidationError
from auth import get_current_user, check_permission, get_role_name
from logging import log_activity


def create_system_admin(username, first_name, last_name, password=None):
    """
    Create new System Administrator account (Super Admin only).

    Validates all inputs, uses prepared statements, hashes password with
    SHA-256 + salt, encrypts username in database, and logs activity.

    Args:
        username (str): Username (8-10 chars)
        first_name (str): First name
        last_name (str): Last name
        password (str): Password (optional, generates temporary if not provided)

    Returns:
        tuple: (success: bool, message: str, temp_password: str or None)

    Example:
        success, msg, temp_pw = create_system_admin("admin_001", "John", "Doe")
        if success:
            print(f"Created! Temporary password: {temp_pw}")
    """
    # Check permission (Super Admin only)
    if not check_permission("manage_admins"):
        return (
            False,
            "Access denied. Only Super Administrator can create System Admins",
            None,
        )

    current_user = get_current_user()

    # Validate inputs
    try:
        username = validate_username(username)
        first_name = validate_name(first_name, "First name")
        last_name = validate_name(last_name, "Last name")
    except ValidationError as e:
        return False, f"Validation error: {e}", None

    # Generate temporary password if not provided
    temp_password = None
    if password is None:
        temp_password = _generate_temporary_password()
        password = temp_password

    # Check if username already exists
    conn = get_connection()
    cursor = conn.cursor()

    encrypted_username = encrypt_username(username)

    # Prepared statement to prevent SQL injection
    cursor.execute("SELECT id FROM users WHERE username = ?", (encrypted_username,))

    if cursor.fetchone():
        conn.close()
        return False, f"Username '{username}' already exists", None

    # Hash password with SHA-256 + salt
    password_hash = hash_password(password, username)

    # Prepared statement for INSERT
    cursor.execute(
        """
        INSERT INTO users (username, password_hash, role, first_name, last_name)
        VALUES (?, ?, ?, ?, ?)
        """,
        (encrypted_username, password_hash, "system_admin", first_name, last_name),
    )

    conn.commit()
    conn.close()

    # Log activity
    log_activity(
        current_user["username"],
        "New system admin created",
        f"username: {username}, name: {first_name} {last_name}",
    )

    if temp_password:
        return (
            True,
            f"System Administrator '{username}' created successfully",
            temp_password,
        )
    else:
        return True, f"System Administrator '{username}' created successfully", None


def create_service_engineer(username, first_name, last_name, password=None):
    """
    Create new Service Engineer account (Super Admin or System Admin).

    Validates all inputs, uses prepared statements, hashes password with
    SHA-256 + salt, encrypts username in database, and logs activity.

    Args:
        username (str): Username (8-10 chars)
        first_name (str): First name
        last_name (str): Last name
        password (str): Password (optional, generates temporary if not provided)

    Returns:
        tuple: (success: bool, message: str, temp_password: str or None)

    Example:
        success, msg, temp_pw = create_service_engineer("engineer1", "Jane", "Smith")
    """
    # Check permission (Super Admin or System Admin)
    if not check_permission("manage_engineers"):
        return (
            False,
            "Access denied. Insufficient permissions to create Service Engineers",
            None,
        )

    current_user = get_current_user()

    # Validate inputs
    try:
        username = validate_username(username)
        first_name = validate_name(first_name, "First name")
        last_name = validate_name(last_name, "Last name")
    except ValidationError as e:
        return False, f"Validation error: {e}", None

    # Generate temporary password if not provided
    temp_password = None
    if password is None:
        temp_password = _generate_temporary_password()
        password = temp_password

    # Check if username already exists
    conn = get_connection()
    cursor = conn.cursor()

    encrypted_username = encrypt_username(username)

    # Prepared statement
    cursor.execute("SELECT id FROM users WHERE username = ?", (encrypted_username,))

    if cursor.fetchone():
        conn.close()
        return False, f"Username '{username}' already exists", None

    # Hash password
    password_hash = hash_password(password, username)

    # Prepared statement for INSERT
    cursor.execute(
        """
        INSERT INTO users (username, password_hash, role, first_name, last_name)
        VALUES (?, ?, ?, ?, ?)
        """,
        (encrypted_username, password_hash, "service_engineer", first_name, last_name),
    )

    conn.commit()
    conn.close()

    # Log activity
    log_activity(
        current_user["username"],
        "New service engineer created",
        f"username: {username}, name: {first_name} {last_name}",
    )

    if temp_password:
        return (
            True,
            f"Service Engineer '{username}' created successfully",
            temp_password,
        )
    else:
        return True, f"Service Engineer '{username}' created successfully", None


def delete_user(username):
    """
    Delete user account (role-based permissions).

    Super Admin can delete System Admins and Service Engineers.
    System Admin can delete Service Engineers only.
    Uses prepared statements and logs activity.

    Args:
        username (str): Username to delete

    Returns:
        tuple: (success: bool, message: str)

    Example:
        success, msg = delete_user("old_admin")
    """
    current_user = get_current_user()

    if not current_user:
        return False, "You must be logged in to delete users"

    # Validate username
    try:
        username = validate_username(username)
    except ValidationError as e:
        return False, f"Invalid username: {e}"

    # Cannot delete super_admin
    if username.lower() == "super_admin":
        return False, "Cannot delete Super Administrator account"

    # Cannot delete yourself
    if username.lower() == current_user["username"].lower():
        return False, "Cannot delete your own account"

    # Get target user info
    conn = get_connection()
    cursor = conn.cursor()

    encrypted_username = encrypt_username(username)

    # Prepared statement
    cursor.execute(
        "SELECT id, role, first_name, last_name FROM users WHERE username = ?",
        (encrypted_username,),
    )

    user = cursor.fetchone()

    if not user:
        conn.close()
        return False, f"User '{username}' not found"

    user_id, target_role, first_name, last_name = user

    # Permission check
    if target_role == "system_admin":
        # Only Super Admin can delete System Admins
        if not check_permission("manage_admins"):
            conn.close()
            return (
                False,
                "Access denied. Only Super Administrator can delete System Admins",
            )
    elif target_role == "service_engineer":
        # Super Admin or System Admin can delete Service Engineers
        if not check_permission("manage_engineers"):
            conn.close()
            return (
                False,
                "Access denied. Insufficient permissions to delete Service Engineers",
            )

    # Prepared statement for DELETE
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

    conn.commit()
    conn.close()

    # Log activity
    log_activity(
        current_user["username"],
        "User deleted",
        f"User '{username}' ({get_role_name(target_role)}) deleted",
    )

    return True, f"User '{username}' deleted successfully"


def reset_user_password(username):
    """
    Reset user password to temporary password.

    Super Admin can reset System Admin and Service Engineer passwords.
    System Admin can reset Service Engineer passwords only.
    Generates secure temporary password, uses prepared statements, and logs activity.

    Args:
        username (str): Username to reset password for

    Returns:
        tuple: (success: bool, message: str, temp_password: str or None)

    Example:
        success, msg, temp_pw = reset_user_password("admin_001")
        if success:
            print(f"New temporary password: {temp_pw}")
    """
    current_user = get_current_user()

    if not current_user:
        return False, "You must be logged in to reset passwords", None

    # Validate username
    try:
        username = validate_username(username)
    except ValidationError as e:
        return False, f"Invalid username: {e}", None

    # Cannot reset super_admin password
    if username.lower() == "super_admin":
        return False, "Cannot reset Super Administrator password (hardcoded)", None

    # Get target user info
    conn = get_connection()
    cursor = conn.cursor()

    encrypted_username = encrypt_username(username)

    # Prepared statement
    cursor.execute(
        "SELECT id, role FROM users WHERE username = ?", (encrypted_username,)
    )

    user = cursor.fetchone()

    if not user:
        conn.close()
        return False, f"User '{username}' not found", None

    user_id, target_role = user

    # Permission check
    if target_role == "system_admin":
        # Only Super Admin can reset System Admin passwords
        if not check_permission("manage_admins"):
            conn.close()
            return (
                False,
                "Access denied. Only Super Administrator can reset System Admin passwords",
                None,
            )
    elif target_role == "service_engineer":
        # Super Admin or System Admin can reset Service Engineer passwords
        if not check_permission("manage_engineers"):
            conn.close()
            return (
                False,
                "Access denied. Insufficient permissions to reset Service Engineer passwords",
                None,
            )

    # Generate temporary password (secure random)
    temp_password = _generate_temporary_password()

    # Hash new password (SHA-256 + salt)
    new_password_hash = hash_password(temp_password, username)

    # Prepared statement for UPDATE
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, user_id)
    )

    conn.commit()
    conn.close()

    # Log activity
    log_activity(
        current_user["username"],
        "Password reset",
        f"For user: {username} ({get_role_name(target_role)})",
    )

    return True, f"Password reset successfully for '{username}'", temp_password


def update_user_profile(username, first_name=None, last_name=None):
    """
    Update user profile (first name, last name).

    Super Admin can update any System Admin profile.
    System Admin can update Service Engineer profiles.
    Validates inputs, uses prepared statements, and logs activity.

    Args:
        username (str): Username to update
        first_name (str): New first name (optional)
        last_name (str): New last name (optional)

    Returns:
        tuple: (success: bool, message: str)

    Example:
        success, msg = update_user_profile("admin_001", first_name="Johnny")
    """
    current_user = get_current_user()

    if not current_user:
        return False, "You must be logged in to update user profiles"

    # Must update at least one field
    if first_name is None and last_name is None:
        return False, "Must specify at least first_name or last_name to update"

    # Validate username
    try:
        username = validate_username(username)
    except ValidationError as e:
        return False, f"Invalid username: {e}"

    # Validate new names
    try:
        if first_name is not None:
            first_name = validate_name(first_name, "First name")
        if last_name is not None:
            last_name = validate_name(last_name, "Last name")
    except ValidationError as e:
        return False, f"Validation error: {e}"

    # Get target user info
    conn = get_connection()
    cursor = conn.cursor()

    encrypted_username = encrypt_username(username)

    # Prepared statement
    cursor.execute(
        "SELECT id, role, first_name, last_name FROM users WHERE username = ?",
        (encrypted_username,),
    )

    user = cursor.fetchone()

    if not user:
        conn.close()
        return False, f"User '{username}' not found"

    user_id, target_role, old_first_name, old_last_name = user

    # Permission check
    if target_role == "system_admin":
        if not check_permission("manage_admins"):
            conn.close()
            return (
                False,
                "Access denied. Only Super Administrator can update System Admin profiles",
            )
    elif target_role == "service_engineer":
        if not check_permission("manage_engineers"):
            conn.close()
            return (
                False,
                "Access denied. Insufficient permissions to update Service Engineer profiles",
            )

    # Build update query dynamically (still using prepared statements)
    update_fields = []
    params = []

    if first_name is not None:
        update_fields.append("first_name = ?")
        params.append(first_name)

    if last_name is not None:
        update_fields.append("last_name = ?")
        params.append(last_name)

    params.append(user_id)

    # Prepared statement for UPDATE
    cursor.execute(
        f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?", tuple(params)
    )

    conn.commit()
    conn.close()

    # Log activity
    changes = []
    if first_name is not None:
        changes.append(f"first_name: '{old_first_name}' → '{first_name}'")
    if last_name is not None:
        changes.append(f"last_name: '{old_last_name}' → '{last_name}'")

    log_activity(
        current_user["username"],
        "User profile updated",
        f"User: {username}, Changes: {', '.join(changes)}",
    )

    return True, f"Profile updated successfully for '{username}'"


def _generate_temporary_password():
    """
    Generate secure temporary password.

    Requirements (matches validate_password):
    - 12 characters
    - Includes uppercase, lowercase, digits, special characters

    Returns:
        str: Temporary password

    Example:
        temp_pw = _generate_temporary_password()
        # Returns something like: "Temp@1234Abc"
    """
    # Ensure all character types are included
    password_chars = [
        secrets.choice(string.ascii_uppercase),  # Uppercase
        secrets.choice(string.ascii_lowercase),  # Lowercase
        secrets.choice(string.digits),  # Digit
        secrets.choice("~!@#$%&_-+="),  # Special character
    ]

    # Fill remaining 8 characters randomly
    all_chars = string.ascii_letters + string.digits + "~!@#$%&_-+="
    password_chars.extend(secrets.choice(all_chars) for _ in range(8))

    # Shuffle to avoid predictable pattern
    password_list = list(password_chars)
    secrets.SystemRandom().shuffle(password_list)

    return "".join(password_list)


def list_all_users():
    """
    Display all users with their roles (Admin view).

    Returns:
        list: List of user dictionaries

    Example:
        users = list_all_users()
        for user in users:
            print(f"{user['username']} - {user['role_name']}")
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Proper SQL query
    cursor.execute(
        """
        SELECT username, role, first_name, last_name, created_at
        FROM users
        ORDER BY created_at DESC
        """
    )

    results = cursor.fetchall()
    conn.close()

    users = []
    for row in results:
        enc_username, role, first_name, last_name, created_at = row
        users.append(
            {
                "username": decrypt_username(enc_username),
                "role": role,
                "role_name": get_role_name(role),
                "first_name": first_name,
                "last_name": last_name,
                "created_at": created_at,
            }
        )

    return users


# Testing and demonstration
if __name__ == "__main__":
    from auth import login, logout

    print("=" * 60)
    print("USER MANAGEMENT SYSTEM TESTING")
    print("=" * 60)

    # Login as super admin
    print("\n--- Logging in as Super Admin ---")
    login("super_admin", "Admin_123?")

    # Test 1: Create System Admin
    print("\n--- Test 1: Create System Administrator ---")
    success, msg, temp_pw = create_system_admin("admin_001", "John", "Admin")
    print(f"Result: {success}")
    print(f"Message: {msg}")
    if temp_pw:
        print(f"Temporary password: {temp_pw}")

    # Test 2: Create Service Engineer
    print("\n--- Test 2: Create Service Engineer ---")
    success, msg, temp_pw = create_service_engineer("engineer1", "Jane", "Engineer")
    print(f"Result: {success}")
    print(f"Message: {msg}")
    if temp_pw:
        print(f"Temporary password: {temp_pw}")

    # Test 3: List all users
    print("\n--- Test 3: List All Users ---")
    users = list_all_users()
    for user in users:
        print(
            f"  {user['username']:15s} | {user['role_name']:25s} | {user['first_name']} {user['last_name']}"
        )

    # Test 4: Reset password
    print("\n--- Test 4: Reset User Password ---")
    success, msg, temp_pw = reset_user_password("admin_001")
    print(f"Result: {success}")
    print(f"Message: {msg}")
    if temp_pw:
        print(f"New temporary password: {temp_pw}")

    # Test 5: Update profile
    print("\n--- Test 5: Update User Profile ---")
    success, msg = update_user_profile("engineer1", first_name="Janet")
    print(f"Result: {success}")
    print(f"Message: {msg}")

    # Test 6: Delete user
    print("\n--- Test 6: Delete User ---")
    success, msg = delete_user("engineer1")
    print(f"Result: {success}")
    print(f"Message: {msg}")

    # Test 7: Try to delete super_admin (should fail)
    print("\n--- Test 7: Try Delete Super Admin (Should Fail) ---")
    success, msg = delete_user("super_admin")
    print(f"Result: {success}")
    print(f"Message: {msg}")

    # Show logs
    print("\n--- Activity Logs ---")
    from logging import get_all_logs, display_logs

    logs = get_all_logs()
    display_logs(logs[-10:])  # Last 10 logs

    logout()

    print("\n" + "=" * 60)
    print("✓ User management system ready!")
    print("=" * 60)
