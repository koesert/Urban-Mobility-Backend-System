from cryptography.fernet import Fernet
import base64
import os

# You should store this key securely!
FERNET_KEY_PATH = os.getenv("FERNET_KEY_PATH", "fernet.key")

def generate_key():
    key = Fernet.generate_key()
    with open(FERNET_KEY_PATH, "wb") as f:
        f.write(key)
    return key

def load_key():
    if not os.path.exists(FERNET_KEY_PATH):
        return generate_key()
    with open(FERNET_KEY_PATH, "rb") as f:
        return f.read()

fernet = Fernet(load_key())

def encrypt_field(value: str) -> str:
    return fernet.encrypt(value.encode()).decode()

def decrypt_field(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()