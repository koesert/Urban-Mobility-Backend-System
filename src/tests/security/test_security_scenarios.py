import pytest
import tempfile
import os
import gc
from auth import AuthenticationService
from utils import RoleManager
from data.db_context import DatabaseContext


class TestSecurityScenarios:
    """Integration tests for security scenarios"""

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
    def setup_test_environment(self, temp_db_path):
        """Setup complete test environment"""
        db = DatabaseContext(temp_db_path)
        auth = AuthenticationService()
        auth.db = db
        role_manager = RoleManager(auth)

        return {"db": db, "auth": auth, "role_manager": role_manager}

    def test_privilege_escalation_protection(self, setup_test_environment):
        """Test that users cannot escalate privileges"""
        env = setup_test_environment

        # Create service engineer
        with env["db"].get_connection() as conn:
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
                    "engineer",
                    password_hash,
                    "service_engineer",
                    "Test",
                    "Engineer",
                    datetime.now().isoformat(),
                    1,
                ),
            )
            conn.commit()

        # Login as service engineer
        env["auth"].login("engineer", "Engineer123!")

        # Attempt to access admin functions - should be denied
        assert (
            env["role_manager"].check_permission("manage_system_administrators")
            is False
        )
        assert env["role_manager"].check_permission("manage_service_engineers") is False
        assert env["role_manager"].check_permission("view_logs") is False
        assert env["role_manager"].check_permission("create_backup") is False

        # Should only have engineer permissions
        permissions = env["role_manager"].get_available_permissions()
        expected_engineer_permissions = {
            "search_scooters",
            "manage_scooters",
            "update_selected_scooter_info",
            "update_own_password",
        }
        assert set(permissions) == expected_engineer_permissions

    def test_authentication_bypass_protection(self, setup_test_environment):
        """Test that authentication cannot be bypassed"""
        env = setup_test_environment

        # Test accessing role manager without authentication
        assert env["role_manager"].get_current_role_handler() is None
        assert env["role_manager"].check_permission("manage_scooters") is False
        assert env["role_manager"].get_available_permissions() == []

        # Reset and test proper authentication
        env["auth"].current_user = None
        env["auth"].login("super_admin", "Admin_123?")
        assert (
            env["role_manager"].check_permission("manage_system_administrators") is True
        )
