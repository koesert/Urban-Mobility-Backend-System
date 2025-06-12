import pytest
import tempfile
import os
import gc
from unittest.mock import patch
from data.db_context import DatabaseContext
from data.encryption import decrypt_field, encrypt_field


class TestEncryptionIntegration:
    """Integration tests for encryption with database operations"""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for integration testing"""
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

    def test_end_to_end_encryption_with_database(self, temp_db_path, temp_key_path):
        """Test complete encryption flow from insertion to retrieval"""

        # Patch the encryption key path to use our test key
        with patch("data.encryption.FERNET_KEY_PATH", temp_key_path):
            # Create database context
            db = DatabaseContext(temp_db_path)

            # Test traveler data (based on original test_encryption.py)
            traveler_data = {
                "customer_id": "CUST000001",
                "first_name": "Alice",
                "last_name": "Smith",
                "birthday": "01-01-1990",
                "gender": "Female",
                "street_name": "Main St",
                "house_number": "1",
                "zip_code": "1012NX",
                "city": "Amsterdam",
                "email": "alice@example.com",
                "mobile_phone": "+31612345678",
                "driving_license": "DL123456",
                "registration_date": "2025-06-11T10:00:00",
            }

            # Insert traveler (this should encrypt sensitive fields)
            db.insert_traveler(traveler_data)

            # Fetch raw data from database to verify encryption
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT email, mobile_phone, driving_license FROM travelers WHERE customer_id = ?",
                    ("CUST000001",),
                )
                encrypted_row = cursor.fetchone()

                # Verify data is encrypted in database
                assert encrypted_row is not None
                encrypted_email, encrypted_phone, encrypted_license = encrypted_row

                # Raw database values should NOT match original values
                assert encrypted_email != "alice@example.com"
                assert encrypted_phone != "+31612345678"
                assert encrypted_license != "DL123456"

                # But should be longer (due to encryption overhead)
                assert len(encrypted_email) > len("alice@example.com")
                assert len(encrypted_phone) > len("+31612345678")
                assert len(encrypted_license) > len("DL123456")

                print("✅ Raw encrypted data in database:")
                print(f"   Email: {encrypted_email}")
                print(f"   Phone: {encrypted_phone}")
                print(f"   License: {encrypted_license}")

                # Decrypt and verify original values
                decrypted_email = decrypt_field(encrypted_email)
                decrypted_phone = decrypt_field(encrypted_phone)
                decrypted_license = decrypt_field(encrypted_license)

                print("✅ Decrypted values:")
                print(f"   Email: {decrypted_email}")
                print(f"   Phone: {decrypted_phone}")
                print(f"   License: {decrypted_license}")

                # Verify decryption matches original data
                assert decrypted_email == "alice@example.com"
                assert decrypted_phone == "+31612345678"
                assert decrypted_license == "DL123456"

    def test_multiple_travelers_encryption_independence(
        self, temp_db_path, temp_key_path
    ):
        """Test that multiple travelers with same data get different encrypted values"""

        with patch("data.encryption.FERNET_KEY_PATH", temp_key_path):
            db = DatabaseContext(temp_db_path)

            # Create two travelers with identical sensitive data
            traveler1 = {
                "customer_id": "CUST000001",
                "first_name": "John",
                "last_name": "Doe",
                "birthday": "01-01-1990",
                "gender": "Male",
                "street_name": "Same Street",
                "house_number": "1",
                "zip_code": "1000AA",
                "city": "Amsterdam",
                "email": "identical@example.com",  # Same email
                "mobile_phone": "+31687654321",  # Same phone
                "driving_license": "SAME123456",  # Same license
                "registration_date": "2025-06-11T10:00:00",
            }

            traveler2 = {
                "customer_id": "CUST000002",
                "first_name": "Jane",
                "last_name": "Doe",
                "birthday": "02-02-1990",
                "gender": "Female",
                "street_name": "Different Street",
                "house_number": "2",
                "zip_code": "2000BB",
                "city": "Rotterdam",
                "email": "identical@example.com",  # Same email as traveler1
                "mobile_phone": "+31687654321",  # Same phone as traveler1
                "driving_license": "SAME123456",  # Same license as traveler1
                "registration_date": "2025-06-11T11:00:00",
            }

            # Insert both travelers
            db.insert_traveler(traveler1)
            db.insert_traveler(traveler2)

            # Retrieve encrypted data for both
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT customer_id, email, mobile_phone, driving_license 
                    FROM travelers 
                    ORDER BY customer_id
                """
                )
                results = cursor.fetchall()

                assert len(results) == 2

                # Extract encrypted values
                traveler1_data = results[0]
                traveler2_data = results[1]

                # Encrypted values should be different (Fernet uses random IV)
                assert traveler1_data[1] != traveler2_data[1]  # email
                assert traveler1_data[2] != traveler2_data[2]  # phone
                assert traveler1_data[3] != traveler2_data[3]  # license

                # But both should decrypt to the same original values
                for i, traveler_data in enumerate([traveler1_data, traveler2_data], 1):
                    decrypted_email = decrypt_field(traveler_data[1])
                    decrypted_phone = decrypt_field(traveler_data[2])
                    decrypted_license = decrypt_field(traveler_data[3])

                    assert decrypted_email == "identical@example.com"
                    assert decrypted_phone == "+31687654321"
                    assert decrypted_license == "SAME123456"

                    print(f"✅ Traveler {i} decryption successful")

    def test_encryption_with_special_characters(self, temp_db_path, temp_key_path):
        """Test encryption works with special characters and unicode"""

        with patch("data.encryption.FERNET_KEY_PATH", temp_key_path):
            db = DatabaseContext(temp_db_path)

            # Traveler with special characters
            special_traveler = {
                "customer_id": "CUST000001",
                "first_name": "José",
                "last_name": "García-López",
                "birthday": "01-01-1990",
                "gender": "Male",
                "street_name": "Straße der Résistance",
                "house_number": "1A",
                "zip_code": "1000AA",
                "city": "Amsterdam",
                "email": "josé.garcía@exämple.com",  # Special chars
                "mobile_phone": "+31 6 áéíóú321",  # Unicode in phone
                "driving_license": "ÄÖÜ123456",  # German umlauts
                "registration_date": "2025-06-11T10:00:00",
            }

            # Insert traveler
            db.insert_traveler(special_traveler)

            # Retrieve and verify
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT email, mobile_phone, driving_license FROM travelers WHERE customer_id = ?",
                    ("CUST000001",),
                )
                encrypted_data = cursor.fetchone()

                # Decrypt and verify special characters are preserved
                decrypted_email = decrypt_field(encrypted_data[0])
                decrypted_phone = decrypt_field(encrypted_data[1])
                decrypted_license = decrypt_field(encrypted_data[2])

                assert decrypted_email == "josé.garcía@exämple.com"
                assert decrypted_phone == "+31 6 áéíóú321"
                assert decrypted_license == "ÄÖÜ123456"

                print("✅ Special characters preserved through encryption/decryption")

    def test_encryption_error_handling(self, temp_db_path, temp_key_path):
        """Test error handling with corrupted encrypted data"""

        with patch("data.encryption.FERNET_KEY_PATH", temp_key_path):
            db = DatabaseContext(temp_db_path)

            # Insert normal traveler
            traveler = {
                "customer_id": "CUST000001",
                "first_name": "Test",
                "last_name": "User",
                "birthday": "01-01-1990",
                "gender": "Male",
                "street_name": "Test Street",
                "house_number": "1",
                "zip_code": "1000AA",
                "city": "Amsterdam",
                "email": "test@example.com",
                "mobile_phone": "+31612345678",
                "driving_license": "TU123456",
                "registration_date": "2025-06-11T10:00:00",
            }

            db.insert_traveler(traveler)

            # Manually corrupt the encrypted data in database
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE travelers 
                    SET email = 'corrupted_data_not_base64_valid'
                    WHERE customer_id = ?
                """,
                    ("CUST000001",),
                )
                conn.commit()

                # Try to retrieve and decrypt corrupted data
                cursor.execute(
                    "SELECT email FROM travelers WHERE customer_id = ?", ("CUST000001",)
                )
                corrupted_email = cursor.fetchone()[0]

                # Attempting to decrypt should raise an exception
                with pytest.raises(Exception):
                    decrypt_field(corrupted_email)

                print("✅ Corrupted data properly raises exception")

    def test_encryption_performance_with_database(self, temp_db_path, temp_key_path):
        """Test encryption performance in database operations"""
        import time

        with patch("data.encryption.FERNET_KEY_PATH", temp_key_path):
            db = DatabaseContext(temp_db_path)

            # Insert multiple travelers and measure time
            num_travelers = 50
            start_time = time.time()

            for i in range(num_travelers):
                traveler = {
                    "customer_id": f"CUST{i:06d}",
                    "first_name": f"User{i}",
                    "last_name": f"Last{i}",
                    "birthday": "01-01-1990",
                    "gender": "Male" if i % 2 == 0 else "Female",
                    "street_name": f"Street {i}",
                    "house_number": str(i + 1),
                    "zip_code": f"{1000 + i:04d}AB",
                    "city": "Amsterdam",
                    "email": f"user{i}@performance.test",
                    "mobile_phone": f"+31 6 {i:08d}",
                    "driving_license": f"PF{i:07d}",
                    "registration_date": "2025-06-11T10:00:00",
                }
                db.insert_traveler(traveler)

            insert_time = time.time() - start_time

            # Read and decrypt all travelers
            start_time = time.time()
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT email, mobile_phone, driving_license FROM travelers"
                )
                all_encrypted_data = cursor.fetchall()

                decrypted_count = 0
                for encrypted_data in all_encrypted_data:
                    try:
                        decrypt_field(encrypted_data[0])  # email
                        decrypt_field(encrypted_data[1])  # phone
                        decrypt_field(encrypted_data[2])  # license
                        decrypted_count += 1
                    except Exception:
                        pass

            decrypt_time = time.time() - start_time

            # Performance assertions
            assert decrypted_count == num_travelers
            assert (
                insert_time < 10.0
            ), f"Insert time too slow: {insert_time}s for {num_travelers} records"
            assert (
                decrypt_time < 5.0
            ), f"Decrypt time too slow: {decrypt_time}s for {num_travelers * 3} decryptions"

            print(f"✅ Performance test completed:")
            print(f"   Inserted {num_travelers} travelers in {insert_time:.2f}s")
            print(f"   Decrypted {decrypted_count * 3} fields in {decrypt_time:.2f}s")

    def test_cross_key_decryption_failure(self, temp_db_path):
        """Test that data encrypted with one key cannot be decrypted with another"""

        # Create two different encryption keys
        key1_fd, key1_path = tempfile.mkstemp(suffix=".key")
        key2_fd, key2_path = tempfile.mkstemp(suffix=".key")
        os.close(key1_fd)
        os.close(key2_fd)

        from cryptography.fernet import Fernet

        try:
            # Generate two different keys
            key1 = Fernet.generate_key()
            key2 = Fernet.generate_key()

            with open(key1_path, "wb") as f:
                f.write(key1)
            with open(key2_path, "wb") as f:
                f.write(key2)

            encrypted_email = None

            # Encrypt data with first key
            with patch("data.encryption.FERNET_KEY_PATH", key1_path):
                # Also patch the fernet instance to ensure it uses the new key
                with patch("data.encryption.fernet", Fernet(key1)):
                    db = DatabaseContext(temp_db_path)

                    traveler = {
                        "customer_id": "CUST000001",
                        "first_name": "KeyTest",
                        "last_name": "User",
                        "birthday": "01-01-1990",
                        "gender": "Male",
                        "street_name": "Key Street",
                        "house_number": "1",
                        "zip_code": "1000AA",
                        "city": "Amsterdam",
                        "email": "keytest@example.com",
                        "mobile_phone": "+31612345678",
                        "driving_license": "KT123456",
                        "registration_date": "2025-06-11T10:00:00",
                    }

                    db.insert_traveler(traveler)

                    # Get the encrypted email
                    with db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT email FROM travelers WHERE customer_id = ?",
                            ("CUST000001",),
                        )
                        encrypted_email = cursor.fetchone()[0]

            # Try to decrypt with second key (should fail)
            with patch("data.encryption.FERNET_KEY_PATH", key2_path):
                # Patch the fernet instance to use the second key
                with patch("data.encryption.fernet", Fernet(key2)):
                    from data.encryption import decrypt_field

                    # This should raise an exception
                    with pytest.raises(Exception):
                        decrypt_field(encrypted_email)

                    print("✅ Cross-key decryption properly failed")

        finally:
            # Cleanup
            for key_path in [key1_path, key2_path]:
                if os.path.exists(key_path):
                    os.unlink(key_path)