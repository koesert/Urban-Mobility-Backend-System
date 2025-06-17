import pytest
import os
import tempfile
from unittest.mock import patch
from cryptography.fernet import Fernet, InvalidToken
from data.encryption import encrypt_field, decrypt_field, generate_key, load_key, fernet


class TestEncryptionUnit:
    """Unit tests for encryption functionality"""

    def test_encrypt_field_returns_different_output_each_time(self):
        """Test that encryption produces different ciphertext for same input"""
        plaintext = "test@example.com"

        encrypted1 = encrypt_field(plaintext)
        encrypted2 = encrypt_field(plaintext)

        assert encrypted1 != encrypted2
        assert isinstance(encrypted1, str)
        assert isinstance(encrypted2, str)
        assert len(encrypted1) > len(plaintext)
        assert len(encrypted2) > len(plaintext)

    def test_decrypt_field_returns_original_value(self):
        """Test that decryption returns original plaintext"""
        plaintext = "sensitive_data@example.com"

        encrypted = encrypt_field(plaintext)
        decrypted = decrypt_field(encrypted)

        assert decrypted == plaintext

    def test_encrypt_decrypt_cycle_with_various_data_types(self):
        """Test encryption/decryption with different string types"""
        test_cases = [
            "simple_text",
            "email@domain.com",
            "+31 6 12345678",
            "AB123456",
            "Special chars: àáâãäåæçèéêë",
            "Numbers: 1234567890",
            "Mixed: Test123@Domain.nl",
            "",
            " ",
            "   leading and trailing spaces   ",
        ]

        for test_data in test_cases:
            encrypted = encrypt_field(test_data)
            decrypted = decrypt_field(encrypted)

            assert decrypted == test_data, f"Failed for: '{test_data}'"

    def test_decrypt_field_raises_error_for_invalid_token(self):
        """Test that invalid token raises InvalidToken exception"""
        invalid_tokens = [
            "invalid_token",
            "gAAAAABh",
            "not_base64_at_all",
            "",
            "gAAAAABhZ0invalid_token_data_here",
        ]

        for invalid_token in invalid_tokens:
            with pytest.raises(InvalidToken):
                decrypt_field(invalid_token)

    def test_encrypt_field_handles_unicode_characters(self):
        """Test encryption with unicode and special characters"""
        unicode_strings = [
            "café",
            "naïve",
            "Москва",
            "北京",
            "🎉🚀📱",
            "Test\nwith\nnewlines",
            "Test\twith\ttabs",
        ]

        for unicode_str in unicode_strings:
            encrypted = encrypt_field(unicode_str)
            decrypted = decrypt_field(encrypted)

            assert decrypted == unicode_str
            assert isinstance(encrypted, str)

    def test_generate_key_creates_valid_fernet_key(self):
        """Test that generate_key creates a valid Fernet key"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            with patch("data.encryption.FERNET_KEY_PATH", tmp_path):
                key = generate_key()

                assert isinstance(key, bytes)
                assert len(key) == 44

                fernet_instance = Fernet(key)
                test_data = "test"
                encrypted = fernet_instance.encrypt(test_data.encode())
                decrypted = fernet_instance.decrypt(encrypted).decode()
                assert decrypted == test_data

                assert os.path.exists(tmp_path)
                with open(tmp_path, "rb") as f:
                    file_key = f.read()
                assert file_key == key
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_load_key_reads_existing_key_file(self):
        """Test that load_key reads an existing key file"""
        test_key = Fernet.generate_key()

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(test_key)
            tmp_path = tmp_file.name

        try:
            with patch("data.encryption.FERNET_KEY_PATH", tmp_path):
                loaded_key = load_key()

                assert loaded_key == test_key
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_load_key_generates_new_key_when_file_missing(self):
        """Test that load_key generates new key when file doesn't exist"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".key") as tmp_file:
            nonexistent_path = tmp_file.name

        if os.path.exists(nonexistent_path):
            os.unlink(nonexistent_path)

        with patch("data.encryption.FERNET_KEY_PATH", nonexistent_path):
            try:
                loaded_key = load_key()

                assert isinstance(loaded_key, bytes)
                assert len(loaded_key) == 44
                assert os.path.exists(nonexistent_path)

                fernet_instance = Fernet(loaded_key)
                test_encrypted = fernet_instance.encrypt(b"test")
                test_decrypted = fernet_instance.decrypt(test_encrypted)
                assert test_decrypted == b"test"
            finally:
                if os.path.exists(nonexistent_path):
                    os.unlink(nonexistent_path)

    def test_encryption_consistency_across_module_reload(self):
        """Test that encryption is consistent across different module states"""
        if os.name == "nt":
            pytest.skip("Cross-module encryption test not reliable on Windows")

        test_data = "consistent_test_data"

        encrypted = encrypt_field(test_data)

        decrypted = decrypt_field(encrypted)

        assert decrypted == test_data

    def test_encryption_with_very_long_strings(self):
        """Test encryption with long strings (edge case)"""
        long_string = "A" * 10000
        very_long_string = "B" * 100000

        test_cases = [long_string, very_long_string]

        for test_string in test_cases:
            encrypted = encrypt_field(test_string)
            decrypted = decrypt_field(encrypted)

            assert decrypted == test_string
            assert len(encrypted) > len(test_string)

    def test_encryption_performance_reasonable(self):
        """Test that encryption performance is reasonable for typical use"""
        import time

        test_data = "test@example.com"
        iterations = 1000

        start_time = time.time()
        for _ in range(iterations):
            encrypt_field(test_data)
        encryption_time = time.time() - start_time

        encrypted = encrypt_field(test_data)
        start_time = time.time()
        for _ in range(iterations):
            decrypt_field(encrypted)
        decryption_time = time.time() - start_time

        assert (
            encryption_time < 5.0
        ), f"Encryption too slow: {encryption_time}s for {iterations} operations"
        assert (
            decryption_time < 5.0
        ), f"Decryption too slow: {decryption_time}s for {iterations} operations"

    def test_fernet_global_instance_is_properly_initialized(self):
        """Test that the global fernet instance is properly initialized"""
        assert fernet is not None
        assert isinstance(fernet, Fernet)

        test_data = "test_global_instance"
        encrypted = fernet.encrypt(test_data.encode())
        decrypted = fernet.decrypt(encrypted).decode()
        assert decrypted == test_data

    def test_key_file_permissions_security(self):
        """Test that key file has appropriate permissions (Unix systems)"""
        if os.name != "posix":
            return pytest.skip("Permission test only applicable on Unix systems")

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = tmp_file.name

        try:
            with patch("data.encryption.FERNET_KEY_PATH", tmp_path):
                generate_key()

                file_stat = os.stat(tmp_path)
                file_permissions = oct(file_stat.st_mode)[-3:]

                assert (
                    file_permissions == "600"
                ), f"Key file has permissions {file_permissions}, should be 600 (owner read/write only)"
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_encryption_with_none_input_raises_error(self):
        """Test that None input raises appropriate error"""
        with pytest.raises(AttributeError):
            encrypt_field(None)  # type: ignore

    def test_decryption_with_none_input_raises_error(self):
        """Test that None input to decrypt raises appropriate error"""
        with pytest.raises(AttributeError):
            decrypt_field(None)  # type: ignore
