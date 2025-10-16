import os
import zipfile
import secrets
import string
from pathlib import Path
from datetime import datetime
from database import get_connection, encrypt_field, decrypt_field
from auth import get_current_user, check_permission
from logging import log_activity

# Backup directory
BACKUP_DIR = Path(__file__).parent / "backups"
DATA_DIR = Path(__file__).parent / "data"


def create_backup():
    """
    Create ZIP backup of database and encryption keys.

    Super Admin and System Admin can create backups.
    Uses prepared statements and logs activity.

    Returns:
        tuple: (success: bool, message: str, backup_filename: str or None)

    Example:
        success, msg, filename = create_backup()
        if success:
            print(f"Backup created: {filename}")
    """
    # Check permission
    if not check_permission("create_backup") and not check_permission("restore_backup"):
        return False, "Access denied. Insufficient permissions to create backup", None

    current_user = get_current_user()

    # Create backup directory if not exists
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.zip"
    backup_path = BACKUP_DIR / backup_filename

    try:
        # Create ZIP file
        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Add database
            db_path = DATA_DIR / "urban_mobility.db"
            if db_path.exists():
                zipf.write(db_path, "urban_mobility.db")

            # Add encryption keys
            aes_key_path = DATA_DIR / "aes_key.bin"
            if aes_key_path.exists():
                zipf.write(aes_key_path, "aes_key.bin")

            fernet_key_path = DATA_DIR / "fernet_key.bin"
            if fernet_key_path.exists():
                zipf.write(fernet_key_path, "fernet_key.bin")

            # Add logs
            log_path = DATA_DIR / "system.log"
            if log_path.exists():
                zipf.write(log_path, "system.log")

        # Log activity
        log_activity(
            current_user["username"],
            "Backup created",
            f"Filename: {backup_filename}",
        )

        return True, f"Backup created successfully: {backup_filename}", backup_filename

    except Exception as e:
        return False, f"Error creating backup: {e}", None


def restore_backup(backup_filename, restore_code=None):
    """
    Restore from ZIP backup with role-based access.

    Super Admin: Can restore any backup without code
    System Admin: Requires valid one-use restore code

    Uses prepared statements and logs activity.

    Args:
        backup_filename (str): Backup file to restore
        restore_code (str): Restore code (required for System Admin)

    Returns:
        tuple: (success: bool, message: str)

    Example:
        success, msg = restore_backup("backup_20251015_140000.zip")
    """
    current_user = get_current_user()

    if not current_user:
        return False, "You must be logged in to restore backup"

    # Check permission
    is_super_admin = check_permission("manage_restore_codes")
    is_system_admin = check_permission("restore_backup") and not is_super_admin

    if not is_super_admin and not is_system_admin:
        return False, "Access denied. Insufficient permissions to restore backup"

    # System Admin needs restore code
    if is_system_admin:
        if not restore_code:
            return (
                False,
                "System Administrators require a restore code to restore backups",
            )

        # Validate restore code
        code_valid, code_backup = _validate_restore_code(restore_code)

        if not code_valid:
            log_activity(
                current_user["username"],
                "Restore attempt failed",
                f"Invalid restore code used",
                suspicious=True,
            )
            return False, "Invalid or expired restore code"

        if code_backup != backup_filename:
            return (
                False,
                f"Restore code is valid for '{code_backup}', not '{backup_filename}'",
            )

    # Check if backup exists
    backup_path = BACKUP_DIR / backup_filename

    if not backup_path.exists():
        return False, f"Backup file '{backup_filename}' not found"

    try:
        # Extract ZIP file
        with zipfile.ZipFile(backup_path, "r") as zipf:
            # Restore database
            if "urban_mobility.db" in zipf.namelist():
                zipf.extract("urban_mobility.db", DATA_DIR)

            # Restore encryption keys
            if "aes_key.bin" in zipf.namelist():
                zipf.extract("aes_key.bin", DATA_DIR)

            if "fernet_key.bin" in zipf.namelist():
                zipf.extract("fernet_key.bin", DATA_DIR)

            # Restore logs
            if "system.log" in zipf.namelist():
                zipf.extract("system.log", DATA_DIR)

        # Mark restore code as used (if System Admin)
        if is_system_admin and restore_code:
            _mark_code_as_used(restore_code)

        # Log activity
        log_activity(
            current_user["username"],
            "Backup restored",
            f"Filename: {backup_filename}",
        )

        return True, f"Backup restored successfully from: {backup_filename}"

    except Exception as e:
        return False, f"Error restoring backup: {e}"


def generate_restore_code(backup_filename, target_username):
    """
    Generate one-use restore code for System Admin (Super Admin only).

    Uses prepared statements and logs activity.

    Args:
        backup_filename (str): Backup file the code is valid for
        target_username (str): System Admin who can use the code

    Returns:
        tuple: (success: bool, message: str, restore_code: str or None)

    Example:
        success, msg, code = generate_restore_code("backup_20251015.zip", "admin_001")
    """
    # Check permission (Super Admin only)
    if not check_permission("manage_restore_codes"):
        return (
            False,
            "Access denied. Only Super Administrator can generate restore codes",
            None,
        )

    current_user = get_current_user()

    # Validate backup exists
    backup_path = BACKUP_DIR / backup_filename

    if not backup_path.exists():
        return False, f"Backup file '{backup_filename}' not found", None

    # Generate secure random code
    code = "".join(
        secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12)
    )

    # Store code in database
    conn = get_connection()
    cursor = conn.cursor()

    # Encrypt sensitive data
    encrypted_code = encrypt_field(code)
    encrypted_backup = encrypt_field(backup_filename)
    encrypted_target = encrypt_field(target_username)

    # Prepared statement for INSERT
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS restore_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            backup_filename TEXT NOT NULL,
            target_username TEXT NOT NULL,
            used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        INSERT INTO restore_codes (code, backup_filename, target_username)
        VALUES (?, ?, ?)
        """,
        (encrypted_code, encrypted_backup, encrypted_target),
    )

    conn.commit()
    conn.close()

    # Log activity
    log_activity(
        current_user["username"],
        "Restore code generated",
        f"For user: {target_username}, Backup: {backup_filename}",
    )

    return True, "Restore code generated successfully", code


def revoke_restore_code(restore_code):
    """
    Revoke restore code (Super Admin only).

    Uses prepared statements and logs activity.

    Args:
        restore_code (str): Code to revoke

    Returns:
        tuple: (success: bool, message: str)

    Example:
        success, msg = revoke_restore_code("ABC123DEF456")
    """
    # Check permission (Super Admin only)
    if not check_permission("manage_restore_codes"):
        return (
            False,
            "Access denied. Only Super Administrator can revoke restore codes",
        )

    current_user = get_current_user()

    conn = get_connection()
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='restore_codes'
        """
    )

    if not cursor.fetchone():
        conn.close()
        return False, "No restore codes exist"

    # Get all restore codes and find matching one
    # Note: Cannot search encrypted field directly because Fernet is non-deterministic
    cursor.execute(
        "SELECT id, code, backup_filename, target_username FROM restore_codes WHERE used = 0"
    )

    results = cursor.fetchall()

    if not results:
        conn.close()
        return False, "No active restore codes found"

    # Find matching code by decrypting each one
    code_id = None
    encrypted_backup = None
    encrypted_target = None

    for row in results:
        row_id, encrypted_code, enc_backup, enc_target = row
        decrypted_code = decrypt_field(encrypted_code)
        if decrypted_code == restore_code:
            code_id = row_id
            encrypted_backup = enc_backup
            encrypted_target = enc_target
            break

    if not code_id:
        conn.close()
        return False, f"Restore code not found"

    # Prepared statement for DELETE
    cursor.execute("DELETE FROM restore_codes WHERE id = ?", (code_id,))

    conn.commit()
    conn.close()

    # Decrypt for logging
    backup_name = decrypt_field(encrypted_backup)
    target_user = decrypt_field(encrypted_target)

    # Log activity
    log_activity(
        current_user["username"],
        "Restore code revoked",
        f"For user: {target_user}, Backup: {backup_name}",
    )

    return True, "Restore code revoked successfully"


def list_backups():
    """
    List all available backup files.

    Returns:
        list: List of backup dictionaries

    Example:
        backups = list_backups()
        for backup in backups:
            print(f"{backup['filename']} - {backup['size']} bytes")
    """
    if not BACKUP_DIR.exists():
        return []

    backups = []

    for backup_file in BACKUP_DIR.glob("backup_*.zip"):
        stat = backup_file.stat()
        backups.append(
            {
                "filename": backup_file.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }
        )

    # Sort by creation time (newest first)
    backups.sort(key=lambda x: x["created"], reverse=True)

    return backups


def list_restore_codes():
    """
    List all active restore codes (Super Admin only).

    Returns:
        list: List of restore code dictionaries

    Example:
        codes = list_restore_codes()
        for code in codes:
            print(f"{code['target_username']} - {code['backup_filename']}")
    """
    # Check permission (Super Admin only)
    if not check_permission("manage_restore_codes"):
        return []

    conn = get_connection()
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='restore_codes'
        """
    )

    if not cursor.fetchone():
        conn.close()
        return []

    # Prepared statement to get all unused codes
    cursor.execute(
        """
        SELECT code, backup_filename, target_username, created_at
        FROM restore_codes
        WHERE used = 0
        ORDER BY created_at DESC
        """
    )

    results = cursor.fetchall()
    conn.close()

    codes = []

    for row in results:
        encrypted_code, encrypted_backup, encrypted_target, created_at = row
        codes.append(
            {
                "code": decrypt_field(encrypted_code),
                "backup_filename": decrypt_field(encrypted_backup),
                "target_username": decrypt_field(encrypted_target),
                "created_at": created_at,
            }
        )

    return codes


def _validate_restore_code(restore_code):
    """
    Validate restore code (internal helper).

    Args:
        restore_code (str): Code to validate

    Returns:
        tuple: (is_valid: bool, backup_filename: str or None)
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='restore_codes'
        """
    )

    if not cursor.fetchone():
        conn.close()
        return False, None

    encrypted_code = encrypt_field(restore_code)

    # Prepared statement
    cursor.execute(
        "SELECT backup_filename, used FROM restore_codes WHERE code = ?",
        (encrypted_code,),
    )

    result = cursor.fetchone()
    conn.close()

    if not result:
        return False, None

    encrypted_backup, used = result

    if used:
        return False, None

    return True, decrypt_field(encrypted_backup)


def _mark_code_as_used(restore_code):
    """
    Mark restore code as used (internal helper).

    Args:
        restore_code (str): Code to mark as used
    """
    conn = get_connection()
    cursor = conn.cursor()

    encrypted_code = encrypt_field(restore_code)

    # Prepared statement for UPDATE
    cursor.execute(
        "UPDATE restore_codes SET used = 1 WHERE code = ?", (encrypted_code,)
    )

    conn.commit()
    conn.close()


# Testing and demonstration
if __name__ == "__main__":
    from auth import login, logout

    print("=" * 60)
    print("BACKUP & RESTORE SYSTEM TESTING")
    print("=" * 60)

    # Login as super admin
    print("\n--- Logging in as Super Admin ---")
    login("super_admin", "Admin_123?")

    # Test 1: Create backup
    print("\n--- Test 1: Create Backup ---")
    success, msg, filename = create_backup()
    print(f"Result: {success}")
    print(f"Message: {msg}")
    if filename:
        print(f"Backup file: {filename}")

    # Test 2: List backups
    print("\n--- Test 2: List Backups ---")
    backups = list_backups()
    for backup in backups:
        print(
            f"  {backup['filename']:30s} | {backup['size']:10d} bytes | {backup['created']}"
        )

    # Test 3: Generate restore code
    print("\n--- Test 3: Generate Restore Code ---")
    if filename:
        success, msg, code = generate_restore_code(filename, "system_admin")
        print(f"Result: {success}")
        print(f"Message: {msg}")
        if code:
            print(f"Restore code: {code}")

    # Test 4: List restore codes
    print("\n--- Test 4: List Restore Codes ---")
    codes = list_restore_codes()
    for c in codes:
        print(
            f"  Code: {c['code']} | User: {c['target_username']} | Backup: {c['backup_filename']}"
        )

    # Test 5: Restore backup (Super Admin - no code needed)
    print("\n--- Test 5: Restore Backup (Super Admin) ---")
    if filename:
        success, msg = restore_backup(filename)
        print(f"Result: {success}")
        print(f"Message: {msg}")

    # Test 6: Revoke restore code
    print("\n--- Test 6: Revoke Restore Code ---")
    if code:
        success, msg = revoke_restore_code(code)
        print(f"Result: {success}")
        print(f"Message: {msg}")

    # Show logs
    print("\n--- Activity Logs ---")
    from logging import get_all_logs, display_logs

    logs = get_all_logs()
    display_logs(logs[-8:])

    logout()

    print("\n" + "=" * 60)
    print("✓ Backup & restore system ready!")
    print("=" * 60)
