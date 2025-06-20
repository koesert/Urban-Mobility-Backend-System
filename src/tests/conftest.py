import pytest
from unittest.mock import patch
import tempfile
import os
import gc
import shutil
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


@pytest.fixture
def temp_backup_directory():
    """Function-scoped temporary backup directory for backup tests"""
    backup_dir = tempfile.mkdtemp(prefix="backup_test_")
    yield backup_dir

    # Cleanup
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir, ignore_errors=True)


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
def test_scooter_data():
    """Standard test scooter data for backup tests"""
    return {
        "brand": "TestBrand",
        "model": "TestModel",
        "serial_number": "TEST1234567",
        "top_speed": 25,
        "battery_capacity": 1000,
        "state_of_charge": 80,
        "target_range_min": 20,
        "target_range_max": 40,
        "latitude": 51.92250,
        "longitude": 4.47917,
        "out_of_service_status": "",
        "mileage": 100.0,
        "last_maintenance_date": "2024-01-01",
        "in_service_date": "2024-01-01T10:00:00",
    }


@pytest.fixture
def test_backup_environment(temp_database, temp_encryption_key, temp_backup_directory):
    """Complete backup test environment with database, encryption, and backup directory"""
    with patch("data.encryption.FERNET_KEY_PATH", temp_encryption_key):
        from data.db_context import DatabaseContext
        from auth import AuthenticationService
        from managers.backup_manager import BackupManager

        # Create database and auth service
        db = DatabaseContext(temp_database)
        auth = AuthenticationService()
        auth.db = db

        # Create backup manager
        backup_manager = BackupManager(auth)
        backup_manager.backup_dir = temp_backup_directory

        return {
            "db": db,
            "auth": auth,
            "backup_manager": backup_manager,
            "db_path": temp_database,
            "key_path": temp_encryption_key,
            "backup_dir": temp_backup_directory,
        }


@pytest.fixture
def authorized_user_roles():
    """List of roles authorized to manage travelers"""
    return ["super_admin", "system_admin"]


@pytest.fixture
def unauthorized_user_roles():
    """List of roles not authorized to manage travelers"""
    return ["service_engineer", "invalid_role"]


@pytest.fixture
def backup_authorized_roles():
    """List of roles authorized for backup operations"""
    return {
        "create_backup": ["super_admin", "system_admin"],
        "restore_backup": ["super_admin"],
        "use_restore_code": ["super_admin", "system_admin"],
        "manage_restore_codes": ["super_admin"],
    }


@pytest.fixture
def test_user_credentials():
    """Standard test user credentials for different roles"""
    return {
        "super_admin": {"username": "super_admin", "password": "Admin_123?"},
        "system_admin": {"username": "test_sysadmin", "password": "SysAdmin123!"},
        "service_engineer": {"username": "test_engineer", "password": "Engineer123!"},
    }


# Pytest configuration for better test output
def pytest_configure(config):
    """Configure pytest markers and settings"""
    config.addinivalue_line("markers", "unit: Unit tests for isolated components")
    config.addinivalue_line(
        "markers", "integration: Integration tests with real database"
    )
    config.addinivalue_line("markers", "security: Security-focused tests")
    config.addinivalue_line("markers", "slow: Tests that may take longer to run")
    config.addinivalue_line("markers", "backup: Tests related to backup functionality")
    config.addinivalue_line("markers", "menu: Tests related to menu integration")
    config.addinivalue_line(
        "markers", "encryption: Tests related to encryption functionality"
    )
    config.addinivalue_line(
        "markers", "travelers: Tests related to travelers management"
    )
    config.addinivalue_line("markers", "auth: Tests related to authentication")
    config.addinivalue_line(
        "markers", "database: Tests that require database operations"
    )
    config.addinivalue_line("markers", "performance: Performance and load testing")


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


class BackupTestHelpers:
    """Helper methods for backup testing"""

    @staticmethod
    def assert_backup_file_valid(backup_path):
        """Assert that backup file is valid JSON with required structure"""
        import json

        assert os.path.exists(backup_path), f"Backup file should exist: {backup_path}"

        with open(backup_path, "r", encoding="utf-8") as f:
            backup_data = json.load(f)

        # Verify required fields
        required_fields = ["created_at", "created_by", "version", "tables"]
        for field in required_fields:
            assert field in backup_data, f"Backup should contain {field}"

        # Verify tables structure
        assert isinstance(backup_data["tables"], dict), "Tables should be a dictionary"

        # Verify table structure
        for table_name, table_data in backup_data["tables"].items():
            assert "columns" in table_data, f"Table {table_name} should have columns"
            assert "data" in table_data, f"Table {table_name} should have data"
            assert isinstance(
                table_data["columns"], list
            ), f"Table {table_name} columns should be a list"
            assert isinstance(
                table_data["data"], list
            ), f"Table {table_name} data should be a list"

        return backup_data

    @staticmethod
    def assert_restore_code_valid(restore_code):
        """Assert that restore code meets security requirements"""
        assert restore_code is not None, "Restore code should not be None"
        assert isinstance(restore_code, str), "Restore code should be a string"
        assert len(restore_code) == 12, "Restore code should be 12 characters long"
        assert restore_code.isalnum(), "Restore code should be alphanumeric"
        assert restore_code.isupper(), "Restore code should be uppercase"

        # Check for weak patterns
        weak_patterns = ["123456", "ABCDEF", "000000", "111111"]
        for pattern in weak_patterns:
            assert (
                pattern not in restore_code
            ), f"Restore code should not contain weak pattern: {pattern}"

    @staticmethod
    def create_test_users(db, auth):
        """Create test users for backup testing"""
        import hashlib
        from datetime import datetime

        test_users = [
            ("test_sysadmin", "SysAdmin123!", "system_admin"),
            ("test_engineer", "Engineer123!", "service_engineer"),
        ]

        with db.get_connection() as conn:
            cursor = conn.cursor()
            for username, password, role in test_users:
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                    (
                        username,
                        password_hash,
                        role,
                        "Test",
                        role.replace("_", " ").title(),
                        datetime.now().isoformat(),
                        1,
                    ),
                )
            conn.commit()

    @staticmethod
    def create_test_data(db):
        """Create comprehensive test data for backup testing"""
        from datetime import datetime

        # Create test travelers
        test_travelers = [
            {
                "customer_id": "CUST000001",
                "first_name": "Alice",
                "last_name": "Johnson",
                "birthday": "15-05-1990",
                "gender": "Female",
                "street_name": "Main Street",
                "house_number": "123",
                "zip_code": "1000AA",
                "city": "Amsterdam",
                "email": "alice@example.com",
                "mobile_phone": "+31 6 11111111",
                "driving_license": "AJ1111111",
                "registration_date": datetime.now().isoformat(),
            },
            {
                "customer_id": "CUST000002",
                "first_name": "Bob",
                "last_name": "Smith",
                "birthday": "20-08-1985",
                "gender": "Male",
                "street_name": "Second Street",
                "house_number": "456",
                "zip_code": "2000BB",
                "city": "Rotterdam",
                "email": "bob@example.com",
                "mobile_phone": "+31 6 22222222",
                "driving_license": "BS2222222",
                "registration_date": datetime.now().isoformat(),
            },
        ]

        for traveler in test_travelers:
            db.insert_traveler(traveler)

        # Create test scooters
        test_scooters = [
            {
                "brand": "TestBrand1",
                "model": "TestModel1",
                "serial_number": "TEST1234567",
                "top_speed": 25,
                "battery_capacity": 1000,
                "state_of_charge": 80,
                "target_range_min": 20,
                "target_range_max": 40,
                "latitude": 51.92250,
                "longitude": 4.47917,
                "out_of_service_status": "",
                "mileage": 100.0,
                "last_maintenance_date": "2024-01-01",
                "in_service_date": datetime.now().isoformat(),
            },
            {
                "brand": "TestBrand2",
                "model": "TestModel2",
                "serial_number": "TEST2345678",
                "top_speed": 30,
                "battery_capacity": 1200,
                "state_of_charge": 90,
                "target_range_min": 25,
                "target_range_max": 45,
                "latitude": 52.37403,
                "longitude": 4.88969,
                "out_of_service_status": "",
                "mileage": 50.0,
                "last_maintenance_date": "2024-01-15",
                "in_service_date": datetime.now().isoformat(),
            },
        ]

        for scooter in test_scooters:
            db.insert_scooter(scooter)

        return {
            "travelers_count": len(test_travelers),
            "scooters_count": len(test_scooters),
        }


@pytest.fixture
def test_helpers():
    """Provide test helper methods"""
    return TravelersTestHelpers()


@pytest.fixture
def backup_helpers():
    """Provide backup test helper methods"""
    return BackupTestHelpers()


@pytest.fixture
def comprehensive_test_environment(test_backup_environment, backup_helpers):
    """Complete test environment with test data for comprehensive backup testing"""
    env = test_backup_environment

    # Create test users
    backup_helpers.create_test_users(env["db"], env["auth"])

    # Create test data
    test_data_info = backup_helpers.create_test_data(env["db"])
    env.update(test_data_info)

    # Login as super admin by default
    env["auth"].login("super_admin", "Admin_123?")

    return env
