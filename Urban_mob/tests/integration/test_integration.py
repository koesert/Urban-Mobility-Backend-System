import pytest
import tempfile
import os
import sqlite3
import gc
from auth import AuthenticationService
from utils import RoleManager
from data.db_context import DatabaseContext


class TestRBACIntegration:
    """Integration tests for complete RBAC workflows"""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for integration testing with proper cleanup"""
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
    def db_context(self, temp_db_path):
        """Create database context with temporary database"""
        db = DatabaseContext(temp_db_path)
        return db

    @pytest.fixture
    def auth_service(self, db_context):
        """Create authentication service with real database"""
        service = AuthenticationService()
        service.db = db_context
        return service

    @pytest.fixture
    def role_manager(self, auth_service):
        """Create role manager with real auth service"""
        return RoleManager(auth_service)

    def test_complete_super_admin_login_flow(self, auth_service, role_manager):
        """Test complete login flow for super administrator"""
        # Act - Login with hard-coded super admin credentials
        login_result = auth_service.login("super_admin", "Admin_123?")

        # Assert - Login successful
        assert login_result is True
        assert auth_service.is_logged_in() is True

        current_user = auth_service.get_current_user()
        assert current_user is not None
        assert current_user["username"] == "super_admin"
        assert current_user["role"] == "super_admin"

        # Assert - Has all permissions
        assert role_manager.check_permission("manage_system_administrators") is True
        assert role_manager.check_permission("manage_service_engineers") is True
        assert role_manager.check_permission("view_logs") is True
        assert role_manager.check_permission("create_backup") is True

    def test_user_creation_and_login_flow(self, auth_service, role_manager):
        """Test creating new user and logging in"""
        # Arrange - Create a new system administrator
        with auth_service.db.get_connection() as conn:
            cursor = conn.cursor()
            import hashlib
            from datetime import datetime

            password_hash = hashlib.sha256("NewAdmin123!".encode()).hexdigest()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    "new_admin",
                    password_hash,
                    "system_admin",
                    "New",
                    "Admin",
                    datetime.now().isoformat(),
                    1,
                ),
            )
            conn.commit()

        # Act - Login with new user
        login_result = auth_service.login("new_admin", "NewAdmin123!")

        # Assert - Login successful
        assert login_result is True

        current_user = auth_service.get_current_user()
        assert current_user["username"] == "new_admin"
        assert current_user["role"] == "system_admin"

        # Assert - Has system admin permissions but not super admin permissions
        assert role_manager.check_permission("manage_service_engineers") is True
        assert role_manager.check_permission("manage_travelers") is True
        assert role_manager.check_permission("manage_system_administrators") is False

    def test_role_based_menu_access_simulation(self, auth_service, role_manager):
        """Test simulated menu access based on roles"""
        # Test Super Admin menu access
        auth_service.login("super_admin", "Admin_123?")
        permissions = role_manager.get_available_permissions()

        super_admin_menu_items = [
            item
            for item in [
                ("manage_system_administrators", "Manage System Administrators"),
                ("manage_service_engineers", "Manage Service Engineers"),
                ("manage_travelers", "Manage Travelers"),
                ("manage_scooters", "Manage Scooters"),
                ("view_logs", "View System Logs"),
                ("create_backup", "Create Backup"),
            ]
            if item[0] in permissions
        ]

        # Super admin should see all menu items
        assert len(super_admin_menu_items) == 6

        # Logout and test with different role
        auth_service.logout()

        # Create and login as service engineer
        with auth_service.db.get_connection() as conn:
            cursor = conn.cursor()
            import hashlib
            from datetime import datetime

            password_hash = hashlib.sha256("Engineer123!".encode()).hexdigest()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    "test_engineer",
                    password_hash,
                    "service_engineer",
                    "Test",
                    "Engineer",
                    datetime.now().isoformat(),
                    1,
                ),
            )
            conn.commit()

        auth_service.login("test_engineer", "Engineer123!")
        permissions = role_manager.get_available_permissions()

        # Service engineer should only have specific permissions
        engineer_permissions = role_manager.get_available_permissions()
        assert "update_selected_scooter_info" in engineer_permissions
        assert "manage_system_administrators" not in engineer_permissions

        expected_engineer_permissions = {
            "search_scooters",
            "manage_scooters",
            "update_selected_scooter_info",
            "update_own_password",
        }
        assert set(engineer_permissions) == expected_engineer_permissions

    def test_session_management_integration(self, auth_service):
        """Test session management across login/logout cycles"""
        # Test multiple login/logout cycles
        for _ in range(3):
            # Login
            result = auth_service.login("super_admin", "Admin_123?")
            assert result is True
            assert auth_service.is_logged_in() is True

            # Verify user data
            user = auth_service.get_current_user()
            assert user is not None
            assert user["username"] == "super_admin"

            # Logout
            auth_service.logout()
            assert auth_service.is_logged_in() is False
            assert auth_service.get_current_user() is None

    def test_database_role_constraints_integration(self, auth_service):
        """Test database-level role constraints"""
        with auth_service.db.get_connection() as conn:
            cursor = conn.cursor()

            # Test that invalid role is rejected by database constraint
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, role, first_name, last_name, created_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        "invalid_user",
                        "hash",
                        "invalid_role",
                        "Test",
                        "User",
                        "2024-01-01",
                    ),
                )
                conn.commit()

    def test_concurrent_user_sessions_simulation(self, temp_db_path):
        """Test simulation of concurrent user sessions"""
        # Create two separate auth services (simulating different sessions)
        db1 = DatabaseContext(temp_db_path)
        auth1 = AuthenticationService()
        auth1.db = db1

        db2 = DatabaseContext(temp_db_path)
        auth2 = AuthenticationService()
        auth2.db = db2

        # Login different users in different "sessions"
        result1 = auth1.login("super_admin", "Admin_123?")
        assert result1 is True

        # Create second user for second session
        with auth2.db.get_connection() as conn:
            cursor = conn.cursor()
            import hashlib
            from datetime import datetime

            password_hash = hashlib.sha256("Admin456!".encode()).hexdigest()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    "admin2",
                    password_hash,
                    "system_admin",
                    "Admin",
                    "Two",
                    datetime.now().isoformat(),
                    1,
                ),
            )
            conn.commit()

        result2 = auth2.login("admin2", "Admin456!")
        assert result2 is True

        # Verify both sessions are independent
        # Verify both sessions are independent
        user1 = auth1.get_current_user()
        user2 = auth2.get_current_user()

        assert user1 is not None, "First user should not be None"
        assert user2 is not None, "Second user should not be None"

        assert user1.get("username") == "super_admin"
        assert user2.get("username") == "admin2"
        assert user1.get("role") == "super_admin"
        assert user2.get("role") == "system_admin"
        # Logout one session shouldn't affect the other
        auth1.logout()
        assert auth1.is_logged_in() is False
        assert auth2.is_logged_in() is True
