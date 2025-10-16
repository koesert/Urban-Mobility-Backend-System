import sqlite3
import hashlib
import os
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from cryptography.fernet import Fernet
import base64

# File paths
DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "urban_mobility.db"
AES_KEY_PATH = DATA_DIR / "aes_key.bin"
FERNET_KEY_PATH = DATA_DIR / "fernet_key.bin"

# Default super admin credentials
SUPER_ADMIN_USERNAME = "super_admin"
SUPER_ADMIN_PASSWORD = "Admin_123?"


def load_or_create_aes_key():
    """
    Load or create AES-256 key for username encryption.

    Uses ECB mode because usernames need to be searchable in the database
    (same username must produce same encrypted value for WHERE queries).

    Returns:
        bytes: 32-byte AES encryption key
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if AES_KEY_PATH.exists():
        with open(AES_KEY_PATH, "rb") as key_file:
            key = key_file.read()
        print(f"✓ AES key loaded from {AES_KEY_PATH}")
    else:
        key = get_random_bytes(32)
        with open(AES_KEY_PATH, "wb") as key_file:
            key_file.write(key)
        print(f"✓ New AES key created at {AES_KEY_PATH}")

    return key


aes_key = load_or_create_aes_key()


def encrypt_username(username):
    """
    Encrypt username using deterministic AES-256 ECB.

    Must be deterministic to allow database lookups (WHERE username = ?).

    Args:
        username (str): Plain text username

    Returns:
        str: Base64-encoded encrypted username
    """
    if username is None or username == "":
        return ""

    cipher = AES.new(aes_key, AES.MODE_ECB)
    padded = pad(username.encode(), AES.block_size)
    encrypted = cipher.encrypt(padded)
    return base64.b64encode(encrypted).decode()


def decrypt_username(encrypted_username):
    """
    Decrypt AES-encrypted username back to plain text.

    Args:
        encrypted_username (str): Base64-encoded encrypted username

    Returns:
        str: Plain text username
    """
    if encrypted_username is None or encrypted_username == "":
        return ""

    cipher = AES.new(aes_key, AES.MODE_ECB)
    encrypted = base64.b64decode(encrypted_username)
    decrypted = cipher.decrypt(encrypted)
    return unpad(decrypted, AES.block_size).decode()


def load_or_create_fernet_key():
    """
    Load or create Fernet key for encrypting sensitive data that doesn't need to be searched.

    Uses non-deterministic encryption (different output each time) for better security.
    Used for: emails, phones, driving licenses, serial numbers.

    Returns:
        Fernet: Encryption cipher object
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if FERNET_KEY_PATH.exists():
        with open(FERNET_KEY_PATH, "rb") as key_file:
            key = key_file.read()
        print(f"✓ Fernet key loaded from {FERNET_KEY_PATH}")
    else:
        key = Fernet.generate_key()
        with open(FERNET_KEY_PATH, "wb") as key_file:
            key_file.write(key)
        print(f"✓ New Fernet key created at {FERNET_KEY_PATH}")

    return Fernet(key)


fernet_cipher = load_or_create_fernet_key()


def encrypt_field(plaintext):
    """
    Encrypt field using Fernet (non-deterministic, more secure).

    Use for data that doesn't need to be searched: emails, phones, licenses, serial numbers.

    Args:
        plaintext (str): Plain text value

    Returns:
        str: Encrypted text
    """
    if plaintext is None or plaintext == "":
        return ""
    encrypted_bytes = fernet_cipher.encrypt(plaintext.encode())
    return encrypted_bytes.decode()


def decrypt_field(encrypted_text):
    """
    Decrypt Fernet-encrypted field back to plain text.

    Args:
        encrypted_text (str): Encrypted text

    Returns:
        str: Plain text value
    """
    if encrypted_text is None or encrypted_text == "":
        return ""
    decrypted_bytes = fernet_cipher.decrypt(encrypted_text.encode())
    return decrypted_bytes.decode()


def hash_password(password, username):
    """
    Hash password with SHA-256 using username as salt.

    Salting prevents rainbow table attacks and ensures identical passwords
    produce different hashes for different users.

    Args:
        password (str): Plain text password
        username (str): Username (used as salt)

    Returns:
        str: SHA-256 hash as hexadecimal string
    """
    salt = username.lower()
    salted_password = password + salt
    password_hash = hashlib.sha256(salted_password.encode()).hexdigest()
    return password_hash


def verify_password(password, username, stored_hash):
    """
    Verify password by comparing hashes.

    Args:
        password (str): Plain text password to verify
        username (str): Username (for salt)
        stored_hash (str): Hash from database

    Returns:
        bool: True if password is correct
    """
    input_hash = hash_password(password, username)
    return input_hash == stored_hash


def get_connection():
    """
    Create and return a database connection with foreign keys enabled.

    Returns:
        sqlite3.Connection: Database connection
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables():
    """
    Create database schema: users, travelers, and scooters tables.

    All sensitive fields are encrypted, passwords are hashed.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Users: system administrators and service engineers
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('super_admin', 'system_admin', 'service_engineer')),
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            must_change_password INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Travelers: customers with encrypted personal information
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS travelers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            birthday TEXT NOT NULL,
            gender TEXT NOT NULL CHECK(gender IN ('Male', 'Female')),
            street_name TEXT NOT NULL,
            house_number TEXT NOT NULL,
            zip_code TEXT NOT NULL,
            city TEXT NOT NULL,
            email TEXT NOT NULL,
            mobile_phone TEXT NOT NULL,
            driving_license TEXT NOT NULL,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # Scooters: fleet inventory with encrypted serial numbers
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS scooters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_number TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            battery_level INTEGER NOT NULL CHECK(battery_level >= 0 AND battery_level <= 100),
            status TEXT NOT NULL CHECK(status IN ('available', 'in_use', 'maintenance')),
            location TEXT NOT NULL,
            last_service_date TEXT,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    conn.commit()
    conn.close()

    print("✓ Database tables created successfully")


def init_super_admin():
    """
    Create default super admin account if it doesn't exist.

    Credentials: super_admin / Admin_123?
    Has full access to all system features.
    """
    conn = get_connection()
    cursor = conn.cursor()

    encrypted_username = encrypt_username(SUPER_ADMIN_USERNAME)
    cursor.execute("SELECT id FROM users WHERE username = ?", (encrypted_username,))

    if cursor.fetchone() is None:
        password_hash = hash_password(SUPER_ADMIN_PASSWORD, SUPER_ADMIN_USERNAME)
        cursor.execute(
            """
            INSERT INTO users (username, password_hash, role, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                encrypted_username,
                password_hash,
                "super_admin",
                "Super",
                "Administrator",
            ),
        )

        conn.commit()
        print(f"✓ Super Admin account created")
        print(f"  Username: {SUPER_ADMIN_USERNAME}")
        print(f"  Password: {SUPER_ADMIN_PASSWORD}")
    else:
        print(f"✓ Super Admin account already exists")

    conn.close()


def init_database():
    """
    Initialize the complete database system: keys, tables, and super admin.

    Called on application startup.
    """
    print("=" * 60)
    print("URBAN MOBILITY BACKEND SYSTEM - DATABASE INITIALIZATION")
    print("=" * 60)

    create_tables()
    init_super_admin()

    print("=" * 60)
    print("✓ Database initialization complete!")
    print(f"✓ Database location: {DB_PATH}")
    print(f"✓ AES key (usernames): {AES_KEY_PATH}")
    print(f"✓ Fernet key (other data): {FERNET_KEY_PATH}")
    print("=" * 60)


# Testing and demonstration
if __name__ == "__main__":
    init_database()

    # Verify username encryption is deterministic (required for database queries)
    print("\n--- Testing Username Encryption (AES-256 ECB - Deterministic) ---")
    test_username = "super_admin"
    encrypted1 = encrypt_username(test_username)
    encrypted2 = encrypt_username(test_username)
    decrypted = decrypt_username(encrypted1)

    print(f"Original:     {test_username}")
    print(f"Encrypted 1:  {encrypted1}")
    print(f"Encrypted 2:  {encrypted2}")
    print(f"Deterministic? {encrypted1 == encrypted2} (Must be True)")
    print(f"Decrypted:    {decrypted}")
    print(f"Match: {test_username == decrypted}")

    # Verify Fernet encryption is non-deterministic (better security)
    print("\n--- Testing Other Field Encryption (Fernet - Non-Deterministic) ---")
    test_email = "test@example.com"
    encrypted_email1 = encrypt_field(test_email)
    encrypted_email2 = encrypt_field(test_email)
    decrypted_email = decrypt_field(encrypted_email1)

    print(f"Original:     {test_email}")
    print(f"Encrypted 1:  {encrypted_email1[:50]}...")
    print(f"Encrypted 2:  {encrypted_email2[:50]}...")
    print(
        f"Deterministic? {encrypted_email1 == encrypted_email2} (Must be False for security)"
    )
    print(f"Decrypted:    {decrypted_email}")
    print(f"Match: {test_email == decrypted_email}")

    # Verify password hashing with salt
    print("\n--- Testing Password Hashing (SHA-256 + Salt) ---")
    test_username = "test_user"
    test_password = "TestPass123!"
    password_hash = hash_password(test_password, test_username)
    print(f"Username: {test_username}")
    print(f"Password: {test_password}")
    print(f"Hash: {password_hash}")
    print(
        f"Verify (correct): {verify_password(test_password, test_username, password_hash)}"
    )
    print(
        f"Verify (wrong): {verify_password('WrongPass123!', test_username, password_hash)}"
    )
