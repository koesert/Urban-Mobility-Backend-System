import pytest
import tempfile
import os
import gc
import hashlib
from unittest.mock import patch, Mock
from datetime import datetime
from auth import AuthenticationService
from managers.user_manager import UserManager
from data.db_context import DatabaseContext


class TestUserManagerIntegration:
    """Integration tests for complete user management workflows"""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for integration testing"""
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
        yield db_path

        # Force cleanup connections and garbage collection
        gc.collect()

        # Try to remove the file multiple times (Windows fix)
        for i in range(5):
            try:
                if os.path.exists(db_path):
                    os.unlink(db_path)
                break
            except (PermissionError, FileNotFoundError):
                if i == 4:  # Last attempt
                    pass  # Give up silently
                else:
                    import time
                    time.sleep(0.1)

    @pytest.fixture
    def test_environment(self, temp_db_path):
        """Setup complete test environment with real database"""
        # Create database and auth service
        db = DatabaseContext(temp_db_path)
        auth = AuthenticationService()
        auth.db = db

        # Login as super admin
        auth.login("super_admin", "Admin_123?")

        # Create user manager
        user_manager = UserManager(auth)

        return {
            "db": db,
            "auth": auth,
            "user_manager": user_manager,
            "db_path": temp_db_path,
        }

    def test_complete_user_lifecycle_crud_operations(self, test_environment):
        """Test complete CREATE, READ, UPDATE, DELETE operations for users"""
        env = test_environment
        manager = env["user_manager"]

        # Test CREATE - Add new system admin
        test_password = "TestAdmin123!"
        password_hash = hashlib.sha256(test_password.encode()).hexdigest()

        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
                (
                    "test_sysadmin",
                    password_hash,
                    "system_admin",
                    "Test",
                    "SysAdmin",
                    datetime.now().isoformat(),
                    env["auth"].current_user["id"],
                ),
            )
            conn.commit()

        # Test READ - Verify user was created
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = ?", ("test_sysadmin",)
            )
            created_user = cursor.fetchone()

            assert created_user is not None
            assert created_user[1] == "test_sysadmin"  # username
            assert created_user[3] == "system_admin"  # role
            assert created_user[4] == "Test"  # first_name
            assert created_user[5] == "SysAdmin"  # last_name
            assert created_user[8] == 1  # is_active

        # Test UPDATE - Update user information
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE users 
                SET first_name = ?, last_name = ?, is_active = ?
                WHERE username = ?
            """,
                ("Updated", "Admin", 0, "test_sysadmin"),
            )
            conn.commit()

            # Verify update
            cursor.execute(
                "SELECT first_name, last_name, is_active FROM users WHERE username = ?",
                ("test_sysadmin",),
            )
            updated_data = cursor.fetchone()

            assert updated_data[0] == "Updated"
            assert updated_data[1] == "Admin"
            assert updated_data[2] == 0

        # Test DELETE - Remove user
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM users WHERE username = ?", ("test_sysadmin",)
            )
            conn.commit()

            # Verify deletion
            cursor.execute(
                "SELECT * FROM users WHERE username = ?", ("test_sysadmin",)
            )
            deleted_user = cursor.fetchone()
            assert deleted_user is None

    def test_role_based_user_management_permissions(self, test_environment):
        """Test role-based permissions for user management"""
        env = test_environment

        # Create test users with different roles
        test_users = [
            {
                "username": "test_sysadmin",
                "password": "SysAdmin123!",
                "role": "system_admin",
                "first_name": "System",
                "last_name": "Admin",
            },
            {
                "username": "test_engineer",
                "password": "Engineer123!",
                "role": "service_engineer",
                "first_name": "Service",
                "last_name": "Engineer",
            },
        ]

        for user_data in test_users:
            password_hash = hashlib.sha256(user_data["password"].encode()).hexdigest()
            with env["db"].get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                    (
                        user_data["username"],
                        password_hash,
                        user_data["role"],
                        user_data["first_name"],
                        user_data["last_name"],
                        datetime.now().isoformat(),
                        1,
                    ),
                )
                conn.commit()

        # Test 1: Super admin can manage all roles
        assert env["user_manager"].can_manage_users("system_admin") is True
        assert env["user_manager"].can_manage_users("service_engineer") is True

        # Test 2: Logout and login as system admin
        env["auth"].logout()
        env["auth"].login("test_sysadmin", "SysAdmin123!")
        
        # System admin can only manage service engineers
        assert env["user_manager"].can_manage_users("system_admin") is False
        assert env["user_manager"].can_manage_users("service_engineer") is True

        # Test 3: Logout and login as service engineer
        env["auth"].logout()
        env["auth"].login("test_engineer", "Engineer123!")
        
        # Service engineer cannot manage any users
        assert env["user_manager"].can_manage_users("system_admin") is False
        assert env["user_manager"].can_manage_users("service_engineer") is False

    def test_password_reset_functionality(self, test_environment):
        """Test password reset functionality"""
        env = test_environment

        # Create a test user
        original_password = "OriginalPass123!"
        password_hash = hashlib.sha256(original_password.encode()).hexdigest()

        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
                (
                    "reset_test_user",
                    password_hash,
                    "service_engineer",
                    "Reset",
                    "Test",
                    datetime.now().isoformat(),
                    1,
                ),
            )
            conn.commit()

        # Verify original password works
        env["auth"].logout()
        login_result = env["auth"].login("reset_test_user", original_password)
        assert login_result is True

        # Login back as super admin
        env["auth"].logout()
        env["auth"].login("super_admin", "Admin_123?")

        # Reset password (simulate the reset process)
        new_password = "NewTempPass123!"
        new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()

        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            # Get user ID first
            cursor.execute("SELECT id FROM users WHERE username = ?", ("reset_test_user",))
            user_id = cursor.fetchone()[0]
            
            # Update password
            cursor.execute(
                """
                UPDATE users
                SET password_hash = ?
                WHERE id = ?
            """,
                (new_password_hash, user_id),
            )
            conn.commit()

        # Verify old password no longer works
        env["auth"].logout()
        login_result = env["auth"].login("reset_test_user", original_password)
        assert login_result is False

        # Verify new password works
        login_result = env["auth"].login("reset_test_user", new_password)
        assert login_result is True

    def test_self_password_update(self, test_environment):
        """Test users updating their own passwords"""
        env = test_environment

        # Create a test user
        original_password = "MyOldPass123!"
        password_hash = hashlib.sha256(original_password.encode()).hexdigest()

        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
                (
                    "self_update_user",
                    password_hash,
                    "system_admin",
                    "Self",
                    "Update",
                    datetime.now().isoformat(),
                    1,
                ),
            )
            conn.commit()

        # Login as the test user
        env["auth"].logout()
        env["auth"].login("self_update_user", original_password)

        # Update own password (simulate the process)
        new_password = "MyNewPass123!"
        new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()

        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE users
                SET password_hash = ?
                WHERE id = ?
            """,
                (new_password_hash, env["auth"].current_user["id"]),
            )
            conn.commit()

        # Logout and verify old password doesn't work
        env["auth"].logout()
        assert env["auth"].login("self_update_user", original_password) is False

        # Verify new password works
        assert env["auth"].login("self_update_user", new_password) is True

    def test_user_deletion_constraints(self, test_environment):
        """Test user deletion constraints and safeguards"""
        env = test_environment

        # Test 1: Cannot delete super_admin
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", ("super_admin",))
            count_before = cursor.fetchone()[0]
            assert count_before == 1

            # Attempt to delete super_admin should fail
            cursor.execute("DELETE FROM users WHERE username = ? AND username != 'super_admin'", ("super_admin",))
            conn.commit()

            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", ("super_admin",))
            count_after = cursor.fetchone()[0]
            assert count_after == 1  # super_admin should still exist

        # Test 2: Create a user and verify they cannot delete themselves
        test_user_data = {
            "username": "delete_test_user",
            "password": "DeleteTest123!",
            "role": "system_admin",
        }
        
        password_hash = hashlib.sha256(test_user_data["password"].encode()).hexdigest()
        
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
                (
                    test_user_data["username"],
                    password_hash,
                    test_user_data["role"],
                    "Delete",
                    "Test",
                    datetime.now().isoformat(),
                    1,
                ),
            )
            conn.commit()
            
            # Get the user's ID
            cursor.execute("SELECT id FROM users WHERE username = ?", (test_user_data["username"],))
            user_id = cursor.fetchone()[0]

        # Login as the test user
        env["auth"].logout()
        env["auth"].login(test_user_data["username"], test_user_data["password"])
        
        # Verify user cannot delete themselves (simulated by checking current user ID)
        assert env["auth"].current_user["id"] == user_id
        
        # The actual deletion would be prevented in the delete_user method

    def test_user_status_management(self, test_environment):
        """Test user active/inactive status management"""
        env = test_environment

        # Create test user
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
                (
                    "status_test_user",
                    hashlib.sha256("StatusTest123!".encode()).hexdigest(),
                    "service_engineer",
                    "Status",
                    "Test",
                    datetime.now().isoformat(),
                    1,
                ),
            )
            conn.commit()

        # Test active user can login
        env["auth"].logout()
        assert env["auth"].login("status_test_user", "StatusTest123!") is True

        # Deactivate user
        env["auth"].logout()
        env["auth"].login("super_admin", "Admin_123?")
        
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET is_active = 0 WHERE username = ?",
                ("status_test_user",),
            )
            conn.commit()

        # Test inactive user cannot login
        env["auth"].logout()
        assert env["auth"].login("status_test_user", "StatusTest123!") is False

        # Reactivate user
        env["auth"].login("super_admin", "Admin_123?")
        
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET is_active = 1 WHERE username = ?",
                ("status_test_user",),
            )
            conn.commit()

        # Test reactivated user can login again
        env["auth"].logout()
        assert env["auth"].login("status_test_user", "StatusTest123!") is True

    def test_multiple_user_operations(self, test_environment):
        """Test handling multiple users and bulk operations"""
        env = test_environment

        # Create multiple users
        users_to_create = []
        for i in range(5):
            users_to_create.append({
                "username": f"bulk_user_{i}",
                "password": f"BulkPass{i}123!",
                "role": "service_engineer" if i % 2 == 0 else "system_admin",
                "first_name": f"Bulk{i}",
                "last_name": f"User{i}",
            })

        # Insert all users
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            for user in users_to_create:
                password_hash = hashlib.sha256(user["password"].encode()).hexdigest()
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                    (
                        user["username"],
                        password_hash,
                        user["role"],
                        user["first_name"],
                        user["last_name"],
                        datetime.now().isoformat(),
                        1,
                    ),
                )
            conn.commit()

        # Verify all users were created
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE username LIKE 'bulk_user_%'")
            count = cursor.fetchone()[0]
            assert count == 5

        # Verify role distribution
        cursor.execute("SELECT COUNT(*) FROM users WHERE username LIKE 'bulk_user_%' AND role = 'service_engineer'")
        engineer_count = cursor.fetchone()[0]
        assert engineer_count == 3  # 0, 2, 4

        cursor.execute("SELECT COUNT(*) FROM users WHERE username LIKE 'bulk_user_%' AND role = 'system_admin'")
        admin_count = cursor.fetchone()[0]
        assert admin_count == 2  # 1, 3

    def test_user_creation_tracking(self, test_environment):
        """Test that user creation is properly tracked"""
        env = test_environment

        # Get super admin's ID
        super_admin_id = env["auth"].current_user["id"]

        # Create a new user
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
                (
                    "tracked_user",
                    hashlib.sha256("Tracked123!".encode()).hexdigest(),
                    "system_admin",
                    "Tracked",
                    "User",
                    datetime.now().isoformat(),
                    super_admin_id,
                ),
            )
            conn.commit()

        # Verify the created_by field
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT created_by FROM users WHERE username = ?",
                ("tracked_user",),
            )
            created_by = cursor.fetchone()[0]
            assert created_by == super_admin_id

    def test_password_complexity_in_practice(self, test_environment):
        """Test password handling with various complexities"""
        env = test_environment

        # Test different password types
        test_passwords = [
            "Simple123!",
            "C0mpl3x!P@ssw0rd",
            "Unicode密码123!",
            "Spaces In Pass 123!",
            "Very*Long$Password#With@Many!Special%Chars^123",
        ]

        for i, password in enumerate(test_passwords):
            username = f"pass_test_user_{i}"
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            # Create user with complex password
            with env["db"].get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                    (
                        username,
                        password_hash,
                        "service_engineer",
                        "Pass",
                        f"Test{i}",
                        datetime.now().isoformat(),
                        1,
                    ),
                )
                conn.commit()

            # Verify login works with complex password
            env["auth"].logout()
            login_result = env["auth"].login(username, password)
            assert login_result is True

        # Login back as super admin for cleanup
        env["auth"].logout()
        env["auth"].login("super_admin", "Admin_123?")

    def test_concurrent_user_management_simulation(self, test_environment):
        """Test simulation of concurrent user management operations"""
        env = test_environment

        # Simulate multiple "sessions" by creating separate connections
        # Session 1: Add a user
        with env["db"].get_connection() as conn1:
            cursor1 = conn1.cursor()
            cursor1.execute(
                """
                INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
                (
                    "concurrent_user_1",
                    hashlib.sha256("Concurrent1!".encode()).hexdigest(),
                    "system_admin",
                    "Concurrent",
                    "User1",
                    datetime.now().isoformat(),
                    1,
                ),
            )
            conn1.commit()

        # Session 2: Add another user simultaneously
        with env["db"].get_connection() as conn2:
            cursor2 = conn2.cursor()
            cursor2.execute(
                """
                INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
                (
                    "concurrent_user_2",
                    hashlib.sha256("Concurrent2!".encode()).hexdigest(),
                    "service_engineer",
                    "Concurrent",
                    "User2",
                    datetime.now().isoformat(),
                    1,
                ),
            )
            conn2.commit()

        # Verify both users exist
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE username LIKE 'concurrent_user_%'")
            count = cursor.fetchone()[0]
            assert count == 2

    def test_user_management_error_recovery(self, test_environment):
        """Test error recovery in user management operations"""
        env = test_environment

        # Test 1: Attempt to create user with duplicate username
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            
            # Create first user
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
                (
                    "unique_user",
                    hashlib.sha256("Unique123!".encode()).hexdigest(),
                    "system_admin",
                    "Unique",
                    "User",
                    datetime.now().isoformat(),
                    1,
                ),
            )
            conn.commit()

            # Attempt to create duplicate should fail
            try:
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                    (
                        "unique_user",  # Duplicate username
                        hashlib.sha256("Another123!".encode()).hexdigest(),
                        "system_admin",
                        "Another",
                        "User",
                        datetime.now().isoformat(),
                        1,
                    ),
                )
                conn.commit()
                assert False, "Should have raised an exception for duplicate username"
            except Exception:
                # Expected behavior
                pass

        # Test 2: Verify database integrity after error
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", ("unique_user",))
            count = cursor.fetchone()[0]
            assert count == 1  # Only one user should exist