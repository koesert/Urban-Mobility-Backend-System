class SystemAdministrator:
    def __init__(self, auth_service):
        self.auth = auth_service
        self.db = auth_service.db

    def get_permissions(self):
        """Define what System Administrator can do"""
        return [
            "manage_service_engineers",
            "manage_travelers",
            "add_scooter",
            "delete_scooter",
            "view_logs",
            "create_backup",
            "use_restore_code",
            "update_own_password",
            "update_own_profile",
            "delete_own_account",
            "update_scooter_info",
            "manage_scooters",
        ]

    def can_access(self, permission):
        """Check if current user has permission"""
        if (
            not self.auth.current_user
            or self.auth.current_user["role"] != "system_admin"
        ):
            return False
        return permission in self.get_permissions()
