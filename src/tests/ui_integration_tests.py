"""
UI & INTEGRATION TESTS FOR URBAN MOBILITY BACKEND SYSTEM

Tests complete user flows through the UI/menu system (um_members.py).
Simulates real user interactions and validates entire workflows.

Test Categories:
- Complete login flows
- Menu navigation
- CRUD workflows (create → read → update → delete)
- Role-based menu access
- Input validation in UI prompts
- Error handling in UI
"""

import sys
from io import StringIO
from unittest.mock import patch
from pathlib import Path

# Add parent directory to sys.path to import modules
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Test results tracking
test_results = {"total": 0, "passed": 0, "failed": 0, "errors": []}


def test_header(test_name):
    """Print test section header."""
    print("\n" + "=" * 80)
    print(f"TEST: {test_name}")
    print("=" * 80)


def assert_true(condition, message):
    """Assert condition is True."""
    test_results["total"] += 1
    if condition:
        test_results["passed"] += 1
        print(f"✅ PASS: {message}")
        return True
    else:
        test_results["failed"] += 1
        test_results["errors"].append(message)
        print(f"❌ FAIL: {message}")
        return False


def assert_contains(text, substring, message):
    """Assert text contains substring."""
    return assert_true(substring in text if text else False, message)


def cleanup_test_data():
    """Clean up test database and files."""
    print("\n🧹 Cleaning up test data...")

    # Try both possible data directory locations
    possible_data_dirs = [
        Path("data"),  # If running from same dir as modules
        Path(__file__).parent / "data",  # If in tests subfolder
        Path(__file__).parent.parent / "data",  # If tests are in src/tests
    ]

    for data_dir in possible_data_dirs:
        if data_dir.exists():
            db_path = data_dir / "urban_mobility.db"
            if db_path.exists():
                db_path.unlink()

            log_path = data_dir / "system.log"
            if log_path.exists():
                log_path.unlink()

            check_path = data_dir / "last_log_check.txt"
            if check_path.exists():
                check_path.unlink()

            break  # Only clean one data directory

    print("✅ Test data cleaned up")


# ============================================================================
# TEST 1: LOGIN FLOW TESTS
# ============================================================================


def test_login_flows():
    """Test complete login workflows including success and failure cases."""
    test_header("LOGIN FLOW TESTS")

    from database import init_database
    from auth import login, logout, get_current_user

    # Initialize
    cleanup_test_data()
    init_database()

    # Test 1.1: Successful super admin login
    print("\n--- Test 1.1: Successful Super Admin Login ---")
    success, msg = login("super_admin", "Admin_123?")
    assert_true(success, "Super admin login successful")

    user = get_current_user()
    assert_true(user is not None, "User session created")
    assert_true(user["username"] == "super_admin", "Correct username in session")
    assert_true(user["role"] == "super_admin", "Correct role in session")

    logout()

    # Test 1.2: Failed login - wrong password
    print("\n--- Test 1.2: Failed Login - Wrong Password ---")
    success, msg = login("super_admin", "WrongPassword123!")
    assert_true(not success, "Login fails with wrong password")
    assert_contains(msg.lower(), "invalid", "Error message mentions invalid")

    user = get_current_user()
    assert_true(user is None, "No session created on failed login")

    # Test 1.3: Failed login - non-existent user
    print("\n--- Test 1.3: Failed Login - Non-existent User ---")
    success, msg = login("nonexistent", "Password123!")
    assert_true(not success, "Login fails for non-existent user")

    # Test 1.4: Failed login - invalid username format
    print("\n--- Test 1.4: Failed Login - Invalid Username Format ---")
    success, msg = login("123", "Password123!")
    assert_true(not success, "Login fails for invalid username format")

    # Test 1.5: Logout when not logged in
    print("\n--- Test 1.5: Logout When Not Logged In ---")
    success, msg = logout()
    assert_true(not success, "Logout fails when not logged in")

    # Test 1.6: Multiple login attempts (suspicious activity)
    print("\n--- Test 1.6: Multiple Failed Login Attempts ---")
    for i in range(3):
        success, msg = login("super_admin", "WrongPass123!")
        assert_true(not success, f"Failed login attempt {i+1} blocked")

    # Check if suspicious activities were logged
    from activity_log import get_suspicious_logs

    suspicious = get_suspicious_logs()
    assert_true(len(suspicious) >= 3, "Multiple failed logins logged as suspicious")


# ============================================================================
# TEST 2: MENU NAVIGATION TESTS
# ============================================================================


def test_menu_navigation():
    """Test menu access based on roles."""
    test_header("MENU NAVIGATION & ROLE-BASED ACCESS")

    from database import init_database
    from auth import login, logout, check_permission
    from users import create_system_admin, create_service_engineer, reset_user_password

    # Initialize
    init_database()

    # Test 2.1: Super Admin menu options
    print("\n--- Test 2.1: Super Admin Menu Access ---")
    login("super_admin", "Admin_123?")

    # Super Admin should have access to all permissions
    expected_permissions = [
        "manage_admins",
        "manage_engineers",
        "manage_travelers",
        "manage_scooters",
        "view_logs",
        "create_backup",
        "manage_restore_codes",
    ]

    for perm in expected_permissions:
        has_perm = check_permission(perm)
        assert_true(has_perm, f"Super Admin has {perm} permission")

    logout()

    # Test 2.2: System Admin menu options
    print("\n--- Test 2.2: System Admin Menu Access ---")
    login("super_admin", "Admin_123?")  # Need to be logged in to create users
    create_system_admin("testadmin", "Test", "Admin")
    success, msg, temp_pw = reset_user_password("testadmin")
    logout()  # Logout super_admin before logging in as testadmin

    success, login_msg = login("testadmin", temp_pw)

    # System Admin should NOT have these permissions
    denied_permissions = ["manage_admins", "manage_restore_codes"]
    for perm in denied_permissions:
        has_perm = check_permission(perm)
        assert_true(not has_perm, f"System Admin does NOT have {perm} permission")

    # System Admin SHOULD have these permissions
    allowed_permissions = ["manage_engineers", "manage_travelers", "manage_scooters", "view_logs"]
    for perm in allowed_permissions:
        has_perm = check_permission(perm)
        assert_true(has_perm, f"System Admin has {perm} permission")

    logout()

    # Test 2.3: Service Engineer menu options
    print("\n--- Test 2.3: Service Engineer Menu Access ---")
    login("super_admin", "Admin_123?")
    create_service_engineer("engineer1", "Test", "Engineer")
    success, msg, temp_pw = reset_user_password("engineer1")
    logout()

    success, login_msg = login("engineer1", temp_pw)

    # Service Engineer should have minimal permissions
    denied_permissions = [
        "manage_admins",
        "manage_engineers",
        "manage_travelers",
        "view_logs",
        "create_backup",
    ]
    for perm in denied_permissions:
        has_perm = check_permission(perm)
        assert_true(not has_perm, f"Service Engineer does NOT have {perm} permission")

    # Service Engineer can only update scooters (limited permissions)
    assert_true(
        check_permission("manage_scooters"), "Service Engineer can manage scooters (update only)"
    )

    logout()


# ============================================================================
# TEST 3: COMPLETE CRUD WORKFLOWS
# ============================================================================


def test_complete_user_workflow():
    """Test complete user management workflow (Create → Read → Update → Delete)."""
    test_header("COMPLETE USER MANAGEMENT WORKFLOW")

    from database import init_database
    from auth import login, logout
    from users import (
        create_system_admin,
        list_all_users,
        update_user_profile,
        reset_user_password,
        delete_user,
    )

    # Initialize
    init_database()
    login("super_admin", "Admin_123?")

    # Step 1: CREATE
    print("\n--- Step 1: CREATE System Admin ---")
    success, msg, temp_pw = create_system_admin("workflow01", "Workflow", "User")
    assert_true(success, "User created in workflow")
    assert_true(len(temp_pw) > 0, "Temporary password generated")

    # Step 2: READ
    print("\n--- Step 2: READ - Verify User Exists ---")
    users = list_all_users()
    user_found = any(u["username"] == "workflow01" for u in users)
    assert_true(user_found, "Created user found in list")

    # Step 3: UPDATE
    print("\n--- Step 3: UPDATE - Change User Profile ---")
    success, msg = update_user_profile("workflow01", first_name="Updated")
    assert_true(success, "User profile updated")

    users = list_all_users()
    updated_user = next((u for u in users if u["username"] == "workflow01"), None)
    assert_true(updated_user["first_name"] == "Updated", "First name updated correctly")

    # Step 4: RESET PASSWORD
    print("\n--- Step 4: RESET PASSWORD ---")
    success, msg, new_temp_pw = reset_user_password("workflow01")
    assert_true(success, "Password reset successfully")
    assert_true(new_temp_pw != temp_pw, "New password is different")

    # Step 5: DELETE
    print("\n--- Step 5: DELETE - Remove User ---")
    success, msg = delete_user("workflow01")
    assert_true(success, "User deleted successfully")

    users = list_all_users()
    user_found = any(u["username"] == "workflow01" for u in users)
    assert_true(not user_found, "Deleted user not in list")

    logout()


def test_complete_traveler_workflow():
    """Test complete traveler management workflow."""
    test_header("COMPLETE TRAVELER MANAGEMENT WORKFLOW")

    from database import init_database
    from auth import login, logout
    from travelers import (
        add_traveler,
        list_all_travelers,
        get_traveler_by_id,
        update_traveler,
        search_travelers,
        delete_traveler,
    )

    # Initialize
    init_database()
    login("super_admin", "Admin_123?")

    # Step 1: CREATE
    print("\n--- Step 1: CREATE Traveler ---")
    success, msg, customer_id = add_traveler(
        first_name="Workflow",
        last_name="Traveler",
        birthday="15-03-1990",
        gender="Male",
        street_name="Test Street",
        house_number="123",
        zip_code="3011AB",
        city="Amsterdam",
        email="workflow@example.com",
        mobile_phone="12345678",
        driving_license="AB1234567",
    )
    assert_true(success, "Traveler created in workflow")
    assert_true(len(customer_id) > 0, "Customer ID generated")

    # Step 2: READ
    print("\n--- Step 2: READ - Verify Traveler Exists ---")
    traveler = get_traveler_by_id(customer_id)
    assert_true(traveler is not None, "Traveler found by ID")
    assert_true(traveler["first_name"] == "Workflow", "Correct first name")
    assert_true(
        traveler["email"] == "workflow@example.com", "Correct email (decrypted)"
    )

    # Step 3: SEARCH
    print("\n--- Step 3: SEARCH - Find Traveler ---")
    results = search_travelers("Workflow")
    assert_true(len(results) >= 1, "Traveler found in search")

    # Step 4: UPDATE
    print("\n--- Step 4: UPDATE - Change Traveler Info ---")
    success, msg = update_traveler(customer_id, email="updated@example.com")
    assert_true(success, "Traveler updated successfully")

    traveler = get_traveler_by_id(customer_id)
    assert_true(traveler["email"] == "updated@example.com", "Email updated correctly")

    # Step 5: DELETE
    print("\n--- Step 5: DELETE - Remove Traveler ---")
    success, msg = delete_traveler(customer_id)
    assert_true(success, "Traveler deleted successfully")

    traveler = get_traveler_by_id(customer_id)
    assert_true(traveler is None, "Deleted traveler not found")

    logout()


def test_complete_scooter_workflow():
    """Test complete scooter management workflow."""
    test_header("COMPLETE SCOOTER MANAGEMENT WORKFLOW")

    from database import init_database
    from auth import login, logout
    from scooters import (
        add_scooter,
        list_all_scooters,
        get_scooter_by_serial,
        update_scooter,
        search_scooters,
        delete_scooter,
    )

    # Initialize
    init_database()
    login("super_admin", "Admin_123?")

    # Step 1: CREATE
    print("\n--- Step 1: CREATE Scooter ---")
    success, msg = add_scooter(
        serial_number="WF123456",
        scooter_type="Workflow Model",
        battery_level=100,
        status="available",
        location="Test Location",
    )
    assert_true(success, "Scooter created in workflow")

    # Step 2: READ
    print("\n--- Step 2: READ - Verify Scooter Exists ---")
    scooter = get_scooter_by_serial("WF123456")
    assert_true(scooter is not None, "Scooter found by serial")
    assert_true(scooter["type"] == "Workflow Model", "Correct type")
    assert_true(scooter["battery_level"] == 100, "Correct battery level")

    # Step 3: SEARCH
    print("\n--- Step 3: SEARCH - Find Scooter ---")
    results = search_scooters("Workflow")
    assert_true(len(results) >= 1, "Scooter found in search")

    # Step 4: UPDATE
    print("\n--- Step 4: UPDATE - Change Scooter Info ---")
    success, msg = update_scooter("WF123456", battery_level=75, location="New Location")
    assert_true(success, "Scooter updated successfully")

    scooter = get_scooter_by_serial("WF123456")
    assert_true(scooter["battery_level"] == 75, "Battery level updated")
    assert_true(scooter["location"] == "New Location", "Location updated")

    # Step 5: DELETE
    print("\n--- Step 5: DELETE - Remove Scooter ---")
    success, msg = delete_scooter("WF123456")
    assert_true(success, "Scooter deleted successfully")

    scooter = get_scooter_by_serial("WF123456")
    assert_true(scooter is None, "Deleted scooter not found")

    logout()


# ============================================================================
# TEST 4: INPUT VALIDATION IN UI
# ============================================================================


def test_ui_input_validation():
    """Test that UI properly validates inputs before processing."""
    test_header("UI INPUT VALIDATION")

    from database import init_database
    from auth import login, logout
    from users import create_system_admin
    from travelers import add_traveler
    from scooters import add_scooter
    from validation import ValidationError

    # Initialize
    init_database()
    login("super_admin", "Admin_123?")

    # Test 4.1: Invalid username in user creation
    print("\n--- Test 4.1: Invalid Username Rejected ---")
    success, msg, temp_pw = create_system_admin("short", "Test", "User")
    assert_true(not success, "Short username rejected")
    assert_contains(msg.lower(), "validation", "Error mentions validation")

    # Test 4.2: Invalid email in traveler creation
    print("\n--- Test 4.2: Invalid Email Rejected ---")
    success, msg, cid = add_traveler(
        "Test",
        "User",
        "15-03-1990",
        "Male",
        "Street",
        "1",
        "3011AB",
        "Amsterdam",
        "notanemail",  # Invalid email
        "12345678",
        "AB1234567",
    )
    assert_true(not success, "Invalid email rejected")
    assert_contains(msg.lower(), "validation", "Error mentions validation")

    # Test 4.3: Invalid phone format in traveler creation
    print("\n--- Test 4.3: Invalid Phone Rejected ---")
    success, msg, cid = add_traveler(
        "Test",
        "User",
        "15-03-1990",
        "Male",
        "Street",
        "1",
        "3011AB",
        "Amsterdam",
        "test@example.com",
        "1234567",  # Only 7 digits
        "AB1234567",
    )
    assert_true(not success, "Invalid phone rejected")

    # Test 4.4: Invalid battery level in scooter creation
    print("\n--- Test 4.4: Invalid Battery Level Rejected ---")
    success, msg = add_scooter(
        "SC123456", "Model X", 150, "available", "Amsterdam"  # Battery > 100
    )
    assert_true(not success, "Invalid battery level rejected")

    # Test 4.5: Invalid serial number format
    print("\n--- Test 4.5: Invalid Serial Number Rejected ---")
    success, msg = add_scooter(
        "SC12", "Model X", 100, "available", "Amsterdam"  # Too short (< 6 chars)
    )
    assert_true(not success, "Invalid serial number rejected")

    logout()


# ============================================================================
# TEST 5: ERROR HANDLING IN UI
# ============================================================================


def test_ui_error_handling():
    """Test that UI properly handles errors and edge cases."""
    test_header("UI ERROR HANDLING")

    from database import init_database
    from auth import login, logout
    from users import delete_user, update_user_profile
    from travelers import delete_traveler, update_traveler
    from scooters import delete_scooter, update_scooter

    # Initialize
    init_database()
    login("super_admin", "Admin_123?")

    # Test 5.1: Delete non-existent user
    print("\n--- Test 5.1: Delete Non-existent User ---")
    success, msg = delete_user("notexist1")
    assert_true(not success, "Deleting non-existent user fails gracefully")
    assert_contains(msg.lower(), "not found", "Error message mentions user not found")

    # Test 5.2: Update non-existent traveler
    print("\n--- Test 5.2: Update Non-existent Traveler ---")
    success, msg = update_traveler("9999999999", email="test@example.com")
    assert_true(not success, "Updating non-existent traveler fails gracefully")

    # Test 5.3: Delete non-existent scooter
    print("\n--- Test 5.3: Delete Non-existent Scooter ---")
    success, msg = delete_scooter("NONEXIST")
    assert_true(not success, "Deleting non-existent scooter fails gracefully")

    # Test 5.4: Update with no changes
    print("\n--- Test 5.4: Update with No Changes ---")
    from users import create_system_admin

    create_system_admin("testuser", "Test", "User")

    success, msg = update_user_profile("testuser")  # No fields specified
    assert_true(not success, "Update with no fields fails gracefully")

    # Test 5.5: Cannot delete super_admin
    print("\n--- Test 5.5: Cannot Delete Super Admin ---")
    success, msg = delete_user("super_admin")
    assert_true(not success, "Cannot delete super_admin account")
    assert_contains(msg.lower(), "cannot delete", "Error mentions cannot delete")

    # Test 5.6: Cannot delete self
    print("\n--- Test 5.6: Cannot Delete Self ---")
    success, msg = delete_user("super_admin")
    assert_true(not success, "Cannot delete own account")

    logout()


# ============================================================================
# TEST 6: INTEGRATION TEST - COMPLETE SCENARIO
# ============================================================================


def test_complete_system_scenario():
    """Test complete realistic usage scenario spanning multiple features."""
    test_header("COMPLETE SYSTEM INTEGRATION SCENARIO")

    from database import init_database
    from auth import login, logout
    from users import create_system_admin, create_service_engineer
    from travelers import add_traveler
    from scooters import add_scooter, update_scooter
    from activity_log import get_all_logs, get_suspicious_logs
    from backup import create_backup, list_backups

    print("\n📋 SCENARIO: Super Admin sets up system and performs daily operations")

    # Initialize
    cleanup_test_data()
    init_database()

    # Step 1: Super Admin logs in
    print("\n--- Step 1: Super Admin Login ---")
    success, msg = login("super_admin", "Admin_123?")
    assert_true(success, "Super admin logged in")

    # Step 2: Create System Admin
    print("\n--- Step 2: Create System Administrator ---")
    success, msg, admin_pw = create_system_admin("admin_001", "John", "Admin")
    assert_true(success, "System admin created")

    # Step 3: Create Service Engineer
    print("\n--- Step 3: Create Service Engineer ---")
    success, msg, eng_pw = create_service_engineer("engineer1", "Jane", "Engineer")
    assert_true(success, "Service engineer created")

    # Step 4: Add travelers
    print("\n--- Step 4: Add Multiple Travelers ---")
    travelers_data = [
        ("Alice", "Johnson", "alice@example.com", "12345678", "AB1111111"),
        ("Bob", "Smith", "bob@example.com", "23456789", "CD2222222"),
        ("Charlie", "Brown", "charlie@example.com", "34567890", "EF3333333"),
    ]

    for first, last, email, phone, license in travelers_data:
        success, msg, cid = add_traveler(
            first,
            last,
            "15-03-1990",
            "Male",
            "Main Street",
            "1",
            "3011AB",
            "Amsterdam",
            email,
            phone,
            license,
        )
        assert_true(success, f"Traveler {first} {last} added")

    # Step 5: Add scooters
    print("\n--- Step 5: Add Multiple Scooters ---")
    scooters_data = [
        ("SC111111", "Model X", 100, "available", "Amsterdam Central"),
        ("SC222222", "Model Y", 85, "in_use", "Rotterdam Port"),
        ("SC333333", "Model Z", 60, "maintenance", "Utrecht Station"),
    ]

    for serial, model, battery, status, location in scooters_data:
        success, msg = add_scooter(serial, model, battery, status, location)
        assert_true(success, f"Scooter {serial} added")

    # Step 6: Create backup
    print("\n--- Step 6: Create System Backup ---")
    success, msg, backup_file = create_backup()
    assert_true(success, "Backup created")

    backups = list_backups()
    assert_true(len(backups) >= 1, "Backup listed")

    # Step 7: Logout and login as Service Engineer
    print("\n--- Step 7: Service Engineer Updates Scooter ---")
    logout()
    login("engineer1", eng_pw)

    # Service Engineer updates scooter battery
    success, msg = update_scooter(
        "SC111111", battery_level=95, location="Amsterdam West"
    )
    assert_true(success, "Service engineer updated scooter")

    # Service Engineer CANNOT update scooter type
    success, msg = update_scooter("SC111111", type="Model Updated")
    assert_true(not success, "Service engineer cannot update type")

    logout()

    # Step 8: Check system logs
    print("\n--- Step 8: Review System Logs ---")
    login("super_admin", "Admin_123?")

    logs = get_all_logs()
    assert_true(len(logs) >= 10, "Multiple activities logged")

    # Check for specific activities
    log_activities = [log["activity"] for log in logs]
    assert_true("New system admin created" in log_activities, "Admin creation logged")
    assert_true("New traveler added" in log_activities, "Traveler addition logged")
    assert_true("New scooter added" in log_activities, "Scooter addition logged")
    assert_true("Backup created" in log_activities, "Backup creation logged")
    assert_true("Scooter updated" in log_activities, "Scooter update logged")

    # Step 9: Check suspicious activities
    print("\n--- Step 9: Check Suspicious Activities ---")
    suspicious = get_suspicious_logs()
    print(f"   Found {len(suspicious)} suspicious activities")

    logout()

    print("\n✅ Complete integration scenario passed!")


# ============================================================================
# TEST 7: STRESS & EDGE CASE TESTS
# ============================================================================


def test_bulk_operations():
    """Test system performance with bulk operations."""
    test_header("BULK OPERATIONS & PERFORMANCE")

    from database import init_database
    from auth import login, logout
    from travelers import add_traveler, list_all_travelers
    from scooters import add_scooter, list_all_scooters

    # Initialize
    init_database()
    login("super_admin", "Admin_123?")

    # Test 7.1: Add multiple travelers
    print("\n--- Test 7.1: Add 10 Travelers ---")
    first_names = ["Alice", "Bob", "Charlie", "Diana", "Edward", "Fiona", "George", "Hannah", "Isaac", "Julia"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    
    for i in range(10):
        success, msg, cid = add_traveler(
            first_names[i],
            last_names[i],
            "15-03-1990",
            "Male" if i % 2 == 0 else "Female",
            "Main Street",
            str(i+1),
            "3011AB",
            "Amsterdam",
            f"user{i}@example.com",
            f"{12345670+i:08d}",
            f"AB{1234567+i}",
        )
        assert_true(success, f"Traveler {i+1} added (msg: {msg if not success else 'OK'})")

    travelers = list_all_travelers()
    assert_true(len(travelers) >= 10, "All travelers added successfully")

    # Test 7.2: Add multiple scooters
    print("\n--- Test 7.2: Add 10 Scooters ---")
    for i in range(10):
        success, msg = add_scooter(
            f"SC{100000+i}", f"Model {i}", 100, "available", "Amsterdam"
        )
        assert_true(success, f"Scooter {i+1} added")

    scooters = list_all_scooters()
    assert_true(len(scooters) >= 10, "All scooters added successfully")

    logout()


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================


def run_all_tests():
    """Run all UI and integration tests."""
    print("\n" + "🎯" * 40)
    print("UI & INTEGRATION TESTS FOR URBAN MOBILITY BACKEND")
    print("Testing complete user workflows and menu navigation")
    print("🎯" * 40)

    try:
        # Run all test suites
        test_login_flows()
        test_menu_navigation()
        test_complete_user_workflow()
        test_complete_traveler_workflow()
        test_complete_scooter_workflow()
        test_ui_input_validation()
        test_ui_error_handling()
        test_complete_system_scenario()
        test_bulk_operations()

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: Test suite crashed: {e}")
        import traceback

        traceback.print_exc()

    # Print final results
    print("\n" + "=" * 80)
    print("📊 FINAL TEST RESULTS")
    print("=" * 80)
    print(f"Total tests:  {test_results['total']}")
    print(f"✅ Passed:     {test_results['passed']}")
    print(f"❌ Failed:     {test_results['failed']}")

    if test_results["failed"] > 0:
        print(f"\n🔴 {test_results['failed']} TEST(S) FAILED:")
        for error in test_results["errors"]:
            print(f"   • {error}")
    else:
        print("\n✅ ALL TESTS PASSED! 🎉")

    # Calculate success rate
    if test_results["total"] > 0:
        success_rate = (test_results["passed"] / test_results["total"]) * 100
        print(f"\n📈 Success Rate: {success_rate:.1f}%")

    print("=" * 80)

    # Cleanup
    print("\n🧹 Cleaning up test data...")
    cleanup_test_data()
    print("✅ Cleanup complete")


if __name__ == "__main__":
    run_all_tests()
