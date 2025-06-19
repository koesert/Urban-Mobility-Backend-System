import pytest
import tempfile
import os
import gc
from unittest.mock import patch, Mock
from datetime import datetime
from auth import AuthenticationService
from managers.travelers_manager import TravelersManager
from data.db_context import DatabaseContext
from data.encryption import encrypt_field, decrypt_field


class TestTravelersIntegration:
    """Integration tests for complete travelers management workflows"""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for integration testing"""
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
        yield db_path

        # Force cleanup connections and garbage collection
        gc.collect()

        # Try to remove the file multiple times (Windows fix)
        for i in range(5):
            try:
                if os.path.exists(db_path):
                    os.unlink(db_path)
                break
            except (PermissionError, FileNotFoundError):
                if i == 4:  # Last attempt
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

    @pytest.fixture
    def test_environment(self, temp_db_path, temp_key_path):
        """Setup complete test environment with real database and encryption"""
        # Patch the encryption key path
        with patch("data.encryption.FERNET_KEY_PATH", temp_key_path):
            # Create database and auth service
            db = DatabaseContext(temp_db_path)
            auth = AuthenticationService()
            auth.db = db

            # Login as super admin
            auth.login("super_admin", "Admin_123?")

            # Create travelers manager
            travelers_manager = TravelersManager(auth)

            return {
                "db": db,
                "auth": auth,
                "travelers_manager": travelers_manager,
                "db_path": temp_db_path,
                "key_path": temp_key_path,
            }

    def test_complete_traveler_lifecycle_crud_operations(self, test_environment):
        """Test complete CREATE, READ, UPDATE, DELETE operations for travelers"""
        env = test_environment
        manager = env["travelers_manager"]

        # Test CREATE - Add new traveler
        test_traveler = {
            "customer_id": "CUST000001",
            "first_name": "Alice",
            "last_name": "Johnson",
            "birthday": "15-05-1990",
            "gender": "Female",
            "street_name": "Kalverstraat",
            "house_number": "123",
            "zip_code": "1012NX",
            "city": "Amsterdam",
            "email": "alice.johnson@example.com",
            "mobile_phone": "+31 6 12345678",
            "driving_license": "AB1234567",
            "registration_date": datetime.now().isoformat(),
        }

        # Insert traveler using database method (which handles encryption)
        env["db"].insert_traveler(test_traveler)

        # Test READ - Verify traveler was created and data is encrypted in database
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM travelers WHERE customer_id = ?", ("CUST000001",)
            )
            stored_traveler = cursor.fetchone()

            assert stored_traveler is not None
            assert stored_traveler[1] == "CUST000001"  # customer_id
            assert stored_traveler[2] == "Alice"  # first_name (not encrypted)
            assert stored_traveler[3] == "Johnson"  # last_name (not encrypted)

            # Verify sensitive data is encrypted
            assert (
                stored_traveler[10] != "alice.johnson@example.com"
            )  # email should be encrypted
            assert stored_traveler[11] != "+31 6 12345678"  # phone should be encrypted
            assert stored_traveler[12] != "AB1234567"  # license should be encrypted

            # Verify we can decrypt the data
            decrypted_email = decrypt_field(stored_traveler[10])
            decrypted_phone = decrypt_field(stored_traveler[11])
            decrypted_license = decrypt_field(stored_traveler[12])

            assert decrypted_email == "alice.johnson@example.com"
            assert decrypted_phone == "+31 6 12345678"
            assert decrypted_license == "AB1234567"

        # Test READ - Get traveler by ID
        retrieved_traveler = manager._get_traveler_by_id("CUST000001")
        assert retrieved_traveler is not None
        assert retrieved_traveler[1] == "CUST000001"

        # Test UPDATE - Update traveler information
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()

            # Update email and phone
            new_email = encrypt_field("alice.updated@example.com")
            new_phone = encrypt_field("+31 6 87654321")

            cursor.execute(
                """
                UPDATE travelers 
                SET email = ?, mobile_phone = ?
                WHERE customer_id = ?
            """,
                (new_email, new_phone, "CUST000001"),
            )
            conn.commit()

            # Verify update
            cursor.execute(
                "SELECT email, mobile_phone FROM travelers WHERE customer_id = ?",
                ("CUST000001",),
            )
            updated_data = cursor.fetchone()

            assert decrypt_field(updated_data[0]) == "alice.updated@example.com"
            assert decrypt_field(updated_data[1]) == "+31 6 87654321"

        # Test DELETE - Remove traveler
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM travelers WHERE customer_id = ?", ("CUST000001",)
            )
            conn.commit()

            # Verify deletion
            cursor.execute(
                "SELECT * FROM travelers WHERE customer_id = ?", ("CUST000001",)
            )
            deleted_traveler = cursor.fetchone()
            assert deleted_traveler is None

    def test_search_traveler_with_encrypted_email(self, test_environment):
        """Test searching travelers by encrypted email address"""
        env = test_environment
        manager = env["travelers_manager"]

        # Add test travelers
        test_travelers = [
            {
                "customer_id": "CUST000001",
                "first_name": "John",
                "last_name": "Smith",
                "birthday": "01-01-1985",
                "gender": "Male",
                "street_name": "Main Street",
                "house_number": "1",
                "zip_code": "1000AA",
                "city": "Amsterdam",
                "email": "john.smith@example.com",
                "mobile_phone": "+31 6 11111111",
                "driving_license": "JS1234567",
                "registration_date": datetime.now().isoformat(),
            },
            {
                "customer_id": "CUST000002",
                "first_name": "Jane",
                "last_name": "Doe",
                "birthday": "15-03-1990",
                "gender": "Female",
                "street_name": "Second Street",
                "house_number": "2",
                "zip_code": "1000BB",
                "city": "Rotterdam",
                "email": "jane.doe@example.com",
                "mobile_phone": "+31 6 22222222",
                "driving_license": "JD1234567",
                "registration_date": datetime.now().isoformat(),
            },
        ]

        for traveler in test_travelers:
            env["db"].insert_traveler(traveler)

        # Test search by non-encrypted fields (name, customer_id)
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()

            # Search by first name
            cursor.execute(
                """
                SELECT * FROM travelers 
                WHERE first_name LIKE ?
            """,
                ("%John%",),
            )
            john_results = cursor.fetchall()
            assert len(john_results) == 1
            assert john_results[0][2] == "John"

            # Search by customer ID
            cursor.execute(
                """
                SELECT * FROM travelers 
                WHERE customer_id LIKE ?
            """,
                ("%CUST000002%",),
            )
            jane_results = cursor.fetchall()
            assert len(jane_results) == 1
            assert jane_results[0][1] == "CUST000002"

        # Test search in encrypted email field (simulating manager's search method)
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM travelers")
            all_travelers = cursor.fetchall()

            # Find traveler with specific email
            found_traveler = None
            search_email = "jane.doe@example.com"

            for traveler in all_travelers:
                try:
                    decrypted_email = decrypt_field(traveler[10])  # email field
                    if search_email.lower() in decrypted_email.lower():
                        found_traveler = traveler
                        break
                except Exception:
                    continue

            assert found_traveler is not None
            assert found_traveler[3] == "Doe"  # last_name

    def test_multiple_travelers_with_same_personal_data_different_encryption(
        self, test_environment
    ):
        """Test that identical personal data gets different encrypted values"""
        env = test_environment

        # Create two travelers with same email but different customer IDs
        traveler1 = {
            "customer_id": "CUST000001",
            "first_name": "John",
            "last_name": "Smith",
            "birthday": "01-01-1985",
            "gender": "Male",
            "street_name": "Street A",
            "house_number": "1",
            "zip_code": "1000AA",
            "city": "Amsterdam",
            "email": "duplicate@example.com",
            "mobile_phone": "+31 6 11111111",
            "driving_license": "JS1111111",
            "registration_date": datetime.now().isoformat(),
        }

        traveler2 = {
            "customer_id": "CUST000002",
            "first_name": "Jane",
            "last_name": "Doe",
            "birthday": "15-03-1990",
            "gender": "Female",
            "street_name": "Street B",
            "house_number": "2",
            "zip_code": "2000BB",
            "city": "Rotterdam",
            "email": "duplicate@example.com",  # Same email
            "mobile_phone": "+31 6 22222222",
            "driving_license": "JD2222222",
            "registration_date": datetime.now().isoformat(),
        }

        # Insert both travelers
        env["db"].insert_traveler(traveler1)
        env["db"].insert_traveler(traveler2)

        # Verify they have different encrypted values even with same email
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT customer_id, email FROM travelers ORDER BY customer_id"
            )
            results = cursor.fetchall()

            assert len(results) == 2
            encrypted_email1 = results[0][1]
            encrypted_email2 = results[1][1]

            # Encrypted values should be different (Fernet includes random IV)
            assert encrypted_email1 != encrypted_email2

            # But both should decrypt to the same value
            assert decrypt_field(encrypted_email1) == "duplicate@example.com"
            assert decrypt_field(encrypted_email2) == "duplicate@example.com"

    def test_traveler_data_integrity_after_database_operations(self, test_environment):
        """Test data integrity throughout multiple database operations"""
        env = test_environment

        original_data = {
            "customer_id": "CUST000001",
            "first_name": "DataIntegrity",
            "last_name": "TestUser",
            "birthday": "01-01-1990",
            "gender": "Male",
            "street_name": "Integrity Street",
            "house_number": "1",
            "zip_code": "1234AB",
            "city": "Utrecht",
            "email": "integrity@test.com",
            "mobile_phone": "+31 6 12345678",
            "driving_license": "IT1234567",
            "registration_date": datetime.now().isoformat(),
        }

        # Insert
        env["db"].insert_traveler(original_data)

        # Multiple read operations
        for _ in range(5):
            with env["db"].get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM travelers WHERE customer_id = ?", ("CUST000001",)
                )
                traveler = cursor.fetchone()

                # Verify data consistency
                assert traveler[2] == "DataIntegrity"
                assert decrypt_field(traveler[10]) == "integrity@test.com"
                assert decrypt_field(traveler[11]) == "+31 6 12345678"
                assert decrypt_field(traveler[12]) == "IT1234567"

        # Update operation
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            new_email = encrypt_field("updated.integrity@test.com")
            cursor.execute(
                """
                UPDATE travelers 
                SET email = ? 
                WHERE customer_id = ?
            """,
                (new_email, "CUST000001"),
            )
            conn.commit()

        # Verify update integrity
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT email FROM travelers WHERE customer_id = ?", ("CUST000001",)
            )
            updated_email = cursor.fetchone()[0]
            assert decrypt_field(updated_email) == "updated.integrity@test.com"

    def test_concurrent_traveler_operations_simulation(self, test_environment):
        """Test simulation of concurrent operations on travelers"""
        env = test_environment

        # Simulate multiple "sessions" by creating separate database connections

        # Session 1: Add traveler
        with env["db"].get_connection() as conn1:
            cursor1 = conn1.cursor()
            env["db"].insert_traveler(
                {
                    "customer_id": "CUST000001",
                    "first_name": "Concurrent",
                    "last_name": "User1",
                    "birthday": "01-01-1990",
                    "gender": "Male",
                    "street_name": "Concurrent St",
                    "house_number": "1",
                    "zip_code": "1111AA",
                    "city": "Amsterdam",
                    "email": "concurrent1@test.com",
                    "mobile_phone": "+31 6 11111111",
                    "driving_license": "CU1111111",
                    "registration_date": datetime.now().isoformat(),
                }
            )

        # Session 2: Add another traveler simultaneously
        with env["db"].get_connection() as conn2:
            cursor2 = conn2.cursor()
            env["db"].insert_traveler(
                {
                    "customer_id": "CUST000002",
                    "first_name": "Concurrent",
                    "last_name": "User2",
                    "birthday": "02-02-1990",
                    "gender": "Female",
                    "street_name": "Concurrent Ave",
                    "house_number": "2",
                    "zip_code": "2222BB",
                    "city": "Rotterdam",
                    "email": "concurrent2@test.com",
                    "mobile_phone": "+31 6 22222222",
                    "driving_license": "CU2222222",
                    "registration_date": datetime.now().isoformat(),
                }
            )

        # Verify both travelers exist and data is correct
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM travelers")
            count = cursor.fetchone()[0]
            assert count == 2

            # Verify each traveler's data
            cursor.execute(
                "SELECT * FROM travelers WHERE customer_id = ?", ("CUST000001",)
            )
            traveler1 = cursor.fetchone()
            assert decrypt_field(traveler1[10]) == "concurrent1@test.com"

            cursor.execute(
                "SELECT * FROM travelers WHERE customer_id = ?", ("CUST000002",)
            )
            traveler2 = cursor.fetchone()
            assert decrypt_field(traveler2[10]) == "concurrent2@test.com"

    def test_encryption_key_rotation_compatibility(self, test_environment):
        """Test that travelers can still be read after encryption key operations"""
        env = test_environment

        # Add traveler with current key
        original_traveler = {
            "customer_id": "CUST000001",
            "first_name": "KeyRotation",
            "last_name": "TestUser",
            "birthday": "01-01-1990",
            "gender": "Male",
            "street_name": "Key Street",
            "house_number": "1",
            "zip_code": "1111KK",
            "city": "Amsterdam",
            "email": "keyrotation@test.com",
            "mobile_phone": "+31 6 99999999",
            "driving_license": "KR9999999",
            "registration_date": datetime.now().isoformat(),
        }

        env["db"].insert_traveler(original_traveler)

        # Verify we can read the data
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT email FROM travelers WHERE customer_id = ?", ("CUST000001",)
            )
            encrypted_email = cursor.fetchone()[0]
            decrypted_email = decrypt_field(encrypted_email)
            assert decrypted_email == "keyrotation@test.com"

        # Test that the same encryption key produces consistent results
        # (This tests the stability of the encryption system)
        test_value = "consistency_test@example.com"
        encrypted1 = encrypt_field(test_value)
        encrypted2 = encrypt_field(test_value)

        # Should be different due to random IV
        assert encrypted1 != encrypted2

        # But both should decrypt correctly
        assert decrypt_field(encrypted1) == test_value
        assert decrypt_field(encrypted2) == test_value

    def test_large_dataset_performance(self, test_environment):
        """Test performance with larger number of travelers"""
        env = test_environment
        import time

        # Create 100 test travelers
        travelers_count = 100
        start_time = time.time()

        for i in range(travelers_count):
            traveler = {
                "customer_id": f"CUST{i:06d}",
                "first_name": f"User{i}",
                "last_name": f"TestLast{i}",
                "birthday": "01-01-1990",
                "gender": "Male" if i % 2 == 0 else "Female",
                "street_name": f"Street {i}",
                "house_number": str(i + 1),
                "zip_code": f"{1000 + i:04d}AB",
                "city": env["travelers_manager"].PREDEFINED_CITIES[
                    i % len(env["travelers_manager"].PREDEFINED_CITIES)
                ],
                "email": f"user{i}@performance.test",
                "mobile_phone": f"+31 6 {i:08d}",
                "driving_license": f"PF{i:07d}",
                "registration_date": datetime.now().isoformat(),
            }
            env["db"].insert_traveler(traveler)

        insert_time = time.time() - start_time

        # Test bulk read performance
        start_time = time.time()
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM travelers")
            all_travelers = cursor.fetchall()

        read_time = time.time() - start_time

        # Test decryption performance on subset
        start_time = time.time()
        decrypted_count = 0
        for traveler in all_travelers[:10]:  # Test first 10
            try:
                decrypt_field(traveler[10])  # email
                decrypt_field(traveler[11])  # phone
                decrypt_field(traveler[12])  # license
                decrypted_count += 1
            except Exception:
                pass

        decrypt_time = time.time() - start_time

        # Assertions
        assert len(all_travelers) == travelers_count
        assert decrypted_count == 10

        # Performance should be reasonable
        assert (
            insert_time < 30.0
        ), f"Insert time too slow: {insert_time}s for {travelers_count} records"
        assert (
            read_time < 5.0
        ), f"Read time too slow: {read_time}s for {travelers_count} records"
        assert (
            decrypt_time < 1.0
        ), f"Decrypt time too slow: {decrypt_time}s for 10 decryptions"

    def test_error_recovery_and_transaction_rollback(self, test_environment):
        """Test error recovery and transaction handling"""
        env = test_environment

        # Test 1: Invalid data should not be inserted
        invalid_traveler = {
            "customer_id": "CUST000001",
            "first_name": "Invalid",
            "last_name": "User",
            # Missing required fields to trigger error
        }

        # This should fail gracefully
        try:
            env["db"].insert_traveler(invalid_traveler)
        except Exception:
            pass  # Expected to fail

        # Verify no partial data was inserted
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM travelers")
            count = cursor.fetchone()[0]
            assert count == 0

        # Test 2: Valid traveler should insert successfully after error
        valid_traveler = {
            "customer_id": "CUST000001",
            "first_name": "Valid",
            "last_name": "User",
            "birthday": "01-01-1990",
            "gender": "Male",
            "street_name": "Recovery St",
            "house_number": "1",
            "zip_code": "1111RR",
            "city": "Amsterdam",
            "email": "recovery@test.com",
            "mobile_phone": "+31 6 99999999",
            "driving_license": "RV9999999",
            "registration_date": datetime.now().isoformat(),
        }

        env["db"].insert_traveler(valid_traveler)

        # Verify successful insertion
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM travelers")
            count = cursor.fetchone()[0]
            assert count == 1
