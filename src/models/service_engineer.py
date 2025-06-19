class ServiceEngineer:
    def __init__(self, auth_service):
        self.auth = auth_service
        self.db = auth_service.db

    def get_permissions(self):
        """Define what Service Engineer can do"""
        return [
            "update_selected_scooter_info",  # Can only update, not add/delete
            "search_scooters",
            "update_own_password",
            "manage_scooters",
        ]

    def can_access(self, permission):
        """Check if current user has permission"""
        if (
            not self.auth.current_user
            or self.auth.current_user["role"] != "service_engineer"
        ):
            return False
        return permission in self.get_permissions()
