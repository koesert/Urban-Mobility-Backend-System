import sqlite3
import hashlib
import os
from datetime import datetime
from .encryption import encrypt_field, decrypt_field


class DatabaseContext:
    def __init__(self, db_path="Urban_mob/data/urban_mobility.db"):
        self.db_path = db_path
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
        self.create_super_admin()

    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Users table - stores all system users (not travelers)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
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

    def create_super_admin(self):
        """Create hard-coded super admin account"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check if super admin already exists
            cursor.execute(
                "SELECT id FROM users WHERE username = ?", ("super_admin",))
            if cursor.fetchone():
                return  # Super admin already exists

            # Hash the password Admin_123?
            password_hash = hashlib.sha256("Admin_123?".encode()).hexdigest()

            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, first_name, last_name, created_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    "super_admin",
                    password_hash,
                    "super_admin",
                    "Super",
                    "Administrator",
                    datetime.now().isoformat(),
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
