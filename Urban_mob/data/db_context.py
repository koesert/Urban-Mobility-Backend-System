import sqlite3
import hashlib
import os
from datetime import datetime


class DatabaseContext:
    def __init__(self, db_path="data/urban_mobility.db"):
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
                    out_of_service INTEGER DEFAULT 0,
                    mileage REAL DEFAULT 0,
                    last_maintenance_date TEXT,
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
            cursor.execute("SELECT id FROM users WHERE username = ?", ("super_admin",))
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
