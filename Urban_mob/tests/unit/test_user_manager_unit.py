import pytest
import hashlib
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
from managers.user_manager import UserManager
from cryptography.fernet import InvalidToken


class TestUserManagerUnit:
    """Unit tests for UserManager - isolated component testing"""

    @pytest.fixture
    def mock_auth_service(self):
        """Mock authentication service"""
        mock_auth = Mock()
        mock_auth.db = Mock()
        mock_auth.current_user = {
            "id": 1,
            "username": "super_admin",
            "role": "super_admin",
            "first_name": "Super",
            "last_name": "Admin",
        }
        return mock_auth

    @pytest.fixture
    def user_manager(self, mock_auth_service):
        """Create UserManager with mocked dependencies"""
        return UserManager(mock_auth_service)

    def test_initialization(self, mock_auth_service):
        """Test UserManager initialization"""
        # Act
        manager = UserManager(mock_auth_service)

        # Assert
        assert manager.auth == mock_auth_service
        assert manager.db == mock_auth_service.db

    def test_can_manage_users_super_admin_can_manage_all(self, user_manager):
        """Test super admin can manage all user types"""
        # Arrange
        user_manager.auth.current_user["role"] = "super_admin"

        # Act & Assert
        assert user_manager.can_manage_users("super_admin") is True
        assert user_manager.can_manage_users("system_admin") is True
        assert user_manager.can_manage_users("service_engineer") is True

    def test_can_manage_users_system_admin_limited_access(self, user_manager):
        """Test system admin can only manage service engineers"""
        # Arrange
        user_manager.auth.current_user["role"] = "system_admin"

        # Act & Assert
        assert user_manager.can_manage_users("super_admin") is False
        assert user_manager.can_manage_users("system_admin") is False
        assert user_manager.can_manage_users("service_engineer") is True

    def test_can_manage_users_service_engineer_no_access(self, user_manager):
        """Test service engineer cannot manage any users"""
        # Arrange
        user_manager.auth.current_user["role"] = "service_engineer"

        # Act & Assert
        assert user_manager.can_manage_users("super_admin") is False
        assert user_manager.can_manage_users("system_admin") is False
        assert user_manager.can_manage_users("service_engineer") is False

    def test_can_manage_users_no_current_user(self, user_manager):
        """Test returns False when no user is logged in"""
        # Arrange
        user_manager.auth.current_user = None

        # Act & Assert
        assert user_manager.can_manage_users("any_role") is False

    def test_can_update_own_password_when_logged_in(self, user_manager):
        """Test user can update password when logged in"""
        # Arrange
        user_manager.auth.is_logged_in.return_value = True

        # Act & Assert
        assert user_manager.can_update_own_password() is True

    def test_can_update_own_password_when_not_logged_in(self, user_manager):
        """Test user cannot update password when not logged in"""
        # Arrange
        user_manager.auth.is_logged_in.return_value = False

        # Act & Assert
        assert user_manager.can_update_own_password() is False

    def test_can_reset_user_password_authorized_roles(self, user_manager):
        """Test authorized roles can reset passwords"""
        # Test super admin
        user_manager.auth.current_user["role"] = "super_admin"
        assert user_manager.can_reset_user_password() is True

        # Test system admin
        user_manager.auth.current_user["role"] = "system_admin"
        assert user_manager.can_reset_user_password() is True

    def test_can_reset_user_password_unauthorized_roles(self, user_manager):
        """Test unauthorized roles cannot reset passwords"""
        # Test service engineer
        user_manager.auth.current_user["role"] = "service_engineer"
        assert user_manager.can_reset_user_password() is False

        # Test no user
        user_manager.auth.current_user = None
        assert user_manager.can_reset_user_password() is False

    @patch("builtins.input")
    @patch("builtins.print")
    def test_display_user_management_menu_authorized(self, mock_print, mock_input, user_manager):
        """Test menu display for authorized users"""
        # Arrange
        mock_input.return_value = "6"
        user_manager.auth.current_user["role"] = "super_admin"

        # Act
        result = user_manager.display_user_management_menu("system_admin")

        # Assert
        assert result == "6"
        mock_print.assert_any_call("\n--- MANAGE SYSTEM ADMINS ---")

    @patch("builtins.print")
    def test_display_user_management_menu_unauthorized_system_admin(self, mock_print, user_manager):
        """Test menu access denied for unauthorized system admin management"""
        # Arrange
        user_manager.auth.current_user["role"] = "system_admin"

        # Act
        result = user_manager.display_user_management_menu("system_admin")

        # Assert
        assert result is None
        mock_print.assert_called_with("Access denied: Only Super Administrators can manage System Administrators!")

    def test_view_users_with_role_filter(self, user_manager):
        """Test viewing users with role filter"""
        # Arrange
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            (2, "test_admin", "system_admin", "Test", "Admin", "2024-01-01T10:00:00", 1),
            (3, "test_admin2", "system_admin", "Test2", "Admin2", "2024-01-02T10:00:00", 1),
        ]

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        user_manager.db.get_connection.return_value = mock_conn

        # Act
        with patch("builtins.print"):
            user_manager.view_users("system_admin")

        # Assert
        mock_cursor.execute.assert_called_once()
        query = mock_cursor.execute.call_args[0][0]
        assert "WHERE role = ?" in query
        assert mock_cursor.execute.call_args[0][1] == ("system_admin",)

    def test_view_users_without_filter(self, user_manager):
        """Test viewing all users without filter"""
        # Arrange
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        user_manager.db.get_connection.return_value = mock_conn

        # Act
        with patch("builtins.print"):
            user_manager.view_users()

        # Assert
        mock_cursor.execute.assert_called_once()
        query = mock_cursor.execute.call_args[0][0]
        assert "WHERE" not in query

    def test_generate_temporary_password(self, user_manager):
        """Test temporary password generation"""
        # Act
        password = user_manager._generate_temporary_password()

        # Assert
        assert len(password) == 12
        assert any(c.isalpha() for c in password)
        assert any(c.isdigit() for c in password)
        assert any(c in "!@#$%^&*" for c in password)

    def test_generate_temporary_password_uniqueness(self, user_manager):
        """Test that generated passwords are unique"""
        # Act
        passwords = [user_manager._generate_temporary_password() for _ in range(10)]

        # Assert
        assert len(set(passwords)) == 10  # All passwords should be unique

    @patch("builtins.input")
    def test_get_unique_username_success(self, mock_input, user_manager):
        """Test getting unique username successfully"""
        # Arrange
        mock_input.return_value = "new_user"

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None  # Username doesn't exist

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        user_manager.db.get_connection.return_value = mock_conn

        # Act
        result = user_manager._get_unique_username()

        # Assert
        assert result == "new_user"

    @patch("builtins.input")
    def test_get_unique_username_already_exists(self, mock_input, user_manager):
        """Test handling existing username"""
        # Arrange
        mock_input.side_effect = ["existing_user", "y", "new_unique_user"]

        mock_cursor = Mock()
        # First call returns existing user, second call returns None
        mock_cursor.fetchone.side_effect = [("existing_id",), None]

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        user_manager.db.get_connection.return_value = mock_conn

        # Act
        with patch("builtins.print"):
            result = user_manager._get_unique_username()

        # Assert
        assert result == "new_unique_user"

    @patch("builtins.input")
    def test_get_required_input_success(self, mock_input, user_manager):
        """Test getting required input successfully"""
        # Arrange
        mock_input.return_value = "John"

        # Act
        result = user_manager._get_required_input("First Name")

        # Assert
        assert result == "John"

    @patch("builtins.input")
    def test_get_required_input_retry(self, mock_input, user_manager):
        """Test retry mechanism for required input"""
        # Arrange
        mock_input.side_effect = ["", "y", "John"]

        # Act
        with patch("builtins.print"):
            result = user_manager._get_required_input("First Name")

        # Assert
        assert result == "John"

    @patch("builtins.input")
    def test_get_new_password_success(self, mock_input, user_manager):
        """Test getting new password with validation"""
        # Arrange
        mock_input.side_effect = ["StrongPass123!", "StrongPass123!"]

        # Act
        result = user_manager._get_new_password()

        # Assert
        assert result == "StrongPass123!"

    @patch("builtins.input")
    def test_get_new_password_too_short(self, mock_input, user_manager):
        """Test password validation for length"""
        # Arrange
        mock_input.side_effect = ["short", "y", "ValidPassword123", "ValidPassword123"]

        # Act
        with patch("builtins.print"):
            result = user_manager._get_new_password()

        # Assert
        assert result == "ValidPassword123"

    @patch("builtins.input")
    def test_get_new_password_mismatch(self, mock_input, user_manager):
        """Test password confirmation mismatch"""
        # Arrange
        mock_input.side_effect = ["Password123", "DifferentPass", "y", "Password123", "Password123"]

        # Act
        with patch("builtins.print"):
            result = user_manager._get_new_password()

        # Assert
        assert result == "Password123"

    def test_get_user_by_id_success(self, user_manager):
        """Test getting user by ID successfully"""
        # Arrange
        expected_user = (2, "test_user", "system_admin", "Test", "User", "2024-01-01", 1)

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = expected_user

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        user_manager.db.get_connection.return_value = mock_conn

        # Act
        result = user_manager._get_user_by_id(2)

        # Assert
        assert result == expected_user

    def test_get_user_by_id_not_found(self, user_manager):
        """Test getting non-existent user by ID"""
        # Arrange
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        user_manager.db.get_connection.return_value = mock_conn

        # Act
        result = user_manager._get_user_by_id(999)

        # Assert
        assert result is None

    def test_get_user_by_id_database_error(self, user_manager):
        """Test handling database error when getting user"""
        # Arrange
        user_manager.db.get_connection.side_effect = Exception("Database error")

        # Act
        result = user_manager._get_user_by_id(1)

        # Assert
        assert result is None

    @patch("builtins.input")
    @patch("builtins.print")
    def test_add_user_complete_flow(self, mock_print, mock_input, user_manager):
        """Test complete add user flow"""
        # Arrange
        mock_input.side_effect = ["new_admin", "New", "Admin"]

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None  # Username doesn't exist

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_conn.commit = Mock()

        user_manager.db.get_connection.return_value = mock_conn

        # Mock password generation
        with patch.object(user_manager, '_generate_temporary_password', return_value='TempPass123!'):
            # Act
            user_manager.add_user("system_admin")

        # Assert
        mock_conn.commit.assert_called_once()
        
        # Verify the INSERT query was called
        insert_call = mock_cursor.execute.call_args_list[-1]
        query = insert_call[0][0]
        params = insert_call[0][1]
        
        assert "INSERT INTO users" in query
        assert params[0] == "new_admin"  # username
        assert params[2] == "system_admin"  # role
        assert params[3] == "New"  # first_name
        assert params[4] == "Last"  # last_name

    @patch("builtins.input")
    @patch("builtins.print")
    def test_delete_user_prevention_self_deletion(self, mock_print, mock_input, user_manager):
        """Test prevention of self-deletion"""
        # Arrange
        user_manager.auth.current_user["id"] = 1
        mock_input.return_value = "1"

        # Mock the _get_user_by_id to return current user
        with patch.object(user_manager, '_get_user_by_id', return_value=(1, "current_user", "super_admin", "Current", "User", "2024-01-01", 1)):
            with patch.object(user_manager, 'view_users'):
                # Act
                user_manager.delete_user("super_admin")

        # Assert
        mock_print.assert_any_call("You cannot delete your own account!")

    @patch("builtins.input")
    @patch("builtins.print")
    def test_delete_user_prevention_super_admin(self, mock_print, mock_input, user_manager):
        """Test prevention of super_admin deletion"""
        # Arrange
        mock_input.return_value = "1"

        # Mock the _get_user_by_id to return super_admin user
        with patch.object(user_manager, '_get_user_by_id', return_value=(1, "super_admin", "super_admin", "Super", "Admin", "2024-01-01", 1)):
            with patch.object(user_manager, 'view_users'):
                # Act
                user_manager.delete_user("super_admin")

        # Assert
        mock_print.assert_any_call("The super_admin account cannot be deleted!")

    @patch("builtins.input")
    def test_update_own_password_complete_flow(self, mock_input, user_manager):
        """Test complete password update flow"""
        # Arrange
        user_manager.auth.is_logged_in.return_value = True
        user_manager.auth.current_user = {"id": 1, "username": "test_user"}
        
        mock_input.side_effect = ["OldPass123", "NewPass123", "NewPass123"]

        # Mock cursor for password verification
        mock_cursor = Mock()
        old_password_hash = hashlib.sha256("OldPass123".encode()).hexdigest()
        mock_cursor.fetchone.return_value = (old_password_hash,)

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_conn.commit = Mock()

        user_manager.db.get_connection.return_value = mock_conn

        # Act
        with patch("builtins.print"):
            user_manager.update_own_password()

        # Assert
        # Should have two execute calls: one for SELECT, one for UPDATE
        assert mock_cursor.execute.call_count == 2
        
        # Verify UPDATE query
        update_call = mock_cursor.execute.call_args_list[1]
        query = update_call[0][0]
        assert "UPDATE users" in query
        assert "SET password_hash = ?" in query