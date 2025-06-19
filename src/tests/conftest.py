import pytest
from unittest.mock import patch
import tempfile
import os
import gc
from cryptography.fernet import Fernet


@pytest.fixture(scope="session")
def test_database():
    """Session-scoped test database"""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    yield db_path

    # Enhanced cleanup
    gc.collect()
    for i in range(5):
        try:
            if os.path.exists(db_path):
                os.unlink(db_path)
            break
        except (PermissionError, FileNotFoundError):
            if i == 4:
                pass  # Give up silently
            else:
                import time

                time.sleep(0.1)


@pytest.fixture(scope="session")
def test_encryption_key():
    """Session-scoped test encryption key"""
    key_fd, key_path = tempfile.mkstemp(suffix=".key")
    os.close(key_fd)

    # Generate a test key
    key = Fernet.generate_key()
    with open(key_path, "wb") as f:
        f.write(key)

    yield key_path

    # Cleanup
    if os.path.exists(key_path):
        os.unlink(key_path)


@pytest.fixture
def temp_database():
    """Function-scoped temporary database for isolated tests"""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    yield db_path

    # Enhanced cleanup
    gc.collect()
    for i in range(5):
        try:
            if os.path.exists(db_path):
                os.unlink(db_path)
            break
        except (PermissionError, FileNotFoundError):
            if i == 4:
                pass  # Give up silently
            else:
                import time

                time.sleep(0.1)


@pytest.fixture
def temp_encryption_key():
    """Function-scoped temporary encryption key for isolated tests"""
    key_fd, key_path = tempfile.mkstemp(suffix=".key")
    os.close(key_fd)

    # Generate a test key
    key = Fernet.generate_key()
    with open(key_path, "wb") as f:
        f.write(key)

    yield key_path

    # Cleanup
    if os.path.exists(key_path):
        os.unlink(key_path)


@pytest.fixture(autouse=True)
def reset_auth_state():
    """Reset authentication state between tests"""
    yield
    # Cleanup any global state if needed


@pytest.fixture
def patch_encryption_key_path():
    """Patch the encryption key path for testing"""

    def _patch_key_path(key_path):
        return patch("data.encryption.FERNET_KEY_PATH", key_path)

    return _patch_key_path


@pytest.fixture
def mock_user_input():
    """Mock user input for interactive tests"""

    def _mock_input(inputs):
        """
        Returns a context manager that mocks input() calls

        Args:
            inputs: List of strings to return for each input() call
        """
        return patch("builtins.input", side_effect=inputs)

    return _mock_input


@pytest.fixture
def suppress_print():
    """Suppress print statements during tests"""
    return patch("builtins.print")


@pytest.fixture
def test_traveler_data():
    """Standard test traveler data for tests"""
    return {
        "customer_id": "CUST000001",
        "first_name": "Test",
        "last_name": "User",
        "birthday": "01-01-1990",
        "gender": "Male",
        "street_name": "Test Street",
        "house_number": "123",
        "zip_code": "1234AB",
        "city": "Amsterdam",
        "email": "test@example.com",
        "mobile_phone": "+31 6 12345678",
        "driving_license": "TU1234567",
        "registration_date": "2024-01-01T10:00:00",
    }


@pytest.fixture
def multiple_test_travelers():
    """Multiple test travelers for bulk testing"""
    return [
        {
            "customer_id": "CUST000001",
            "first_name": "Alice",
            "last_name": "Johnson",
            "birthday": "15-05-1990",
            "gender": "Female",
            "street_name": "Main Street",
            "house_number": "1",
            "zip_code": "1000AA",
            "city": "Amsterdam",
            "email": "alice@example.com",
            "mobile_phone": "+31 6 11111111",
            "driving_license": "AJ1111111",
            "registration_date": "2024-01-01T10:00:00",
        },
        {
            "customer_id": "CUST000002",
            "first_name": "Bob",
            "last_name": "Smith",
            "birthday": "20-08-1985",
            "gender": "Male",
            "street_name": "Second Street",
            "house_number": "2",
            "zip_code": "2000BB",
            "city": "Rotterdam",
            "email": "bob@example.com",
            "mobile_phone": "+31 6 22222222",
            "driving_license": "BS2222222",
            "registration_date": "2024-01-01T11:00:00",
        },
        {
            "customer_id": "CUST000003",
            "first_name": "Carol",
            "last_name": "Williams",
            "birthday": "10-12-1995",
            "gender": "Female",
            "street_name": "Third Avenue",
            "house_number": "3A",
            "zip_code": "3000CC",
            "city": "Utrecht",
            "email": "carol@example.com",
            "mobile_phone": "+31 6 33333333",
            "driving_license": "CW3333333",
            "registration_date": "2024-01-01T12:00:00",
        },
    ]


@pytest.fixture
def authorized_user_roles():
    """List of roles authorized to manage travelers"""
    return ["super_admin", "system_admin"]


@pytest.fixture
def unauthorized_user_roles():
    """List of roles not authorized to manage travelers"""
    return ["service_engineer", "invalid_role"]


# Pytest configuration for better test output
def pytest_configure(config):
    """Configure pytest markers and settings"""
    config.addinivalue_line("markers", "unit: Unit tests for isolated components")
    config.addinivalue_line(
        "markers", "integration: Integration tests with real database"
    )
    config.addinivalue_line("markers", "security: Security-focused tests")
    config.addinivalue_line("markers", "slow: Tests that may take longer to run")


# Performance monitoring fixture
@pytest.fixture
def performance_monitor():
    """Monitor test performance"""
    import time

    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def duration(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

        def assert_duration_under(self, max_seconds):
            assert (
                self.duration < max_seconds
            ), f"Test took {self.duration}s, expected under {max_seconds}s"

    return PerformanceMonitor()


# Custom assertion helpers
class TravelersTestHelpers:
    """Helper methods for travelers testing"""

    @staticmethod
    def assert_traveler_data_matches(
        actual_traveler, expected_data, encrypted_fields=None
    ):
        """Assert that traveler data matches expected values"""
        if encrypted_fields is None:
            encrypted_fields = ["email", "mobile_phone", "driving_license"]

        # Map tuple indices to field names for database results
        field_mapping = {
            0: "id",
            1: "customer_id",
            2: "first_name",
            3: "last_name",
            4: "birthday",
            5: "gender",
            6: "street_name",
            7: "house_number",
            8: "zip_code",
            9: "city",
            10: "email",
            11: "mobile_phone",
            12: "driving_license",
            13: "registration_date",
        }

        for index, field_name in field_mapping.items():
            if field_name in expected_data and index < len(actual_traveler):
                if field_name in encrypted_fields:
                    # For encrypted fields, decrypt before comparing
                    from data.encryption import decrypt_field

                    decrypted_value = decrypt_field(actual_traveler[index])
                    assert (
                        decrypted_value == expected_data[field_name]
                    ), f"Field {field_name}: expected {expected_data[field_name]}, got {decrypted_value}"
                else:
                    # For non-encrypted fields, compare directly
                    assert (
                        actual_traveler[index] == expected_data[field_name]
                    ), f"Field {field_name}: expected {expected_data[field_name]}, got {actual_traveler[index]}"

    @staticmethod
    def assert_data_is_encrypted(encrypted_value, original_value):
        """Assert that data is properly encrypted"""
        assert encrypted_value != original_value, "Data should be encrypted"
        assert len(encrypted_value) > len(
            original_value
        ), "Encrypted data should be longer"

        # Verify it's valid base64 (characteristic of Fernet encryption)
        import base64

        try:
            base64.b64decode(encrypted_value.encode())
        except Exception:
            assert False, "Encrypted data should be valid base64"


@pytest.fixture
def test_helpers():
    """Provide test helper methods"""
    return TravelersTestHelpers()
