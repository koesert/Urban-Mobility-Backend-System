class SuperAdministrator:
    def __init__(self, auth_service):
        self.auth = auth_service
        self.db = auth_service.db

    def get_permissions(self):
        """Define what Super Administrator can do"""
        return [
            "manage_system_administrators",
            "manage_service_engineers",
            "manage_travelers",
            "manage_scooters",
            "view_logs",
            "create_backup",
            "restore_backup",
            "generate_restore_codes",
            "revoke_restore_codes",
            "update_own_password",
        ]

    def can_access(self, permission):
        """Check if current user has permission"""
        if (
            not self.auth.current_user
            or self.auth.current_user["role"] != "super_admin"
        ):
            return False
        return permission in self.get_permissions()
