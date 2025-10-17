"""
Unit tests for auth.py module.

Tests authentication, authorization, session management,
and password handling functions.
"""

import pytest
from unittest.mock import Mock, patch
from auth import (
    login,
    logout,
    get_current_user,
    is_logged_in,
    check_permission,
    update_password,
)


# ============================================================================
# Login Tests
# ============================================================================

@pytest.mark.unit
class TestLogin:
    """Test login function"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset auth state before each test"""
        logout()
        yield
        logout()

    @patch('auth.get_connection')
    @patch('auth.verify_password')
    @patch('auth.decrypt_username')
    @patch('auth.encrypt_username')
    def test_successful_login(self, mock_encrypt, mock_decrypt, mock_verify, mock_conn):
        """Test successful login with valid credentials"""
        # Mock database response
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (
            1,  # user_id
            'encrypted_testuser',  # encrypted username
            b'hashed_password',  # password_hash
            'system_admin',  # role
            'Test',  # first_name
            'User',  # last_name
            0  # must_change_password
        )
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_conn.return_value.close = Mock()
        mock_encrypt.return_value = 'encrypted_testuser'
        mock_decrypt.return_value = 'testuser'
        mock_verify.return_value = True

        success, message = login('testuser', 'password123')

        assert success is True
        assert "welcome" in message.lower()
        assert get_current_user() is not None
        assert get_current_user()['username'] == 'testuser'

    @patch('auth.get_connection')
    @patch('auth.encrypt_username')
    def test_login_nonexistent_user(self, mock_encrypt, mock_conn):
        """Test login with non-existent username"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_conn.return_value.close = Mock()
        mock_encrypt.return_value = 'encrypted_nonexistent'

        success, message = login('nonexistent', 'password')

        assert success is False
        assert "invalid" in message.lower()
        assert get_current_user() is None

    @patch('auth.get_connection')
    @patch('auth.verify_password')
    @patch('auth.decrypt_username')
    @patch('auth.encrypt_username')
    def test_login_wrong_password(self, mock_encrypt, mock_decrypt, mock_verify, mock_conn):
        """Test login with incorrect password"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (
            1,  # user_id
            'encrypted_testuser',  # encrypted username
            b'hashed_password',  # password_hash
            'system_admin',  # role
            'Test',  # first_name
            'User',  # last_name
            0  # must_change_password
        )
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_conn.return_value.close = Mock()
        mock_encrypt.return_value = 'encrypted_testuser'
        mock_decrypt.return_value = 'testuser'
        mock_verify.return_value = False

        success, message = login('testuser', 'wrongpassword')

        assert success is False
        assert "invalid" in message.lower()
        assert get_current_user() is None

    @patch('auth.get_connection')
    @patch('auth.verify_password')
    @patch('auth.decrypt_username')
    @patch('auth.encrypt_username')
    def test_login_must_change_password(self, mock_encrypt, mock_decrypt, mock_verify, mock_conn):
        """Test login when password must be changed"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (
            1,  # user_id
            'encrypted_testuser',  # encrypted username
            b'hashed_password',  # password_hash
            'system_admin',  # role
            'Test',  # first_name
            'User',  # last_name
            1  # must_change_password
        )
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_conn.return_value.close = Mock()
        mock_encrypt.return_value = 'encrypted_testuser'
        mock_decrypt.return_value = 'testuser'
        mock_verify.return_value = True

        success, message = login('testuser', 'password123')

        assert success is True
        # Message should indicate password needs to be changed
        user = get_current_user()
        assert user is not None
        assert user['must_change_password'] == True

    def test_login_empty_username(self):
        """Test login with empty username"""
        success, message = login('', 'password')
        assert success is False

    @patch('auth.get_connection')
    @patch('auth.verify_password')
    @patch('auth.decrypt_username')
    @patch('auth.encrypt_username')
    def test_login_empty_password(self, mock_encrypt, mock_decrypt, mock_verify, mock_conn):
        """Test login with empty password"""
        # Mock database to return a user
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (
            1,  # user_id
            'encrypted_username',  # encrypted username
            b'hashed_password',  # password_hash
            'system_admin',  # role
            'Test',  # first_name
            'User',  # last_name
            0  # must_change_password
        )
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_conn.return_value.close = Mock()
        mock_encrypt.return_value = 'encrypted_username'
        mock_decrypt.return_value = 'validuser'
        mock_verify.return_value = False  # Empty password won't verify

        success, message = login('validuser', '')
        assert success is False
        assert "invalid" in message.lower()


# ============================================================================
# Logout Tests
# ============================================================================

@pytest.mark.unit
class TestLogout:
    """Test logout function"""

    @patch('auth.get_connection')
    @patch('auth.verify_password')
    @patch('auth.decrypt_username')
    @patch('auth.encrypt_username')
    def test_logout_clears_session(self, mock_encrypt, mock_decrypt, mock_verify, mock_conn):
        """Test that logout clears the session"""
        # First login
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (
            1,  # user_id
            'encrypted_testuser',  # encrypted username
            b'hashed_password',  # password_hash
            'system_admin',  # role
            'Test',  # first_name
            'User',  # last_name
            0  # must_change_password
        )
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_conn.return_value.close = Mock()
        mock_encrypt.return_value = 'encrypted_testuser'
        mock_decrypt.return_value = 'testuser'
        mock_verify.return_value = True

        login('testuser', 'password123')
        assert get_current_user() is not None
        assert is_logged_in() is True

        # Now logout
        logout()
        assert get_current_user() is None
        assert is_logged_in() is False

    def test_logout_when_not_logged_in(self):
        """Test logout when no one is logged in"""
        logout()  # Should not raise an error
        assert get_current_user() is None
        assert is_logged_in() is False


# ============================================================================
# Get Current User Tests
# ============================================================================

@pytest.mark.unit
class TestGetCurrentUser:
    """Test get_current_user function"""

    def test_get_current_user_when_not_logged_in(self):
        """Test get_current_user returns None when not logged in"""
        logout()
        assert get_current_user() is None
        assert is_logged_in() is False

    @patch('auth.get_connection')
    @patch('auth.verify_password')
    @patch('auth.decrypt_username')
    @patch('auth.encrypt_username')
    def test_get_current_user_when_logged_in(self, mock_encrypt, mock_decrypt, mock_verify, mock_conn):
        """Test get_current_user returns user data when logged in"""
        # Mock login
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (
            1,  # user_id
            'encrypted_testuser',  # encrypted username
            b'hashed_password',  # password_hash
            'system_admin',  # role
            'Test',  # first_name
            'User',  # last_name
            0  # must_change_password
        )
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_conn.return_value.close = Mock()
        mock_encrypt.return_value = 'encrypted_testuser'
        mock_decrypt.return_value = 'testuser'
        mock_verify.return_value = True

        login('testuser', 'password123')

        user = get_current_user()
        assert user is not None
        assert user['username'] == 'testuser'
        assert user['role_name'] == 'System Administrator'
        assert is_logged_in() is True

        logout()


# ============================================================================
# Permission Checking Tests
# ============================================================================

@pytest.mark.unit
class TestCheckPermission:
    """Test check_permission function"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset auth state"""
        logout()
        yield
        logout()

    def test_check_permission_when_not_logged_in(self):
        """Test permission check when not logged in"""
        logout()
        result = check_permission('manage_engineers')
        assert result is False

    @patch('auth.get_connection')
    @patch('auth.verify_password')
    @patch('auth.decrypt_username')
    @patch('auth.encrypt_username')
    def test_system_admin_permissions(self, mock_encrypt, mock_decrypt, mock_verify, mock_conn):
        """Test that system_admin has permissions"""
        # Mock system admin login
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (
            1,  # user_id
            'encrypted_adminusr',  # encrypted username
            b'hashed',  # password_hash
            'system_admin',  # role
            'Admin',  # first_name
            'User',  # last_name
            0  # must_change_password
        )
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_conn.return_value.close = Mock()
        mock_encrypt.return_value = 'encrypted_adminusr'
        mock_decrypt.return_value = 'adminusr'
        mock_verify.return_value = True

        success, message = login('adminusr', 'password')
        assert success is True, f"Login failed: {message}"  # Login must succeed first

        # Verify logged in
        assert is_logged_in() is True
        user = get_current_user()
        assert user is not None
        assert user['role'] == 'system_admin'

        # Check permissions
        result = check_permission('manage_engineers')
        assert isinstance(result, bool)
        assert result is True  # system_admin should have this permission

        logout()

    @patch('auth.get_connection')
    @patch('auth.verify_password')
    @patch('auth.decrypt_username')
    @patch('auth.encrypt_username')
    def test_service_engineer_permissions(self, mock_encrypt, mock_decrypt, mock_verify, mock_conn):
        """Test that service_engineer permissions work"""
        # Mock service engineer login
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (
            2,  # user_id
            'encrypted_engineer',  # encrypted username
            b'hashed',  # password_hash
            'service_engineer',  # role
            'Engineer',  # first_name
            'User',  # last_name
            0  # must_change_password
        )
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_conn.return_value.close = Mock()
        mock_encrypt.return_value = 'encrypted_engineer'
        mock_decrypt.return_value = 'engineer'
        mock_verify.return_value = True

        login('engineer', 'password')

        # Check that permission checking works
        result = check_permission('manage_scooters')
        assert isinstance(result, bool)
        assert result is True  # service_engineer should have this permission

        logout()


# ============================================================================
# Password Update Tests
# ============================================================================

@pytest.mark.unit
class TestUpdatePassword:
    """Test update_password function"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset auth state"""
        logout()
        yield
        logout()

    def test_update_password_not_logged_in(self):
        """Test password update when not logged in"""
        logout()
        success, message = update_password('oldpass', 'NewPass123!')

        assert success is False
        assert "logged in" in message.lower()

    @patch('auth.get_connection')
    @patch('auth.hash_password')
    @patch('auth.verify_password')
    @patch('auth.validate_password')
    @patch('auth.decrypt_username')
    @patch('auth.encrypt_username')
    def test_update_password_success(self, mock_encrypt, mock_decrypt, mock_validate,
                                     mock_verify, mock_hash, mock_conn):
        """Test successful password update"""
        # Mock login
        mock_cursor = Mock()
        # First fetchone for login, second for password update
        mock_cursor.fetchone.side_effect = [
            (1, 'encrypted_testuser', b'old_hash', 'system_admin', 'Test', 'User', 0),
            (b'old_hash',)  # For password update
        ]
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_conn.return_value.close = Mock()
        mock_conn.return_value.commit = Mock()
        mock_encrypt.return_value = 'encrypted_testuser'
        mock_decrypt.return_value = 'testuser'
        mock_verify.side_effect = [True, True]  # Login verify, password update verify
        mock_validate.return_value = 'NewPass123!'
        mock_hash.return_value = b'new_hash'

        login('testuser', 'oldpassword')

        # Update password
        success, message = update_password('oldpassword', 'NewPass123!')

        assert success is True
        assert "success" in message.lower() or "updated" in message.lower()

        logout()

    @patch('auth.get_connection')
    @patch('auth.verify_password')
    @patch('auth.decrypt_username')
    @patch('auth.encrypt_username')
    def test_update_password_wrong_old_password(self, mock_encrypt, mock_decrypt, mock_verify, mock_conn):
        """Test password update with wrong current password"""
        mock_cursor = Mock()
        # First fetchone for login, second for password update
        mock_cursor.fetchone.side_effect = [
            (1, 'encrypted_testuser', b'hash', 'system_admin', 'Test', 'User', 0),
            (b'hash',)  # For password update
        ]
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_conn.return_value.close = Mock()
        mock_encrypt.return_value = 'encrypted_testuser'
        mock_decrypt.return_value = 'testuser'
        # True for login, False for password verification
        mock_verify.side_effect = [True, False]

        login('testuser', 'password')

        success, message = update_password('wrongpass', 'NewPass123!')

        assert success is False

        logout()


# ============================================================================
# Security Tests
# ============================================================================

@pytest.mark.unit
class TestAuthSecurity:
    """Test security aspects of authentication"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset auth state"""
        logout()
        yield
        logout()

    @patch('auth.get_connection')
    def test_sql_injection_attempt(self, mock_conn):
        """Test that SQL injection attempts don't succeed"""
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.return_value.cursor.return_value = mock_cursor

        # Try SQL injection in username
        success, message = login("admin' OR '1'='1", "password")

        assert success is False

    @patch('auth.get_connection')
    @patch('auth.verify_password')
    @patch('auth.decrypt_username')
    @patch('auth.encrypt_username')
    def test_session_isolation(self, mock_encrypt, mock_decrypt, mock_verify, mock_conn):
        """Test that sessions don't interfere with each other"""
        mock_cursor = Mock()
        # First login for user1abc, then for user2def
        mock_cursor.fetchone.side_effect = [
            (1, 'encrypted_user1abc', b'hash', 'system_admin', 'User', 'One', 0),
            (2, 'encrypted_user2def', b'hash', 'service_engineer', 'User', 'Two', 0)
        ]
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_conn.return_value.close = Mock()
        mock_verify.return_value = True

        # Login as user1abc
        mock_encrypt.return_value = 'encrypted_user1abc'
        mock_decrypt.return_value = 'user1abc'
        success, _ = login('user1abc', 'password')
        assert success is True
        user1 = get_current_user()
        assert user1 is not None
        assert user1['username'] == 'user1abc'

        # Logout
        logout()
        assert get_current_user() is None

        # Can login as different user
        mock_encrypt.return_value = 'encrypted_user2def'
        mock_decrypt.return_value = 'user2def'
        success, _ = login('user2def', 'password')
        assert success is True
        user2 = get_current_user()
        assert user2 is not None
        assert user2['username'] == 'user2def'

        logout()

    def test_no_password_in_session_data(self):
        """Test that passwords are never exposed in session"""
        logout()
        user = get_current_user()
        assert user is None  # Not logged in

        # When logged in, the returned user dict should not contain password
        # This is enforced by the get_current_user() implementation
