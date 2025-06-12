import pytest
from unittest.mock import Mock
from models.super_administrator import SuperAdministrator
from models.system_administrator import SystemAdministrator
from models.service_engineer import ServiceEngineer


class TestRolePermissionsUnit:
    """Unit tests for individual role permission checking"""

    @pytest.fixture
    def mock_auth_service(self):
        """Mock authentication service for role testing"""
        mock_auth = Mock()
        mock_auth.db = Mock()
        return mock_auth

    def test_super_admin_has_all_permissions(self, mock_auth_service):
        """Test Super Administrator has access to all system functions"""
        # Arrange
        mock_auth_service.current_user = {
            "id": 1,
            "role": "super_admin",
            "username": "super_admin",
        }
        super_admin = SuperAdministrator(mock_auth_service)

        # Act & Assert
        expected_permissions = [
            "manage_system_administrators",
            "manage_service_engineers",
            "manage_travelers",
            "manage_scooters",
            "view_logs",
            "create_backup",
            "restore_backup",
            "generate_restore_codes",
            "revoke_restore_codes",
        ]

        for permission in expected_permissions:
            assert super_admin.can_access(permission) is True

    def test_system_admin_has_correct_permissions(self, mock_auth_service):
        """Test System Administrator has correct subset of permissions"""
        # Arrange
        mock_auth_service.current_user = {
            "id": 2,
            "role": "system_admin",
            "username": "sys_admin",
        }
        sys_admin = SystemAdministrator(mock_auth_service)

        # Act & Assert - Test allowed permissions
        allowed_permissions = [
            "manage_service_engineers",
            "manage_travelers",
            "manage_scooters",
            "view_logs",
            "create_backup",
            "use_restore_code",
        ]

        for permission in allowed_permissions:
            assert sys_admin.can_access(permission) is True

        # Test denied permissions
        denied_permissions = [
            "manage_system_administrators",
            "generate_restore_codes",
            "revoke_restore_codes",
        ]

        for permission in denied_permissions:
            assert sys_admin.can_access(permission) is False

    def test_service_engineer_has_minimal_permissions(self, mock_auth_service):
        """Test Service Engineer has only basic permissions"""
        # Arrange
        mock_auth_service.current_user = {
            "id": 3,
            "role": "service_engineer",
            "username": "engineer",
        }
        engineer = ServiceEngineer(mock_auth_service)

        # Act & Assert - Test allowed permissions
        allowed_permissions = [
            "update_scooter_info",
            "search_scooters",
            "update_own_password",
        ]

        for permission in allowed_permissions:
            assert engineer.can_access(permission) is True

        # Test denied permissions
        denied_permissions = [
            "manage_system_administrators",
            "manage_service_engineers",
            "manage_travelers",
            "manage_scooters",  # Can update but not fully manage
            "view_logs",
            "create_backup",
        ]

        for permission in denied_permissions:
            assert engineer.can_access(permission) is False

    def test_role_access_denied_when_not_logged_in(self, mock_auth_service):
        """Test all roles deny access when no user is logged in"""
        # Arrange
        mock_auth_service.current_user = None

        super_admin = SuperAdministrator(mock_auth_service)
        sys_admin = SystemAdministrator(mock_auth_service)
        engineer = ServiceEngineer(mock_auth_service)

        # Act & Assert
        test_permission = "manage_scooters"

        assert super_admin.can_access(test_permission) is False
        assert sys_admin.can_access(test_permission) is False
        assert engineer.can_access(test_permission) is False

    def test_role_access_denied_for_wrong_role(self, mock_auth_service):
        """Test role denies access when user has different role"""
        # Arrange - User with system_admin role trying to access super_admin functions
        mock_auth_service.current_user = {
            "id": 2,
            "role": "system_admin",
            "username": "sys_admin",
        }
        super_admin = SuperAdministrator(mock_auth_service)

        # Act & Assert
        assert super_admin.can_access("manage_system_administrators") is False
