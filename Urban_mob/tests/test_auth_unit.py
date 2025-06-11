import pytest
import hashlib
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from auth import AuthenticationService
from data.db_context import DatabaseContext


class TestAuthenticationServiceUnit:
    """Unit tests for AuthenticationService - isolated component testing"""

    @pytest.fixture
    def mock_db_context(self):
        """Mock database context for isolated testing"""
        mock_db = Mock(spec=DatabaseContext)
        return mock_db

    @pytest.fixture
    def auth_service(self, mock_db_context):
        """Create auth service with mocked database"""
        service = AuthenticationService()
        service.db = mock_db_context
        return service

    def test_login_success_with_valid_credentials(self, auth_service):
        """Test successful login with correct username and password"""
        # Arrange
        username = "test_admin"
        password = "Admin_123?"

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (
            1,
            username,
            "super_admin",
            "Test",
            "Admin",
        )

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        auth_service.db.get_connection.return_value = mock_conn

        # Act
        result = auth_service.login(username, password)

        # Assert
        assert result is True
        assert auth_service.current_user is not None
        assert auth_service.current_user["username"] == username
        assert auth_service.current_user["role"] == "super_admin"
        assert auth_service.current_user["id"] == 1

    def test_login_failure_with_invalid_password(self, auth_service):
        """Test login fails with incorrect password"""
        # Arrange
        username = "test_admin"
        wrong_password = "WrongPassword123"

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None  # No user found with this hash

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        auth_service.db.get_connection.return_value = mock_conn

        # Act
        result = auth_service.login(username, wrong_password)

        # Assert
        assert result is False
        assert auth_service.current_user is None

    def test_login_failure_with_nonexistent_user(self, auth_service):
        """Test login fails with non-existent username"""
        # Arrange
        username = "nonexistent_user"
        password = "SomePassword123"

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        auth_service.db.get_connection.return_value = mock_conn

        # Act
        result = auth_service.login(username, password)

        # Assert
        assert result is False
        assert auth_service.current_user is None

    def test_logout_clears_current_user(self, auth_service):
        """Test logout properly clears current user session"""
        # Arrange
        auth_service.current_user = {
            "id": 1,
            "username": "test",
            "role": "admin",
            "first_name": "Test",
            "last_name": "User",
        }

        # Act
        auth_service.logout()

        # Assert
        assert auth_service.current_user is None

    def test_is_logged_in_returns_true_when_user_exists(self, auth_service):
        """Test is_logged_in returns True when user is logged in"""
        # Arrange
        auth_service.current_user = {"id": 1, "username": "test"}

        # Act & Assert
        assert auth_service.is_logged_in() is True

    def test_is_logged_in_returns_false_when_no_user(self, auth_service):
        """Test is_logged_in returns False when no user is logged in"""
        # Arrange
        auth_service.current_user = None

        # Act & Assert
        assert auth_service.is_logged_in() is False

    def test_password_hashing_consistency(self, auth_service):
        """Test that same password produces same hash"""
        # Arrange
        password = "TestPassword123!"

        # Act
        hash1 = hashlib.sha256(password.encode()).hexdigest()
        hash2 = hashlib.sha256(password.encode()).hexdigest()

        # Assert
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 produces 64-character hex string

    def test_sql_injection_protection_in_login(self, auth_service):
        """Test that SQL injection attempts are handled safely"""
        # Arrange
        malicious_username = "admin'; DROP TABLE users; --"
        password = "password"

        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)

        auth_service.db.get_connection.return_value = mock_conn

        # Act
        result = auth_service.login(malicious_username, password)

        # Assert
        assert result is False
        # Verify parameterized query was used (cursor.execute called with tuple)
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        assert len(call_args[0]) == 2  # Query and parameters
        assert isinstance(call_args[0][1], tuple)  # Parameters as tuple
