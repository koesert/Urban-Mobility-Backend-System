from data.db_context import DatabaseContext
from data.encryption import decrypt_field

db = DatabaseContext()

# Insert a traveler
traveler = {
    "customer_id": "CUST001",
    "first_name": "Alice",
    "last_name": "Smith",
    "birthday": "1990-01-01",
    "gender": "F",
    "street_name": "Main St",
    "house_number": "1",
    "zip_code": "12345",
    "city": "Amsterdam",
    "email": "alice@example.com",
    "mobile_phone": "+31612345678",
    "driving_license": "DL123456",
    "registration_date": "2025-06-11",
}
db.insert_traveler(traveler)

# Fetch and decrypt
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT email, mobile_phone, driving_license FROM travelers WHERE customer_id = ?", ("CUST001",))
    row = cursor.fetchone()
    print("Encrypted:", row)
    print("Decrypted:", [decrypt_field(val) for val in row])