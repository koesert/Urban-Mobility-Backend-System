import hashlib
from data.db_context import DatabaseContext


class AuthenticationService:
    def __init__(self):
        self.db = DatabaseContext()
        self.current_user = None

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
                self.current_user = {
                    "id": user_data[0],
                    "username": user_data[1],
                    "role": user_data[2],
                    "first_name": user_data[3],
                    "last_name": user_data[4],
                }
                return True
            return False

    def logout(self):
        """Clear current user session"""
        self.current_user = None

    def is_logged_in(self):
        """Check if user is logged in"""
        return self.current_user is not None

    def get_current_user(self):
        """Get current logged in user"""
        return self.current_user
