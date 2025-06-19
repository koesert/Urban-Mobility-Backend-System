import pytest
from unittest.mock import Mock
from utils import RoleManager


class TestRoleManagerUnit:
    """Unit tests for RoleManager functionality"""

    @pytest.fixture
    def mock_auth_service(self):
        """Mock authentication service"""
        mock_auth = Mock()
        mock_auth.db = Mock()
        return mock_auth

    @pytest.fixture
    def role_manager(self, mock_auth_service):
        """Create role manager with mocked auth service"""
        return RoleManager(mock_auth_service)

    def test_get_current_role_handler_returns_correct_handler(
        self, role_manager, mock_auth_service
    ):
        """Test role manager returns correct handler for current user role"""
        # Arrange
        mock_auth_service.current_user = {"role": "super_admin"}

        # Act
        handler = role_manager.get_current_role_handler()

        # Assert
        assert handler is not None
        assert handler.__class__.__name__ == "SuperAdministrator"

    def test_get_current_role_handler_returns_none_when_no_user(
        self, role_manager, mock_auth_service
    ):
        """Test role manager returns None when no user logged in"""
        # Arrange
        mock_auth_service.current_user = None

        # Act
        handler = role_manager.get_current_role_handler()

        # Assert
        assert handler is None

    def test_check_permission_returns_true_for_valid_permission(
        self, role_manager, mock_auth_service
    ):
        """Test permission check returns True for valid user permission"""
        # Arrange
        mock_auth_service.current_user = {"role": "super_admin"}

        # Act
        result = role_manager.check_permission("manage_scooters")

        # Assert
        assert result is True

    def test_check_permission_returns_false_for_invalid_permission(
        self, role_manager, mock_auth_service
    ):
        """Test permission check returns False for invalid permission"""
        # Arrange
        mock_auth_service.current_user = {"role": "service_engineer"}

        # Act
        result = role_manager.check_permission("manage_system_administrators")

        # Assert
        assert result is False

    def test_get_available_permissions_returns_correct_list(
        self, role_manager, mock_auth_service
    ):
        """Test getting available permissions for current user"""
        # Arrange
        mock_auth_service.current_user = {"role": "service_engineer"}

        # Act
        permissions = role_manager.get_available_permissions()

        # Assert
        expected_permissions = [
            "search_scooters",
            "manage_scooters",
            "update_selected_scooter_info",
            "update_own_password",
        ]
        assert set(permissions) == set(expected_permissions)
