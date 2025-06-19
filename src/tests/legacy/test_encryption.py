import pytest
import tempfile
import os
import gc
from unittest.mock import patch
from data.db_context import DatabaseContext
from data.encryption import decrypt_field


class TestLegacyEncryption:
    """Legacy encryption demonstration test"""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for legacy testing"""
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
    def temp_key_path(self):
        """Create temporary encryption key for testing"""
        key_fd, key_path = tempfile.mkstemp(suffix=".key")
        os.close(key_fd)

        # Generate a test key
        from cryptography.fernet import Fernet

        key = Fernet.generate_key()
        with open(key_path, "wb") as f:
            f.write(key)

        yield key_path

        # Cleanup
        if os.path.exists(key_path):
            os.unlink(key_path)

    def test_legacy_encryption_demonstration(self, temp_db_path, temp_key_path):
        """Legacy test: demonstrate encryption functionality"""

        # Patch the encryption key path to use our test key
        with patch("data.encryption.FERNET_KEY_PATH", temp_key_path):
            # Create database context
            db = DatabaseContext(temp_db_path)

            # Insert a traveler
            traveler = {
                "customer_id": "CUST001",
                "first_name": "Alice",
                "last_name": "Smith",
                "birthday": "01-01-1990",  # Fixed format
                "gender": "Female",  # Fixed format
                "street_name": "Main St",
                "house_number": "1",
                "zip_code": "1012NX",  # Fixed format
                "city": "Amsterdam",
                "email": "alice@example.com",
                "mobile_phone": "+31612345678",
                "driving_license": "DL123456",
                "registration_date": "2025-06-11T10:00:00",  # Fixed format
            }

            # Insert traveler (this should encrypt sensitive fields)
            db.insert_traveler(traveler)

            # Fetch and decrypt
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT email, mobile_phone, driving_license FROM travelers WHERE customer_id = ?",
                    ("CUST001",),
                )
                row = cursor.fetchone()

                print("Encrypted:", row)
                decrypted_values = [decrypt_field(val) for val in row]
                print("Decrypted:", decrypted_values)

                # Verify encryption/decryption works
                assert decrypted_values[0] == "alice@example.com"
                assert decrypted_values[1] == "+31612345678"
                assert decrypted_values[2] == "DL123456"

                # Verify data was actually encrypted
                assert row[0] != "alice@example.com"
                assert row[1] != "+31612345678"
                assert row[2] != "DL123456"
