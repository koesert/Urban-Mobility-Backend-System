import pytest
import tempfile
import os
import gc
import json
import shutil
from unittest.mock import patch, Mock
from datetime import datetime
from auth import AuthenticationService
from managers.backup_manager import BackupManager
from data.db_context import DatabaseContext
from data.encryption import encrypt_field, decrypt_field


class TestBackupIntegration:
    """Integration tests for complete backup workflows"""

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
    def temp_backup_dir(self):
        """Create temporary backup directory"""
        backup_dir = tempfile.mkdtemp(prefix="backup_test_")
        yield backup_dir

        # Cleanup
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir, ignore_errors=True)

    @pytest.fixture
    def test_environment(self, temp_db_path, temp_key_path, temp_backup_dir):
        """Setup complete test environment with real database and encryption"""
        with patch("data.encryption.FERNET_KEY_PATH", temp_key_path):
            # Create database and auth service
            db = DatabaseContext(temp_db_path)
            auth = AuthenticationService()
            auth.db = db

            # Login as super admin
            auth.login("super_admin", "Admin_123?")

            # Create backup manager with custom backup directory
            backup_manager = BackupManager(auth)
            backup_manager.backup_dir = temp_backup_dir

            return {
                "db": db,
                "auth": auth,
                "backup_manager": backup_manager,
                "db_path": temp_db_path,
                "key_path": temp_key_path,
                "backup_dir": temp_backup_dir,
            }

    def test_complete_backup_restore_cycle(self, test_environment):
        """Test complete backup and restore cycle"""
        env = test_environment
        backup_manager = env["backup_manager"]

        # Step 1: Add test data to database
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
                "mobile_phone": "+31 6 12345678",
                "driving_license": "AJ1234567",
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
                "mobile_phone": "+31 6 87654321",
                "driving_license": "BS2345678",
                "registration_date": datetime.now().isoformat(),
            },
        ]

        # Insert test travelers
        for traveler in test_travelers:
            env["db"].insert_traveler(traveler)

        # Add test scooter
        test_scooter = {
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
            "in_service_date": datetime.now().isoformat(),
        }
        env["db"].insert_scooter(test_scooter)

        # Step 2: Verify initial data count
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM travelers")
            initial_travelers_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM scooters")
            initial_scooters_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM users")
            initial_users_count = cursor.fetchone()[0]

        assert initial_travelers_count == 2
        assert initial_scooters_count == 1
        assert initial_users_count >= 1  # At least super_admin

        # Step 3: Create backup
        backup_filename = backup_manager.create_backup()
        assert backup_filename is not None
        assert backup_filename.startswith("backup_")
        assert backup_filename.endswith(".json")

        # Verify backup file exists
        backup_path = os.path.join(env["backup_dir"], backup_filename)
        assert os.path.exists(backup_path)

        # Step 4: Verify backup contents
        with open(backup_path, "r", encoding="utf-8") as f:
            backup_data = json.load(f)

        assert "created_at" in backup_data
        assert "created_by" in backup_data
        assert backup_data["created_by"] == "super_admin"
        assert "tables" in backup_data

        # Check table data in backup
        assert "users" in backup_data["tables"]
        assert "travelers" in backup_data["tables"]
        assert "scooters" in backup_data["tables"]

        # Verify data counts in backup
        assert len(backup_data["tables"]["users"]["data"]) == initial_users_count
        assert (
            len(backup_data["tables"]["travelers"]["data"]) == initial_travelers_count
        )
        assert len(backup_data["tables"]["scooters"]["data"]) == initial_scooters_count

        # Step 5: Modify database (add new data)
        additional_traveler = {
            "customer_id": "CUST000003",
            "first_name": "Charlie",
            "last_name": "Brown",
            "birthday": "10-12-1995",
            "gender": "Male",
            "street_name": "Third Avenue",
            "house_number": "789",
            "zip_code": "3000CC",
            "city": "Utrecht",
            "email": "charlie@example.com",
            "mobile_phone": "+31 6 11111111",
            "driving_license": "CB3456789",
            "registration_date": datetime.now().isoformat(),
        }
        env["db"].insert_traveler(additional_traveler)

        # Verify modified data count
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM travelers")
            modified_travelers_count = cursor.fetchone()[0]

        assert modified_travelers_count == 3

        # Step 6: Restore from backup
        with patch("builtins.input", return_value="RESTORE"):
            restore_success = backup_manager.restore_backup(backup_filename)

        assert restore_success is True

        # Step 7: Verify data was restored to original state
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM travelers")
            restored_travelers_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM scooters")
            restored_scooters_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM users")
            restored_users_count = cursor.fetchone()[0]

        # Data should be back to original counts
        assert restored_travelers_count == initial_travelers_count
        assert restored_scooters_count == initial_scooters_count
        assert restored_users_count == initial_users_count

        # Step 8: Verify specific traveler data was restored correctly
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM travelers WHERE customer_id = ?", ("CUST000001",)
            )
            restored_traveler = cursor.fetchone()

        assert restored_traveler is not None
        assert restored_traveler[2] == "Alice"  # first_name
        assert restored_traveler[3] == "Johnson"  # last_name

        # Verify encrypted data is still encrypted and can be decrypted
        encrypted_email = restored_traveler[10]
        decrypted_email = decrypt_field(encrypted_email)
        assert decrypted_email == "alice@example.com"

    def test_backup_with_encrypted_data_integrity(self, test_environment):
        """Test that encrypted data maintains integrity through backup/restore"""
        env = test_environment
        backup_manager = env["backup_manager"]

        # Add traveler with sensitive data
        sensitive_traveler = {
            "customer_id": "CUST000001",
            "first_name": "Sensitive",
            "last_name": "Data",
            "birthday": "01-01-1990",
            "gender": "Male",
            "street_name": "Privacy Street",
            "house_number": "1",
            "zip_code": "1234AB",
            "city": "Amsterdam",
            "email": "highly.sensitive@classified.gov",
            "mobile_phone": "+31 6 99999999",
            "driving_license": "SD9999999",
            "registration_date": datetime.now().isoformat(),
        }

        env["db"].insert_traveler(sensitive_traveler)

        # Get encrypted values from database
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT email, mobile_phone, driving_license FROM travelers WHERE customer_id = ?",
                ("CUST000001",),
            )
            original_encrypted_data = cursor.fetchone()

        # Create backup
        backup_filename = backup_manager.create_backup()
        assert backup_filename is not None

        # Verify backup contains encrypted data
        backup_path = os.path.join(env["backup_dir"], backup_filename)
        with open(backup_path, "r", encoding="utf-8") as f:
            backup_data = json.load(f)

        traveler_data = backup_data["tables"]["travelers"]["data"][0]
        backed_up_email = traveler_data[10]  # email field
        backed_up_phone = traveler_data[11]  # phone field
        backed_up_license = traveler_data[12]  # license field

        # Backup should contain encrypted data (not plaintext)
        assert backed_up_email != "highly.sensitive@classified.gov"
        assert backed_up_phone != "+31 6 99999999"
        assert backed_up_license != "SD9999999"

        # But should be the same encrypted values
        assert backed_up_email == original_encrypted_data[0]
        assert backed_up_phone == original_encrypted_data[1]
        assert backed_up_license == original_encrypted_data[2]

        # Clear database and restore
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM travelers")
            conn.commit()

        # Restore backup
        with patch("builtins.input", return_value="RESTORE"):
            restore_success = backup_manager.restore_backup(backup_filename)

        assert restore_success is True

        # Verify restored data can be decrypted correctly
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT email, mobile_phone, driving_license FROM travelers WHERE customer_id = ?",
                ("CUST000001",),
            )
            restored_encrypted_data = cursor.fetchone()

        # Decrypt and verify
        restored_email = decrypt_field(restored_encrypted_data[0])
        restored_phone = decrypt_field(restored_encrypted_data[1])
        restored_license = decrypt_field(restored_encrypted_data[2])

        assert restored_email == "highly.sensitive@classified.gov"
        assert restored_phone == "+31 6 99999999"
        assert restored_license == "SD9999999"

    def test_restore_code_workflow(self, test_environment):
        """Test complete restore code workflow"""
        env = test_environment
        backup_manager = env["backup_manager"]

        # Create test data and backup
        test_traveler = {
            "customer_id": "CUST000001",
            "first_name": "Test",
            "last_name": "User",
            "birthday": "01-01-1990",
            "gender": "Male",
            "street_name": "Test Street",
            "house_number": "1",
            "zip_code": "1234AB",
            "city": "Amsterdam",
            "email": "test@example.com",
            "mobile_phone": "+31 6 12345678",
            "driving_license": "TU1234567",
            "registration_date": datetime.now().isoformat(),
        }
        env["db"].insert_traveler(test_traveler)

        backup_filename = backup_manager.create_backup()
        assert backup_filename is not None

        # Generate restore code
        restore_code = backup_manager.generate_restore_code(backup_filename)
        assert restore_code is not None
        assert len(restore_code) == 12

        # Verify restore code is stored
        assert restore_code in backup_manager.restore_codes
        assert (
            backup_manager.restore_codes[restore_code]["backup_file"] == backup_filename
        )
        assert backup_manager.restore_codes[restore_code]["used"] is False

        # Modify database
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM travelers")
            conn.commit()

        # Create system admin user for testing restore code usage
        import hashlib

        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            password_hash = hashlib.sha256("SysAdmin123!".encode()).hexdigest()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
                (
                    "test_sysadmin",
                    password_hash,
                    "system_admin",
                    "Test",
                    "SysAdmin",
                    datetime.now().isoformat(),
                    1,
                ),
            )
            conn.commit()

        # Login as system admin
        env["auth"].logout()
        login_success = env["auth"].login("test_sysadmin", "SysAdmin123!")
        assert login_success is True

        # Create new backup manager instance for system admin
        sysadmin_backup_manager = BackupManager(env["auth"])
        sysadmin_backup_manager.backup_dir = env["backup_dir"]

        # Transfer restore codes to new instance
        sysadmin_backup_manager.restore_codes = backup_manager.restore_codes

        # Verify system admin can use restore code
        assert sysadmin_backup_manager.can_use_restore_code() is True
        assert sysadmin_backup_manager.can_restore_backup() is False

        # Restore using code
        with patch("builtins.input", return_value="RESTORE"):
            restore_success = sysadmin_backup_manager.restore_backup(
                backup_filename, restore_code
            )

        assert restore_success is True

        # Verify data was restored
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM travelers")
            count = cursor.fetchone()[0]

        assert count == 1

        # Verify restore code was marked as used
        assert sysadmin_backup_manager.restore_codes[restore_code]["used"] is True

        # Try to use the same code again (should fail)
        with patch("builtins.input", return_value="RESTORE"):
            second_restore = sysadmin_backup_manager.restore_backup(
                backup_filename, restore_code
            )

        assert second_restore is False

    def test_multiple_backups_management(self, test_environment):
        """Test managing multiple backups"""
        env = test_environment
        backup_manager = env["backup_manager"]

        # Create multiple backups with different timestamps
        backup_files = []

        for i in range(3):
            # Add unique data for each backup
            test_traveler = {
                "customer_id": f"CUST00000{i+1}",
                "first_name": f"User{i+1}",
                "last_name": f"Test{i+1}",
                "birthday": "01-01-1990",
                "gender": "Male",
                "street_name": f"Street {i+1}",
                "house_number": str(i + 1),
                "zip_code": f"{1000+i:04d}AB",
                "city": "Amsterdam",
                "email": f"user{i+1}@example.com",
                "mobile_phone": f"+31 6 {12345678+i}",
                "driving_license": f"U{i+1}1234567",
                "registration_date": datetime.now().isoformat(),
            }
            env["db"].insert_traveler(test_traveler)

            # Create backup
            backup_filename = backup_manager.create_backup()
            assert backup_filename is not None
            backup_files.append(backup_filename)

            # Small delay to ensure different timestamps
            import time

            time.sleep(1)

        # List backups
        available_backups = backup_manager.list_backups()

        # Should have all created backups
        assert len(available_backups) == 3
        for backup_file in backup_files:
            assert backup_file in available_backups

        # Backups should be sorted newest first
        assert available_backups == sorted(backup_files, reverse=True)

        # Test backup info for each backup
        for backup_file in backup_files:
            backup_info = backup_manager.show_backup_info(backup_file)
            assert backup_info is not None
            assert "created_at" in backup_info
            assert "created_by" in backup_info
            assert backup_info["created_by"] == "super_admin"

        # Test restore from specific backup
        # Choose the first backup (should have 1 traveler)
        first_backup = backup_files[0]

        with patch("builtins.input", return_value="RESTORE"):
            restore_success = backup_manager.restore_backup(first_backup)

        assert restore_success is True

        # Verify correct data was restored
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM travelers")
            count = cursor.fetchone()[0]

        assert count == 1  # Only one traveler from first backup

    def test_backup_restore_with_database_constraints(self, test_environment):
        """Test backup/restore respects database constraints"""
        env = test_environment
        backup_manager = env["backup_manager"]

        # Get initial user count (super_admin exists)
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            initial_user_count = cursor.fetchone()[0]

        # Add user data
        import hashlib

        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            password_hash = hashlib.sha256("TestUser123!".encode()).hexdigest()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, role, first_name, last_name, created_date, created_by, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
                (
                    "test_user",
                    password_hash,
                    "system_admin",
                    "Test",
                    "User",
                    datetime.now().isoformat(),
                    1,  # created_by super_admin
                ),
            )
            conn.commit()

        # Create backup
        backup_filename = backup_manager.create_backup()
        assert backup_filename is not None

        # Verify backup contains relational data
        backup_path = os.path.join(env["backup_dir"], backup_filename)
        with open(backup_path, "r", encoding="utf-8") as f:
            backup_data = json.load(f)

        users_data = backup_data["tables"]["users"]["data"]
        assert len(users_data) == initial_user_count + 1

        # Find the test user in backup
        test_user_row = None
        for user_row in users_data:
            if user_row[1] == "test_user":  # username field
                test_user_row = user_row
                break

        assert test_user_row is not None
        assert test_user_row[7] == 1  # created_by field

        # Restore and verify foreign key relationships
        with patch("builtins.input", return_value="RESTORE"):
            restore_success = backup_manager.restore_backup(backup_filename)

        assert restore_success is True

        # Verify relationships are maintained
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT u1.username, u2.username as created_by_username
                FROM users u1
                LEFT JOIN users u2 ON u1.created_by = u2.id
                WHERE u1.username = ?
            """,
                ("test_user",),
            )
            relationship_data = cursor.fetchone()

        assert relationship_data is not None
        assert relationship_data[0] == "test_user"
        assert relationship_data[1] == "super_admin"  # created_by relationship

    def test_backup_error_handling_and_recovery(self, test_environment):
        """Test backup system error handling and recovery"""
        env = test_environment
        backup_manager = env["backup_manager"]

        # Test handling of corrupted backup file
        corrupt_backup_path = os.path.join(env["backup_dir"], "corrupt_backup.json")
        with open(corrupt_backup_path, "w") as f:
            f.write("{ invalid json content")

        # Should handle corrupted backup gracefully
        backup_info = backup_manager.show_backup_info("corrupt_backup.json")
        assert backup_info is None

        # Test restore from non-existent backup
        restore_result = backup_manager.restore_backup("nonexistent.json")
        assert restore_result is False

        # Test backup directory permission issues (simulate)
        original_backup_dir = backup_manager.backup_dir
        backup_manager.backup_dir = (
            "/root/no_permission"  # Directory that doesn't exist
        )

        with patch("os.makedirs", side_effect=PermissionError("Permission denied")):
            # Should handle permission errors gracefully
            backup_result = backup_manager.create_backup()
            assert backup_result is None

        # Restore original backup directory
        backup_manager.backup_dir = original_backup_dir

        # Test successful backup after error recovery
        backup_filename = backup_manager.create_backup()
        assert backup_filename is not None

    def test_concurrent_backup_operations_simulation(self, test_environment):
        """Test simulation of concurrent backup operations"""
        env = test_environment
        backup_manager = env["backup_manager"]

        # Add test data
        test_traveler = {
            "customer_id": "CUST000001",
            "first_name": "Concurrent",
            "last_name": "Test",
            "birthday": "01-01-1990",
            "gender": "Male",
            "street_name": "Concurrent Street",
            "house_number": "1",
            "zip_code": "1234AB",
            "city": "Amsterdam",
            "email": "concurrent@example.com",
            "mobile_phone": "+31 6 12345678",
            "driving_license": "CT1234567",
            "registration_date": datetime.now().isoformat(),
        }
        env["db"].insert_traveler(test_traveler)

        # Simulate multiple backup operations with time delays to ensure unique timestamps
        backup_files = []

        # Create multiple backups with forced time differences
        for i in range(3):
            # Mock datetime to ensure different timestamps
            with patch("managers.backup_manager.datetime") as mock_dt:
                mock_dt.now.return_value.strftime.return_value = f"20250620_11594{i+4}"
                mock_dt.now.return_value.isoformat.return_value = (
                    f"2025-06-20T11:59:4{i+4}"
                )

                backup_filename = backup_manager.create_backup()
                assert backup_filename is not None
                backup_files.append(backup_filename)

        # Verify each backup file is unique
        assert (
            len(set(backup_files)) == 3
        ), f"Expected unique filenames but got: {backup_files}"

        # Verify all backups are valid and contain data
        for backup_file in backup_files:
            backup_info = backup_manager.show_backup_info(backup_file)
            assert backup_info is not None
            assert len(backup_info["tables"]["travelers"]["data"]) == 1

        # Test restore from each backup
        for backup_file in backup_files:
            with patch("builtins.input", return_value="RESTORE"):
                restore_success = backup_manager.restore_backup(backup_file)
            assert restore_success is True

            # Verify data consistency after each restore
            with env["db"].get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM travelers")
                count = cursor.fetchone()[0]
            assert count == 1

    def test_backup_system_performance(self, test_environment):
        """Test backup system performance with larger datasets"""
        env = test_environment
        backup_manager = env["backup_manager"]

        import time

        # Create larger dataset
        travelers_count = 50
        start_time = time.time()

        for i in range(travelers_count):
            traveler = {
                "customer_id": f"CUST{i:06d}",
                "first_name": f"User{i}",
                "last_name": f"Test{i}",
                "birthday": "01-01-1990",
                "gender": "Male" if i % 2 == 0 else "Female",
                "street_name": f"Street {i}",
                "house_number": str(i + 1),
                "zip_code": f"{1000 + i:04d}AB",
                "city": (
                    env["backup_manager"].validator.VALID_CITIES[i % 10]
                    if hasattr(env["backup_manager"], "validator")
                    else "Amsterdam"
                ),
                "email": f"user{i}@performance.test",
                "mobile_phone": f"+31 6 {i:08d}",
                "driving_license": f"PF{i:07d}",
                "registration_date": datetime.now().isoformat(),
            }
            env["db"].insert_traveler(traveler)

        data_creation_time = time.time() - start_time

        # Test backup performance
        start_time = time.time()
        backup_filename = backup_manager.create_backup()
        backup_time = time.time() - start_time

        assert backup_filename is not None
        assert backup_time < 10.0, f"Backup took too long: {backup_time}s"

        # Test restore performance
        start_time = time.time()
        with patch("builtins.input", return_value="RESTORE"):
            restore_success = backup_manager.restore_backup(backup_filename)
        restore_time = time.time() - start_time

        assert restore_success is True
        assert restore_time < 15.0, f"Restore took too long: {restore_time}s"

        # Verify data integrity after performance test
        with env["db"].get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM travelers")
            final_count = cursor.fetchone()[0]

        assert final_count == travelers_count

        print(f"Performance test completed:")
        print(
            f"  Data creation: {data_creation_time:.2f}s for {travelers_count} records"
        )
        print(f"  Backup time: {backup_time:.2f}s")
        print(f"  Restore time: {restore_time:.2f}s")
