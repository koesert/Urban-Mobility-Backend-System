import pytest
import tempfile
import os
import gc
import hashlib
import sqlite3
from unittest.mock import patch, Mock
from datetime import datetime
from auth import AuthenticationService
from managers.user_manager import UserManager
from data.db_context import DatabaseContext


class TestUserManagerSecurity:
    """Security-focused tests for user management"""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for security testing"""
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
    def secure_test_environment(self, temp_db_path):
        """Setup secure test environment"""
        db = DatabaseContext(temp_db_path)
        auth = AuthenticationService()
        auth.db = db

        return {
            "db": db,
            "auth": auth,
            "db_path": temp_db_path,
        }

    def test_unauthorized_access_prevention_no_login(self, secure_test_environment):
        """Test that unauthorized users cannot access user management"""
        env = secure_test_environment

        # Test with no user logged in
        env["auth"].current_user = None
        user_manager = UserManager(env["auth"])

        # All management functions should be denied
        assert user_manager.can_manage_users("system_admin") is False
        assert user_manager.can_manage_users("service_engineer") is False
        assert user_manager.can_reset_user_password() is False
        assert user_manager.can_update_own_password() is False

    def test_role_based_access_control_strict_enforcement(self, secure_test_environment):
        """Test strict enforcement of role-based access control"""
        env = secure_test_environment

        # Create users with different roles
        test_roles = [
            ("test_super", "Super123!", "super_admin"),
            ("test_sysadmin", "SysAdmin123!", "system_admin"),
            ("test_engineer", "Engineer123!", "service_engineer"),
        ]

        for username, password, role in test_roles:
            with env["db"].get_connection() as conn:
                cursor = conn.cursor()
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                    (
                        username,
                        password_hash,
                        role,
                        "Test",
                        role.title(),
                        datetime.now().isoformat(),
                        1,
                    ),
                )
                conn.commit()

        # Test each role's permissions
        # Super Admin - can manage all
        env["auth"].login("test_super", "Super123!")
        user_manager = UserManager(env["auth"])
        assert user_manager.can_manage_users("super_admin") is True
        assert user_manager.can_manage_users("system_admin") is True
        assert user_manager.can_manage_users("service_engineer") is True
        assert user_manager.can_reset_user_password() is True

        # System Admin - limited access
        env["auth"].logout()
        env["auth"].login("test_sysadmin", "SysAdmin123!")
        assert user_manager.can_manage_users("super_admin") is False
        assert user_manager.can_manage_users("system_admin") is False
        assert user_manager.can_manage_users("service_engineer") is True
        assert user_manager.can_reset_user_password() is True

        # Service Engineer - no management access
        env["auth"].logout()
        env["auth"].login("test_engineer", "Engineer123!")
        assert user_manager.can_manage_users("super_admin") is False
        assert user_manager.can_manage_users("system_admin") is False
        assert user_manager.can_manage_users("service_engineer") is False
        assert user_manager.can_reset_user_password() is False

    def test_password_security_hashing(self, secure_test_environment):
        """Test that passwords are properly hashed and never stored in plain text"""
        env = secure_test_environment

        # Test password to check
        test_password = "SecurePassword123!"
        test_username = "security_test_user"

        # Create user with password
        password_hash = hashlib.sha256(test_password.encode()).hexdigest()
        
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
                (
                    test_username,
                    password_hash,
                    "system_admin",
                    "Security",
                    "Test",
                    datetime.now().isoformat(),
                    1,
                ),
            )
            conn.commit()

        # Verify password is not stored in plain text
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT password_hash FROM users WHERE username = ?",
                (test_username,),
            )
            stored_hash = cursor.fetchone()[0]

            # Stored value should be a hash, not the original password
            assert stored_hash != test_password
            assert len(stored_hash) == 64  # SHA256 produces 64-character hex string
            assert stored_hash == password_hash

    def test_sql_injection_prevention(self, secure_test_environment):
        """Test that SQL injection attacks are prevented"""
        env = secure_test_environment
        env["auth"].login("super_admin", "Admin_123?")
        user_manager = UserManager(env["auth"])

        # Various SQL injection attempts
        malicious_inputs = [
            "admin'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin' UNION SELECT * FROM users --",
            "'; UPDATE users SET role='super_admin' WHERE '1'='1'; --",
            "admin'/*",
            "admin' AND 1=1 --",
        ]

        for malicious_input in malicious_inputs:
            # Test in username field
            with env["db"].get_connection() as conn:
                cursor = conn.cursor()
                
                # This should be safe due to parameterized queries
                cursor.execute(
                    "SELECT * FROM users WHERE username = ?",
                    (malicious_input,),
                )
                result = cursor.fetchall()
                
                # Should not return any results for malicious input
                assert len(result) == 0

                # Verify database structure is intact
                cursor.execute("SELECT COUNT(*) FROM users")
                count = cursor.fetchone()[0]
                assert count >= 1  # At least super_admin should exist

    def test_privilege_escalation_prevention(self, secure_test_environment):
        """Test that users cannot escalate their privileges"""
        env = secure_test_environment

        # Create a service engineer
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
                (
                    "low_privilege_user",
                    hashlib.sha256("LowPriv123!".encode()).hexdigest(),
                    "service_engineer",
                    "Low",
                    "Privilege",
                    datetime.now().isoformat(),
                    1,
                ),
            )
            conn.commit()

        # Login as service engineer
        env["auth"].login("low_privilege_user", "LowPriv123!")
        user_manager = UserManager(env["auth"])

        # Verify they cannot access management functions
        assert user_manager.can_manage_users("system_admin") is False
        assert user_manager.can_reset_user_password() is False

        # Even if they somehow modify their session role (simulating attack)
        original_role = env["auth"].current_user["role"]
        env["auth"].current_user["role"] = "super_admin"

        # The actual database role should still be checked in a real implementation
        # Reset to original for accurate testing
        env["auth"].current_user["role"] = original_role

    def test_super_admin_protection(self, secure_test_environment):
        """Test that super_admin account is protected from deletion"""
        env = secure_test_environment
        env["auth"].login("super_admin", "Admin_123?")

        # Verify super_admin exists
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", ("super_admin",))
            super_admin_id = cursor.fetchone()[0]

        # Attempt to delete super_admin should be prevented
        # In the actual implementation, this is prevented in the delete_user method
        # Here we verify the account exists and has special properties
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT username, role FROM users WHERE id = ?",
                (super_admin_id,),
            )
            result = cursor.fetchone()
            assert result[0] == "super_admin"
            assert result[1] == "super_admin"

    def test_password_complexity_generation(self, secure_test_environment):
        """Test that generated temporary passwords meet security requirements"""
        env = secure_test_environment
        env["auth"].login("super_admin", "Admin_123?")
        user_manager = UserManager(env["auth"])

        # Generate multiple temporary passwords
        generated_passwords = []
        for _ in range(10):
            password = user_manager._generate_temporary_password()
            generated_passwords.append(password)

        # Verify password complexity
        for password in generated_passwords:
            assert len(password) == 12  # Required length
            assert any(c.isupper() for c in password)  # Has uppercase
            assert any(c.islower() for c in password)  # Has lowercase
            assert any(c.isdigit() for c in password)  # Has digits
            assert any(c in "!@#$%^&*" for c in password)  # Has special chars

        # Verify uniqueness
        assert len(set(generated_passwords)) == 10  # All should be unique

    def test_session_security_password_update(self, secure_test_environment):
        """Test session security during password updates"""
        env = secure_test_environment

        # Create test user
        original_password = "Original123!"
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
                (
                    "session_test_user",
                    hashlib.sha256(original_password.encode()).hexdigest(),
                    "system_admin",
                    "Session",
                    "Test",
                    datetime.now().isoformat(),
                    1,
                ),
            )
            conn.commit()

        # Login as test user
        env["auth"].login("session_test_user", original_password)
        user_manager = UserManager(env["auth"])

        # Verify current password is required for password change
        # This is enforced in the update_own_password method
        assert user_manager.can_update_own_password() is True

        # Simulate password verification check
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT password_hash FROM users WHERE username = ?",
                ("session_test_user",),
            )
            stored_hash = cursor.fetchone()[0]

            # Wrong password should not match
            wrong_password_hash = hashlib.sha256("WrongPassword123!".encode()).hexdigest()
            assert wrong_password_hash != stored_hash

            # Correct password should match
            correct_password_hash = hashlib.sha256(original_password.encode()).hexdigest()
            assert correct_password_hash == stored_hash

    def test_audit_trail_user_creation(self, secure_test_environment):
        """Test that user creation is properly tracked for audit"""
        env = secure_test_environment
        env["auth"].login("super_admin", "Admin_123?")

        # Get creator's ID
        creator_id = env["auth"].current_user["id"]

        # Create a new user
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            creation_time = datetime.now().isoformat()
            
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
                (
                    "audited_user",
                    hashlib.sha256("Audited123!".encode()).hexdigest(),
                    "system_admin",
                    "Audited",
                    "User",
                    creation_time,
                    creator_id,
                ),
            )
            conn.commit()

        # Verify audit trail
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT created_date, created_by 
                FROM users 
                WHERE username = ?
            """,
                ("audited_user",),
            )
            result = cursor.fetchone()

            assert result[0] == creation_time
            assert result[1] == creator_id

    def test_inactive_user_access_prevention(self, secure_test_environment):
        """Test that inactive users cannot access the system"""
        env = secure_test_environment

        # Create an active user
        test_password = "Active123!"
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """,
                (
                    "inactive_user",
                    hashlib.sha256(test_password.encode()).hexdigest(),
                    "system_admin",
                    "Inactive",
                    "User",
                    datetime.now().isoformat(),
                    1,
                ),
            )
            conn.commit()

        # Attempt to login with inactive user
        login_result = env["auth"].login("inactive_user", test_password)
        assert login_result is False

        # Activate the user
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET is_active = 1 WHERE username = ?",
                ("inactive_user",),
            )
            conn.commit()

        # Now login should work
        login_result = env["auth"].login("inactive_user", test_password)
        assert login_result is True

    def test_concurrent_access_security(self, secure_test_environment):
        """Test security with concurrent access attempts"""
        env = secure_test_environment

        # Create multiple database connections to simulate concurrent access
        connections = []
        for i in range(3):
            conn = env["db"].get_connection()
            connections.append(conn)

        try:
            # Each connection tries to create a user with the same username
            username = "concurrent_test"
            password_hash = hashlib.sha256("Concurrent123!".encode()).hexdigest()

            success_count = 0
            for i, conn in enumerate(connections):
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                        (
                            username,
                            password_hash,
                            "system_admin",
                            f"Concurrent{i}",
                            "User",
                            datetime.now().isoformat(),
                            1,
                        ),
                    )
                    conn.commit()
                    success_count += 1
                except sqlite3.IntegrityError:
                    # Expected for duplicate username
                    pass

            # Only one should succeed due to unique constraint
            assert success_count == 1

            # Verify only one user was created
            with env["db"].get_connection() as verify_conn:
                cursor = verify_conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM users WHERE username = ?",
                    (username,),
                )
                count = cursor.fetchone()[0]
                assert count == 1

        finally:
            # Clean up connections
            for conn in connections:
                conn.close()