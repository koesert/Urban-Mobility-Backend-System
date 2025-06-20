import hashlib
import random
import string
from datetime import datetime
from data.db_context import DatabaseContext
from data.encryption import encrypt_field, decrypt_field


class UserManager:
    def __init__(self, auth_service):
        self.auth = auth_service
        self.db = auth_service.db

    def can_manage_users(self, target_role):
        """Check if current user can manage users of the target role"""
        if not self.auth.current_user:
            return False

        current_role = self.auth.current_user["role"]

        # Super admin can manage all roles
        if current_role == "super_admin":
            return True

        # System admin can only manage service engineers
        if current_role == "system_admin" and target_role == "service_engineer":
            return True

        return False

    def can_update_own_password(self):
        """Check if user can update their own password"""
        return self.auth.is_logged_in()

    def can_reset_user_password(self):
        """Check if current user can reset other users' passwords"""
        if not self.auth.current_user:
            return False

        current_role = self.auth.current_user["role"]
        return current_role in ["super_admin", "system_admin"]

    def display_user_management_menu(self, user_type):
        """Display user management menu based on user type"""
        if user_type == "system_admin" and not self.can_manage_users("system_admin"):
            print(
                "Access denied: Only Super Administrators can manage System Administrators!"
            )
            return None

        if user_type == "service_engineer" and not self.can_manage_users(
            "service_engineer"
        ):
            print("Access denied: Insufficient permissions!")
            return None

        print(f"\n--- MANAGE {user_type.upper().replace('_', ' ')}S ---")
        print("1. View All Users")
        print("2. Add New User")
        print("3. Update User")
        print("4. Delete User")
        print("5. Reset User Password")
        print("6. Back to Main Menu")

        choice = input("Select an option: ")
        return choice

    def handle_user_management_menu(self, user_type):
        """Handle user management operations"""
        role_map = {
            "system_admin": "system_admin",
            "service_engineer": "service_engineer",
        }

        target_role = role_map.get(user_type)
        if not target_role:
            print("Invalid user type!")
            return

        while True:
            choice = self.display_user_management_menu(user_type)

            if choice == "1":
                self.view_users(target_role)
            elif choice == "2":
                self.add_user(target_role)
            elif choice == "3":
                self.update_user(target_role)
            elif choice == "4":
                self.delete_user(target_role)
            elif choice == "5":
                self.reset_user_password(target_role)
            elif choice == "6":
                break
            else:
                print("Invalid choice! Please try again.")

            if choice in ["1", "2", "3", "4", "5"]:
                input("\nPress Enter to continue...")

    def view_users(self, role_filter=None):
        """Display all users or users with specific role"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                if role_filter:
                    cursor.execute(
                        """
                        SELECT id, username, role, first_name, last_name, created_date, is_active
                        FROM users
                        WHERE role = ?
                        ORDER BY created_date DESC
                    """,
                        (role_filter,),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT id, username, role, first_name, last_name, created_date, is_active
                        FROM users
                        ORDER BY role, created_date DESC
                    """
                    )

                users = cursor.fetchall()

                if not users:
                    print("No users found.")
                    return

                print(
                    f"\n{'ID':<5} {'Username':<15} {'Role':<20} {'Name':<25} {'Created':<20} {'Status':<10}"
                )
                print("-" * 100)

                for user in users:
                    (
                        user_id,
                        username,
                        role,
                        first_name,
                        last_name,
                        created_date,
                        is_active,
                    ) = user
                    full_name = f"{first_name} {last_name}"
                    role_display = role.replace("_", " ").title()
                    status = "Active" if is_active else "Inactive"
                    created_short = created_date[:10] if created_date else "N/A"

                    print(
                        f"{user_id:<5} {username:<15} {role_display:<20} {full_name:<25} {created_short:<20} {status:<10}"
                    )

                print(f"\nTotal users: {len(users)}")

        except Exception as e:
            print(f"Error retrieving users: {e}")

    def add_user(self, role):
        """Add a new user with specified role"""
        print(f"\n--- ADD NEW {role.upper().replace('_', ' ')} ---")

        try:
            # Collect user information
            username = self._get_unique_username()
            if not username:
                return

            first_name = self._get_required_input("First Name")
            if not first_name:
                return

            last_name = self._get_required_input("Last Name")
            if not last_name:
                return

            # Generate temporary password
            temp_password = self._generate_temporary_password()

            # Hash the password
            password_hash = hashlib.sha256(temp_password.encode()).hexdigest()

            # Insert user with encrypted username
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO users (username, username_encrypted, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                    (
                        username,
                        encrypt_field(username),
                        password_hash,
                        role,
                        first_name,
                        last_name,
                        datetime.now().isoformat(),
                        self.auth.current_user["id"],
                    ),
                )
                conn.commit()

            print(f"\n✅ User created successfully!")
            print(f"Username: {username}")
            print(f"Temporary Password: {temp_password}")
            print(f"⚠️  Please share this password securely with the user.")
            print(f"⚠️  The user should change this password on first login.")

            self.auth.logger.log_activity(
                username=self.auth.current_user["username"],
                activity="Add user",
                details=f"User with username: {username} added."
            )

        except Exception as e:
            print(f"Error adding user: {e}")

    def update_user(self, role_filter):
        """Update an existing user"""
        # First show users of this role
        self.view_users(role_filter)

        user_id = input("\nEnter User ID to update: ").strip()
        if not user_id or not user_id.isdigit():
            print("Invalid User ID!")
            return

        # Get user details
        user = self._get_user_by_id(int(user_id))
        if not user:
            print("User not found!")
            return

        # Check if user has permission to update this user
        if user[2] != role_filter:
            print("You can only update users of the specified role!")
            return

        print(f"\nUpdating user: {user[1]} ({user[3]} {user[4]})")
        print("Press Enter to keep current value")

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Define allowed fields that can be updated
                ALLOWED_FIELDS = ['first_name', 'last_name', 'is_active']

                # Collect updates
                updates = {}

                # First name
                new_first_name = input(f"First Name ({user[3]}): ").strip()
                if new_first_name:
                    updates["first_name"] = new_first_name

                # Last name
                new_last_name = input(f"Last Name ({user[4]}): ").strip()
                if new_last_name:
                    updates["last_name"] = new_last_name

                # Active status
                current_status = "Active" if user[6] else "Inactive"
                status_input = (
                    input(f"Status - Active/Inactive ({current_status}): ")
                    .strip()
                    .lower()
                )
                if status_input in ["active", "inactive"]:
                    updates["is_active"] = 1 if status_input == "active" else 0

                if not updates:
                    print("No changes made.")
                    return

                # Validate that all update fields are in allowed list
                for field in updates.keys():
                    if field not in ALLOWED_FIELDS:
                        print(
                            f"Error: Field '{field}' is not allowed to be updated")
                        return

                # Build UPDATE query using only validated fields
                if len(updates) == 1:
                    field = list(updates.keys())[0]
                    cursor.execute(
                        f"UPDATE users SET {field} = ? WHERE id = ?",
                        (updates[field], user_id)
                    )
                elif len(updates) == 2:
                    fields = list(updates.keys())
                    cursor.execute(
                        f"UPDATE users SET {fields[0]} = ?, {fields[1]} = ? WHERE id = ?",
                        (updates[fields[0]], updates[fields[1]], user_id)
                    )
                elif len(updates) == 3:
                    cursor.execute(
                        "UPDATE users SET first_name = ?, last_name = ?, is_active = ? WHERE id = ?",
                        (updates.get('first_name', user[3]),
                         updates.get('last_name', user[4]),
                         updates.get('is_active', user[6]),
                         user_id)
                    )

                conn.commit()

                if cursor.rowcount > 0:
                    print("✅ User updated successfully!")

                    self.auth.logger.log_activity(
                        username=self.auth.current_user["username"],
                        activity="Update user",
                        details=f"User with user id: {user[0]} & username: {user[1]} updated."
                    )

                else:
                    print("No changes were made.")

        except Exception as e:
            print(f"Error updating user: {e}")

    def delete_user(self, role_filter):
        """Delete a user"""
        # First show users of this role
        self.view_users(role_filter)

        user_id = input("\nEnter User ID to delete: ").strip()
        if not user_id or not user_id.isdigit():
            print("Invalid User ID!")
            return

        # Get user details
        user = self._get_user_by_id(int(user_id))
        if not user:
            print("User not found!")
            return

        # Check if user has permission to delete this user
        if user[2] != role_filter:
            print("You can only delete users of the specified role!")
            return

        # Prevent self-deletion
        if user[0] == self.auth.current_user["id"]:
            print("You cannot delete your own account!")
            return

        # Prevent deletion of super_admin
        if user[1] == "super_admin":
            print("The super_admin account cannot be deleted!")
            return

        print(f"\nUser to be deleted: {user[1]} ({user[3]} {user[4]})")
        print("⚠️  WARNING: This action cannot be undone!")

        confirmation = input("Type 'DELETE' to confirm deletion: ").strip()
        if confirmation != "DELETE":
            print("Deletion cancelled.")
            return

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()

                if cursor.rowcount > 0:
                    print("✅ User deleted successfully!")

                    self.auth.logger.log_activity(
                        username=self.auth.current_user["username"],
                        activity="Delete user",
                        details=f"User with ID: {user[0]} & username: {user[1]} deleted."
                    )

                else:
                    print("Error: User could not be deleted.")

        except Exception as e:
            print(f"Error deleting user: {e}")

    def reset_user_password(self, role_filter=None):
        """Reset a user's password"""
        if not self.can_reset_user_password():
            print("Access denied: You don't have permission to reset passwords!")
            return

        # Show users
        if role_filter:
            self.view_users(role_filter)
        else:
            self.view_users()

        user_id = input("\nEnter User ID to reset password: ").strip()
        if not user_id or not user_id.isdigit():
            print("Invalid User ID!")
            return

        # Get user details
        user = self._get_user_by_id(int(user_id))
        if not user:
            print("User not found!")
            return

        # Check role filter if specified
        if role_filter and user[2] != role_filter:
            print("You can only reset passwords for users of the specified role!")
            return

        # Generate new temporary password
        temp_password = self._generate_temporary_password()
        password_hash = hashlib.sha256(temp_password.encode()).hexdigest()

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE users
                    SET password_hash = ?
                    WHERE id = ?
                """,
                    (password_hash, user_id),
                )
                conn.commit()

                print(f"\n✅ Password reset successfully!")
                print(f"Username: {user[1]}")
                print(f"New Temporary Password: {temp_password}")
                print(f"⚠️  Please share this password securely with the user.")
                print(f"⚠️  The user should change this password on next login.")

        except Exception as e:
            print(f"Error resetting password: {e}")

    def update_own_password(self):
        """Allow user to update their own password"""
        if not self.can_update_own_password():
            print("You must be logged in to change your password!")
            return

        print("\n--- UPDATE PASSWORD ---")
        print(f"Updating password for: {self.auth.current_user['username']}")

        # Get current password for verification
        current_password = input("Current Password: ").strip()
        if not current_password:
            print("Password update cancelled.")
            return

        # Verify current password
        current_hash = hashlib.sha256(current_password.encode()).hexdigest()

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT password_hash FROM users WHERE id = ?
            """,
                (self.auth.current_user["id"],),
            )
            stored_hash = cursor.fetchone()[0]

            if current_hash != stored_hash:
                print("❌ Current password is incorrect!")
                return

        # Get new password
        new_password = self._get_new_password()
        if not new_password:
            return

        # Update password
        new_hash = hashlib.sha256(new_password.encode()).hexdigest()

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE users
                    SET password_hash = ?
                    WHERE id = ?
                """,
                    (new_hash, self.auth.current_user["id"]),
                )
                conn.commit()

                print("✅ Password updated successfully!")
                print("Please use your new password on next login.")

        except Exception as e:
            print(f"Error updating password: {e}")

    # Helper methods
    def _get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, username, role, first_name, last_name, created_date, is_active FROM users WHERE id = ?",
                    (user_id,),
                )
                return cursor.fetchone()
        except Exception:
            return None

    def _get_unique_username(self):
        """Get a unique username from user input (case-insensitive check)"""
        while True:
            username = input("Username: ").strip()
            if not username:
                print("Username cannot be empty!")
                if input("Try again? (y/n): ").lower() != "y":
                    return None
                continue

            # Check if username already exists (case-insensitive)
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username_encrypted FROM users")
                existing_users = cursor.fetchall()
                
                username_exists = False
                for _, encrypted_username in existing_users:
                    if encrypted_username:
                        try:
                            decrypted = decrypt_field(encrypted_username)
                            if decrypted.lower() == username.lower():
                                username_exists = True
                                break
                        except:
                            continue
                
                if username_exists:
                    print("Username already exists!")
                    if input("Try again? (y/n): ").lower() != "y":
                        return None
                    continue

            return username

    def _get_required_input(self, field_name):
        """Get required input with retry capability"""
        while True:
            value = input(f"{field_name}: ").strip()
            if value:
                return value
            else:
                print(f"{field_name} is required!")
                if input("Try again? (y/n): ").lower() != "y":
                    return None

    def _generate_temporary_password(self):
        """Generate a secure temporary password with guaranteed complexity"""
        # Ensure at least one of each character type
        password_chars = []
        password_chars.append(random.choice(string.ascii_lowercase))
        password_chars.append(random.choice(string.ascii_uppercase))
        password_chars.append(random.choice(string.digits))
        password_chars.append(random.choice("!@#$%^&*"))

        # Fill the rest randomly
        all_chars = string.ascii_letters + string.digits + "!@#$%^&*"
        for _ in range(8):  # Total 12 characters
            password_chars.append(random.choice(all_chars))

        # Shuffle to avoid predictable patterns
        random.shuffle(password_chars)
        return "".join(password_chars)

    def _get_new_password(self):
        """Get new password with validation"""
        while True:
            password = input("New Password (min 8 characters): ").strip()
            if not password:
                print("Password cannot be empty!")
                if input("Try again? (y/n): ").lower() != "y":
                    return None
                continue

            if len(password) < 8:
                print("Password must be at least 8 characters long!")
                if input("Try again? (y/n): ").lower() != "y":
                    return None
                continue

            # Confirm password
            confirm = input("Confirm New Password: ").strip()
            if password != confirm:
                print("Passwords do not match!")
                if input("Try again? (y/n): ").lower() != "y":
                    return None
                continue

            return password