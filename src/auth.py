import hashlib
from data.db_context import DatabaseContext
from data.secure_logger import SecureLogger
from data.encryption import encrypt_field, decrypt_field


class AuthenticationService:
    def __init__(self):
        self.db = DatabaseContext()
        self.current_user = None
        self.logger = SecureLogger()
        self.failed_attempts = {}

    def _log_failed_attempt(self, username):
        # Use lowercase username for failed attempts tracking
        username_lower = username.lower()
        self.failed_attempts[username_lower] = self.failed_attempts.get(
            username_lower, 0) + 1
        is_suspicious = self.failed_attempts[username_lower] >= 3

        self.logger.log_activity(
            username=username,
            activity="Failed login attempt",
            details=f"Attempt count: {self.failed_attempts[username_lower]}",
            suspicious=is_suspicious
        )

    def login(self, username, password):
        """Authenticate user and set current_user"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Hash the provided password
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            # Get all active users to check against
            cursor.execute(
                """
                SELECT id, username, role, first_name, last_name, username_encrypted
                FROM users
                WHERE password_hash = ? AND is_active = 1
                """,
                (password_hash,),
            )

            users = cursor.fetchall()
            
            # Find matching user by decrypting and comparing usernames (case-insensitive)
            user_data = None
            for user in users:
                try:
                    # Decrypt the stored username
                    stored_username = decrypt_field(user[5])
                    # Compare case-insensitively
                    if stored_username.lower() == username.lower():
                        user_data = user
                        break
                except Exception as e:
                    # If decryption fails, skip this user
                    continue

            if user_data:
                # Reset failed attempts on successful login
                self.failed_attempts.pop(username.lower(), None)

                self.current_user = {
                    "id": user_data[0],
                    "username": user_data[1],  # Store original username for display
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
                if user_data[2] in ["super_admin", "system_admin"]:
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