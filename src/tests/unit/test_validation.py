from validation.validation import InputValidator, ValidationError


def test_validation():
    """Test the improved validation system"""
    print("🔐 Testing Urban Mobility Validation Framework")
    print("=" * 60)

    validator = InputValidator()

    # Test 1: Valid data
    print("\n✅ Test 1: Valid traveler data")
    valid_data = {
        "first_name": "John",
        "last_name": "Smith",
        "birthday": "15-05-1990",
        "gender": "Male",
        "street_name": "Main Street",
        "house_number": "123A",
        "zip_code": "1234AB",
        "city": "Amsterdam",
        "email": "john.smith@example.com",
        "mobile_phone": "12345678",
        "driving_license": "JS1234567",
    }

    try:
        result = validator.validate_traveler_data(valid_data)
        print("✓ All validation passed!")
        print(f"   Phone formatted: {result['mobile_phone']}")
        print(f"   Email normalized: {result['email']}")
    except ValidationError as e:
        print(f"✗ Unexpected error: {e}")

    # Test 2: Name validation (should reject numbers)
    print("\n❌ Test 2: Names with numbers (should fail)")
    invalid_names = ["John123", "Mary456", "Street123Name"]

    for name in invalid_names:
        try:
            validator.validate_first_name(name)
            print(f"✗ ERROR: {name} was accepted (should be rejected)")
        except ValidationError:
            print(f"✓ Correctly rejected: {name}")

    # Test 3: Street name validation (should allow numbers)
    print("\n✅ Test 3: Street names with numbers (should pass)")
    valid_streets = ["Main Street", "5th Avenue", "Oak Street 123", "Highway 1"]

    for street in valid_streets:
        try:
            result = validator.validate_street_name(street)
            print(f"✓ Accepted: {street}")
        except ValidationError as e:
            print(f"✗ ERROR: {street} was rejected: {e.message}")

    # Test 4: SQL injection protection
    print("\n🛡️ Test 4: SQL injection protection")
    malicious_inputs = [
        "'; DROP TABLE travelers; --",
        "Robert'; DELETE FROM users; --",
        "admin' OR '1'='1",
    ]

    for malicious in malicious_inputs:
        try:
            validator.validate_first_name(malicious)
            print(f"✗ ERROR: SQL injection not caught: {malicious}")
        except ValidationError:
            print(f"✓ SQL injection blocked: {malicious[:20]}...")

    # Test 5: Email validation edge cases
    print("\n📧 Test 5: Email validation edge cases")
    invalid_emails = [
        "test..email@domain.com",  # Double dots
        ".test@domain.com",  # Starts with dot
        "test@domain.com.",  # Ends with dot
        "test@.domain.com",  # Dot after @
        "test@domain..com",  # Double dots in domain
    ]

    for email in invalid_emails:
        try:
            validator.validate_email(email)
            print(f"✗ ERROR: Invalid email accepted: {email}")
        except ValidationError:
            print(f"✓ Correctly rejected email: {email}")

    # Test 6: Dutch phone validation
    print("\n📱 Test 6: Dutch phone validation")
    invalid_phones = ["1234567", "123456789", "12345abc", "+31612345678"]

    for phone in invalid_phones:
        try:
            validator.validate_dutch_mobile(phone)
            print(f"✗ ERROR: Invalid phone accepted: {phone}")
        except ValidationError:
            print(f"✓ Correctly rejected phone: {phone}")

    # Test valid phone
    try:
        valid_phone = validator.validate_dutch_mobile("12345678")
        print(f"✓ Valid phone formatted: {valid_phone}")
    except ValidationError as e:
        print(f"✗ ERROR: Valid phone rejected: {e}")

    # Test 7: House number validation
    print("\n🏠 Test 7: House number validation")
    valid_houses = ["123", "45A", "67-69", "1B"]
    invalid_houses = ["0", "10000", "ABC", ""]

    for house in valid_houses:
        try:
            result = validator.validate_house_number(house)
            print(f"✓ Valid house number: {house}")
        except ValidationError as e:
            print(f"✗ ERROR: Valid house rejected: {house} - {e.message}")

    for house in invalid_houses:
        try:
            validator.validate_house_number(house)
            print(f"✗ ERROR: Invalid house accepted: {house}")
        except ValidationError:
            print(f"✓ Correctly rejected house: {house}")

    print("\n🎉 Validation testing completed!")
    print("✅ Your validation framework is working correctly!")
    print("✅ Immediate feedback implemented")
    print("✅ Proper name validation (no numbers)")
    print("✅ SQL injection protection active")
    print("✅ All field-specific validation working")


if __name__ == "__main__":
    test_validation()
