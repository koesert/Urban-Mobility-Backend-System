import hashlib
from data.db_context import DatabaseContext
from data.secure_logger import SecureLogger


class AuthenticationService:
    def __init__(self):
        self.db = DatabaseContext()
        self.current_user = None
        self.logger = SecureLogger()
        self.failed_attempts = {}

    def _log_failed_attempt(self, username):
        self.failed_attempts[username] = self.failed_attempts.get(
            username, 0) + 1
        is_suspicious = self.failed_attempts[username] >= 3

        self.logger.log_activity(
            username=username,
            activity="Failed login attempt",
            details=f"Attempt count: {self.failed_attempts[username]}",
            suspicious=is_suspicious
        )

    def login(self, username, password):
        """Authenticate user and set current_user"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Hash the provided password
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            cursor.execute(
                """
                SELECT id, username, role, first_name, last_name
                FROM users
                WHERE username = ? AND password_hash = ? AND is_active = 1
            """,
                (username, password_hash),
            )

            user_data = cursor.fetchone()

            if user_data:
                # Reset failed attempts on successful login
                self.failed_attempts.pop(username, None)

                self.current_user = {
                    "id": user_data[0],
                    "username": user_data[1],
                    "role": user_data[2],
                    "first_name": user_data[3],
                    "last_name": user_data[4],
                }

                # Log successful login
                self.logger.log_activity(
                    username=username,
                    activity="Logged in"
                )

                # Check for admin alerts
                if user_data[2] in ["System Administrator", "Super Administrator"]:
                    alerts = self.logger.check_suspicious_activity()
                    if alerts:
                        print("\nSecurity alerts:")
                        for alert in alerts:
                            print(
                                f"[{alert['date']} {alert['time']}] {alert['activity']} - {alert['details']}")

                return True

            # Log failed attempt
            self._log_failed_attempt(username)
            return False

    def logout(self):
        """Clear current user session"""
        if self.current_user:
            self.logger.log_activity(
                username=self.current_user["username"],
                activity="Logged out"
            )
        self.current_user = None

    def is_logged_in(self):
        """Check if user is logged in"""
        return self.current_user is not None

    def get_logs(self, role_manager):
        """Retrieve logs if user has the 'view_logs' permission"""
        if not self.current_user or not role_manager.check_permission("view_logs"):
            raise PermissionError("Insufficient privileges to view logs")
        return self.logger.read_logs(self.current_user["role"])

    def get_current_user(self):
        """Get current logged in user"""
        return self.current_user
