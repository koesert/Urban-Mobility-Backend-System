from models.super_administrator import SuperAdministrator
from models.system_administrator import SystemAdministrator
from models.service_engineer import ServiceEngineer


class RoleManager:
    def __init__(self, auth_service):
        self.auth = auth_service
        self.roles = {
            "super_admin": SuperAdministrator(auth_service),
            "system_admin": SystemAdministrator(auth_service),
            "service_engineer": ServiceEngineer(auth_service),
        }

    def get_current_role_handler(self):
        """Get the role handler for current user"""
        if not self.auth.current_user:
            return None
        return self.roles.get(self.auth.current_user["role"])

    def check_permission(self, permission):
        """Check if current user has specific permission"""
        role_handler = self.get_current_role_handler()
        if not role_handler:
            return False
        return role_handler.can_access(permission)

    def get_available_permissions(self):
        """Get all permissions for current user"""
        role_handler = self.get_current_role_handler()
        if not role_handler:
            return []
        return role_handler.get_permissions()
