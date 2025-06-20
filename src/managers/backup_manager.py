import os
import json
import sqlite3
import hashlib
import secrets
import string
from datetime import datetime
from typing import Dict, List, Optional


class BackupManager:
    def __init__(self, auth_service):
        self.auth = auth_service
        self.db = auth_service.db
        self.backup_dir = "src/data/backups"
        self.restore_codes = {}  # In-memory storage for restore codes

        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_dir, exist_ok=True)

    def can_create_backup(self) -> bool:
        """Check if current user can create backups"""
        if not self.auth.current_user:
            return False

        user_role = self.auth.current_user["role"]
        return user_role in ["super_admin", "system_admin"]

    def can_restore_backup(self) -> bool:
        """Check if current user can restore backups"""
        if not self.auth.current_user:
            return False

        user_role = self.auth.current_user["role"]
        return user_role == "super_admin"

    def can_use_restore_code(self) -> bool:
        """Check if current user can use restore codes"""
        if not self.auth.current_user:
            return False

        user_role = self.auth.current_user["role"]
        return user_role in ["super_admin", "system_admin"]

    def can_manage_restore_codes(self) -> bool:
        """Check if current user can generate/revoke restore codes"""
        if not self.auth.current_user:
            return False

        user_role = self.auth.current_user["role"]
        return user_role == "super_admin"

    def create_backup(self) -> Optional[str]:
        """Create a backup of the database"""
        if not self.can_create_backup():
            print("Access denied: You don't have permission to create backups!")
            return None

        try:
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}.json"
            backup_path = os.path.join(self.backup_dir, backup_filename)

            # Create backup data structure
            backup_data = {
                "created_at": datetime.now().isoformat(),
                "created_by": self.auth.current_user["username"],
                "version": "1.0",
                "tables": {},
            }

            with self.db.get_connection() as conn:
                # Backup users table
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")
                users_data = cursor.fetchall()

                # Get column names for users table
                cursor.execute("PRAGMA table_info(users)")
                users_columns = [column[1] for column in cursor.fetchall()]

                backup_data["tables"]["users"] = {
                    "columns": users_columns,
                    "data": users_data,
                }

                # Backup travelers table
                cursor.execute("SELECT * FROM travelers")
                travelers_data = cursor.fetchall()

                cursor.execute("PRAGMA table_info(travelers)")
                travelers_columns = [column[1] for column in cursor.fetchall()]

                backup_data["tables"]["travelers"] = {
                    "columns": travelers_columns,
                    "data": travelers_data,
                }

                # Backup scooters table
                cursor.execute("SELECT * FROM scooters")
                scooters_data = cursor.fetchall()

                cursor.execute("PRAGMA table_info(scooters)")
                scooters_columns = [column[1] for column in cursor.fetchall()]

                backup_data["tables"]["scooters"] = {
                    "columns": scooters_columns,
                    "data": scooters_data,
                }

            # Write backup to file
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(backup_data, f, indent=2, default=str)

            print(f"✅ Backup created successfully!")
            print(f"   File: {backup_filename}")
            print(f"   Location: {backup_path}")
            print(f"   Users: {len(backup_data['tables']['users']['data'])}")
            print(f"   Travelers: {len(backup_data['tables']['travelers']['data'])}")
            print(f"   Scooters: {len(backup_data['tables']['scooters']['data'])}")

            return backup_filename

        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return None

    def list_backups(self) -> List[str]:
        """List available backup files"""
        try:
            backup_files = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("backup_") and filename.endswith(".json"):
                    backup_files.append(filename)

            return sorted(backup_files, reverse=True)  # Newest first

        except Exception as e:
            print(f"Error listing backups: {e}")
            return []

    def show_backup_info(self, backup_filename: str) -> Optional[Dict]:
        """Show information about a backup file"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)

            if not os.path.exists(backup_path):
                print(f"Backup file not found: {backup_filename}")
                return None

            with open(backup_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)

            print(f"\n📋 BACKUP INFORMATION")
            print(f"   File: {backup_filename}")
            print(f"   Created: {backup_data.get('created_at', 'Unknown')}")
            print(f"   Created by: {backup_data.get('created_by', 'Unknown')}")
            print(f"   Version: {backup_data.get('version', 'Unknown')}")

            if "tables" in backup_data:
                for table_name, table_data in backup_data["tables"].items():
                    record_count = len(table_data.get("data", []))
                    print(f"   {table_name.title()}: {record_count} records")

            return backup_data

        except Exception as e:
            print(f"Error reading backup info: {e}")
            return None

    def restore_backup(
        self, backup_filename: str, restore_code: Optional[str] = None
    ) -> bool:
        """Restore database from backup"""
        # Check permissions
        if restore_code:
            # Using restore code - system admin or super admin
            if not self.can_use_restore_code():
                print("Access denied: You don't have permission to use restore codes!")
                return False

            if not self._validate_restore_code(restore_code):
                print("❌ Invalid or expired restore code!")
                return False
        else:
            # Direct restore - super admin only
            if not self.can_restore_backup():
                print(
                    "Access denied: Only Super Administrator can restore without codes!"
                )
                return False

        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)

            if not os.path.exists(backup_path):
                print(f"❌ Backup file not found: {backup_filename}")
                return False

            # Load backup data
            with open(backup_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)

            print(f"⚠️  WARNING: This will replace ALL current data!")
            confirm = input("Type 'RESTORE' to confirm: ").strip()

            if confirm != "RESTORE":
                print("Restore cancelled.")
                return False

            # Perform restore
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Disable foreign key checks temporarily
                cursor.execute("PRAGMA foreign_keys = OFF")

                # Restore each table
                for table_name, table_data in backup_data["tables"].items():
                    print(f"   Restoring {table_name}...")

                    # Clear existing data
                    cursor.execute(f"DELETE FROM {table_name}")

                    # Insert backup data
                    columns = table_data["columns"]
                    data_rows = table_data["data"]

                    if data_rows:
                        placeholders = ",".join(["?" for _ in columns])
                        insert_sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"

                        cursor.executemany(insert_sql, data_rows)

                # Re-enable foreign key checks
                cursor.execute("PRAGMA foreign_keys = ON")
                conn.commit()

            # Invalidate restore code if used
            if restore_code:
                self._invalidate_restore_code(restore_code)

            print("✅ Database restored successfully!")
            print("⚠️  Please restart the application to ensure proper functionality.")

            return True

        except Exception as e:
            print(f"❌ Error restoring backup: {e}")
            return False

    def generate_restore_code(self, backup_filename: str) -> Optional[str]:
        """Generate a restore code for a specific backup"""
        if not self.can_manage_restore_codes():
            print("Access denied: Only Super Administrator can generate restore codes!")
            return None

        try:
            # Verify backup exists
            backup_path = os.path.join(self.backup_dir, backup_filename)
            if not os.path.exists(backup_path):
                print(f"❌ Backup file not found: {backup_filename}")
                return None

            # Generate secure restore code
            code = self._generate_secure_code()

            # Store restore code with metadata
            self.restore_codes[code] = {
                "backup_file": backup_filename,
                "created_at": datetime.now().isoformat(),
                "created_by": self.auth.current_user["username"],
                "used": False,
            }

            print(f"✅ Restore code generated successfully!")
            print(f"   Code: {code}")
            print(f"   Backup: {backup_filename}")
            print(f"   ⚠️  This code can only be used once!")
            print(f"   ⚠️  Keep this code secure!")

            return code

        except Exception as e:
            print(f"❌ Error generating restore code: {e}")
            return None

    def list_restore_codes(self) -> None:
        """List all active restore codes"""
        if not self.can_manage_restore_codes():
            print("Access denied: Only Super Administrator can view restore codes!")
            return

        if not self.restore_codes:
            print("No active restore codes.")
            return

        print("\n📋 ACTIVE RESTORE CODES")
        print("=" * 60)

        for code, info in self.restore_codes.items():
            status = "USED" if info["used"] else "ACTIVE"
            print(f"Code: {code}")
            print(f"   Backup: {info['backup_file']}")
            print(f"   Created: {info['created_at']}")
            print(f"   Status: {status}")
            print("-" * 40)

    def revoke_restore_code(self, code: str) -> bool:
        """Revoke a restore code"""
        if not self.can_manage_restore_codes():
            print("Access denied: Only Super Administrator can revoke restore codes!")
            return False

        if code in self.restore_codes:
            del self.restore_codes[code]
            print(f"✅ Restore code {code} revoked successfully!")
            return True
        else:
            print(f"❌ Restore code not found: {code}")
            return False

    def _generate_secure_code(self) -> str:
        """Generate a secure restore code"""
        # Generate 12-character alphanumeric code
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(12))

    def _validate_restore_code(self, code: str) -> bool:
        """Validate a restore code"""
        if code not in self.restore_codes:
            return False

        code_info = self.restore_codes[code]

        # Check if code has been used
        if code_info["used"]:
            return False

        # Additional validation could include expiry time
        # For now, codes don't expire

        return True

    def _invalidate_restore_code(self, code: str) -> None:
        """Mark a restore code as used"""
        if code in self.restore_codes:
            self.restore_codes[code]["used"] = True
