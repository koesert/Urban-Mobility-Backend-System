import sqlite3
import hashlib
import os
import secrets
import string
from datetime import datetime
from .encryption import encrypt_field, decrypt_field


class DatabaseContext:
    def __init__(self, db_path="src/data/urban_mobility.db"):
        self.db_path = db_path
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
        self.migrate_database()
        self.create_super_admin()

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Users table - stores all system users (not travelers)
            # Now includes username_encrypted field
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    username_encrypted TEXT,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('super_admin', 'system_admin', 'service_engineer')),
                    first_name TEXT,
                    last_name TEXT,
                    created_date TEXT NOT NULL,
                    created_by INTEGER,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            """
            )

            # Travelers table - customers who use scooters (managed by system users)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS travelers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id TEXT UNIQUE NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    birthday TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    street_name TEXT NOT NULL,
                    house_number TEXT NOT NULL,
                    zip_code TEXT NOT NULL,
                    city TEXT NOT NULL,
                    email TEXT NOT NULL,
                    mobile_phone TEXT NOT NULL,
                    driving_license TEXT NOT NULL,
                    registration_date TEXT NOT NULL
                )
            """
            )

            # Scooters table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS scooters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    brand TEXT NOT NULL,
                    model TEXT NOT NULL,
                    serial_number TEXT UNIQUE NOT NULL,
                    top_speed INTEGER NOT NULL,
                    battery_capacity INTEGER NOT NULL,
                    state_of_charge INTEGER NOT NULL,
                    target_range_min INTEGER NOT NULL,
                    target_range_max INTEGER NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    out_of_service_status TEXT DEFAULT '',
                    mileage REAL DEFAULT 0,
                    last_maintenance_date DATE,
                    in_service_date TEXT NOT NULL
                )
                """
            )

            conn.commit()

    def migrate_database(self):
        """Migrate existing database to add username_encrypted column and encrypt existing usernames"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if username_encrypted column exists
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if "username_encrypted" not in columns:
                # Add the column
                cursor.execute("ALTER TABLE users ADD COLUMN username_encrypted TEXT")
                
                # Encrypt existing usernames
                cursor.execute("SELECT id, username FROM users")
                users = cursor.fetchall()
                
                for user_id, username in users:
                    encrypted_username = encrypt_field(username)
                    cursor.execute(
                        "UPDATE users SET username_encrypted = ? WHERE id = ?",
                        (encrypted_username, user_id)
                    )
                
                conn.commit()

    def create_super_admin(self):
        """Create hard-coded super admin account"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check if super admin already exists (case-insensitive check)
            cursor.execute("SELECT id, username_encrypted FROM users WHERE role = 'super_admin'")
            existing_admins = cursor.fetchall()
            
            # Check for existing super_admin by decrypting usernames
            super_admin_exists = False
            for _, encrypted_username in existing_admins:
                if encrypted_username:
                    try:
                        decrypted = decrypt_field(encrypted_username)
                        if decrypted.lower() == "super_admin":
                            super_admin_exists = True
                            break
                    except:
                        continue
            
            if super_admin_exists:
                return  # Super admin already exists

            # Hash the password Admin_123?
            password_hash = hashlib.sha256("Admin_123?".encode()).hexdigest()

            cursor.execute(
                """
                INSERT INTO users (username, username_encrypted, password_hash, role, first_name, last_name, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    "super_admin",
                    encrypt_field("super_admin"),
                    password_hash,
                    "super_admin",
                    "Super",
                    "Administrator",
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()
            
    def create_user_account(self, username, password, role, first_name, last_name, created_by=None):
        """Create a new user account with the specified role and enforce role-based creation rules"""
        if role not in ("super_admin", "system_admin", "service_engineer"):
            raise ValueError("Invalid role")

        # Enforce role-based creation rules
        if role == "system_admin":
            # Only super_admin can create system_admin
            if created_by is None:
                raise PermissionError("Only super_admin can create system_admin accounts")
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT role FROM users WHERE id = ?", (created_by,))
                row = cursor.fetchone()
                if not row or row[0] != "super_admin":
                    raise PermissionError("Only super_admin can create system_admin accounts")
        elif role == "service_engineer":
            # Only system_admin or super_admin can create service_engineer
            if created_by is None:
                raise PermissionError("Only system_admin or super_admin can create service_engineer accounts")
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT role FROM users WHERE id = ?", (created_by,))
                row = cursor.fetchone()
                if not row or row[0] not in ("system_admin", "super_admin"):
                    raise PermissionError("Only system_admin or super_admin can create service_engineer accounts")
        elif role == "super_admin":
            # Prevent creation of additional super_admins via this method
            raise PermissionError("Cannot create additional super_admin accounts")

        # Check if username already exists (case-insensitive)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username_encrypted FROM users")
            existing_users = cursor.fetchall()
            
            for _, encrypted_username in existing_users:
                if encrypted_username:
                    try:
                        decrypted = decrypt_field(encrypted_username)
                        if decrypted.lower() == username.lower():
                            raise ValueError("Username already exists")
                    except:
                        continue

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, username_encrypted, password_hash, role, first_name, last_name, created_date, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    encrypt_field(username),
                    password_hash,
                    role,
                    first_name,
                    last_name,
                    datetime.now().isoformat(),
                    created_by,
                ),
            )
            conn.commit()
            
    # Example: Insert traveler with encrypted fields
    def insert_traveler(self, traveler):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO travelers (
                    customer_id, first_name, last_name, birthday, gender,
                    street_name, house_number, zip_code, city,
                    email, mobile_phone, driving_license, registration_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    traveler["customer_id"],
                    traveler["first_name"],
                    traveler["last_name"],
                    traveler["birthday"],
                    traveler["gender"],
                    traveler["street_name"],
                    traveler["house_number"],
                    traveler["zip_code"],
                    traveler["city"],
                    encrypt_field(traveler["email"]),
                    encrypt_field(traveler["mobile_phone"]),
                    encrypt_field(traveler["driving_license"]),
                    traveler["registration_date"],
                ),
            )
            conn.commit()

    # Example: Insert scooter with encrypted serial_number
    def insert_scooter(self, scooter):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO scooters (
                    brand, model, serial_number, top_speed, battery_capacity,
                    state_of_charge, target_range_min, target_range_max,
                    latitude, longitude, out_of_service_status, mileage,
                    last_maintenance_date, in_service_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scooter["brand"],
                    scooter["model"],
                    encrypt_field(scooter["serial_number"]),
                    scooter["top_speed"],
                    scooter["battery_capacity"],
                    scooter["state_of_charge"],
                    scooter["target_range_min"],
                    scooter["target_range_max"],
                    scooter["latitude"],
                    scooter["longitude"],
                    scooter.get("out_of_service_status", ""),
                    scooter.get("mileage", 0),
                    scooter.get("last_maintenance_date"),
                    scooter["in_service_date"],
                ),
            )
            conn.commit()
            
    def generate_temporary_password(self, length=12):
        """Generate a secure temporary password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def reset_user_password(self, username):
        """Reset a user's password and return the new temporary password"""
        temp_password = self.generate_temporary_password()
        password_hash = hashlib.sha256(temp_password.encode()).hexdigest()
        
        # Find user by encrypted username (case-insensitive)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username_encrypted FROM users")
            users = cursor.fetchall()
            
            user_id = None
            for uid, encrypted_username in users:
                if encrypted_username:
                    try:
                        decrypted = decrypt_field(encrypted_username)
                        if decrypted.lower() == username.lower():
                            user_id = uid
                            break
                    except:
                        continue
            
            if user_id:
                cursor.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (password_hash, user_id),
                )
                conn.commit()
                return temp_password
            else:
                raise ValueError("User not found")

    def delete_scooter_by_id(self, scooter_id):
        """Delete a scooter by its ID. Returns True if deleted, False if not found."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM scooters WHERE id = ?",
                (scooter_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def show_all_scooters(self):
        """Return a list of all scooters (with decrypted serial_number)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, brand, model, serial_number, top_speed, battery_capacity, state_of_charge,
                       target_range_min, target_range_max, latitude, longitude, out_of_service_status,
                       mileage, last_maintenance_date, in_service_date
                FROM scooters
                """
            )
            rows = cursor.fetchall()
            scooters = []
            for row in rows:
                scooter = {
                    "id": row[0],
                    "brand": row[1],
                    "model": row[2],
                    "serial_number": decrypt_field(row[3]),
                    "top_speed": row[4],
                    "battery_capacity": row[5],
                    "state_of_charge": row[6],
                    "target_range_min": row[7],
                    "target_range_max": row[8],
                    "latitude": row[9],
                    "longitude": row[10],
                    "out_of_service_status": row[11],
                    "mileage": row[12],
                    "last_maintenance_date": row[13],
                    "in_service_date": row[14],
                }
                scooters.append(scooter)
            return scooters

    def update_scooter_by_id(self, scooter_id, scooter):
        """Update scooter details by ID. Returns True if updated, False otherwise."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE scooters SET
                    brand = ?,
                    model = ?,
                    serial_number = ?,
                    top_speed = ?,
                    battery_capacity = ?,
                    state_of_charge = ?,
                    target_range_min = ?,
                    target_range_max = ?,
                    latitude = ?,
                    longitude = ?,
                    out_of_service_status = ?,
                    mileage = ?,
                    last_maintenance_date = ?
                WHERE id = ?
                """,
                (
                    scooter["brand"],
                    scooter["model"],
                    encrypt_field(scooter["serial_number"]),
                    scooter["top_speed"],
                    scooter["battery_capacity"],
                    scooter["state_of_charge"],
                    scooter["target_range_min"],
                    scooter["target_range_max"],
                    scooter["latitude"],
                    scooter["longitude"],
                    scooter["out_of_service_status"],
                    scooter["mileage"],
                    scooter["last_maintenance_date"],
                    scooter_id,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0