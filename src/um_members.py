import os
import sys
from pathlib import Path

# Local imports
from auth import login, logout, get_current_user, check_permission, update_password
from users import (
    create_system_admin,
    create_service_engineer,
    delete_user,
    list_all_users,
    reset_user_password,
    update_user_profile,
)
from travelers import (
    add_traveler,
    update_traveler,
    delete_traveler,
    search_travelers,
    get_traveler_by_id,
    list_all_travelers,
)
from scooters import (
    add_scooter,
    update_scooter,
    delete_scooter,
    search_scooters,
    get_scooter_by_serial,
    list_all_scooters,
)
from logging import (
    get_all_logs,
    display_logs,
    check_suspicious_activities,
)
from backup import (
    create_backup,
    restore_backup,
    generate_restore_code,
    revoke_restore_code,
    list_backups,
    list_restore_codes,
)
from validation import ValidationError
from validation import (
    validate_email,
    validate_phone,
    validate_zipcode,
    validate_date,
    validate_city,
    validate_gender,
    validate_driving_license,
    validate_name,
    validate_house_number,
    validate_username,
    validate_password,
    validate_serial_number,
    validate_scooter_type,
    validate_battery_level,
    validate_location,
)


def clear_screen():
    """Clear console screen for better UX."""
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title):
    """
    Print formatted header.

    Args:
        title (str): Header title
    """
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_user_info():
    """Print current user information."""
    user = get_current_user()
    if user:
        print(f"\nLogged in as: {user['username']} ({user['role_name']})")


def wait_for_enter():
    """Wait for user to press Enter."""
    input("\nPress Enter to continue...")


def prompt_with_validation(prompt_text, validator_func):
    """
    Prompt user for input with immediate validation loop.

    Keeps asking until valid input is provided. Shows error message
    and repeats the same prompt on validation failure.

    Args:
        prompt_text (str): Text to show to user (e.g., "Email: ")
        validator_func (callable): Validation function from validation.py

    Returns:
        Validated value (type depends on validator function)

    Example:
        email = prompt_with_validation("Email: ", validate_email)
    """
    while True:
        user_input = input(prompt_text).strip()
        try:
            # Call validator function
            validated_value = validator_func(user_input)
            return validated_value
        except ValidationError as e:
            # Show error and repeat the same prompt
            print(f"❌ Error: {e}\n")


def prompt_integer_with_validation(prompt_text, validator_func):
    """
    Prompt user for integer input with immediate validation loop.

    Similar to prompt_with_validation but handles integer conversion
    and validation (e.g., battery level, house number).

    Args:
        prompt_text (str): Text to show to user
        validator_func (callable): Validation function that accepts int or str

    Returns:
        int: Validated integer value

    Example:
        battery = prompt_integer_with_validation("Battery level (0-100): ", validate_battery_level)
    """
    while True:
        user_input = input(prompt_text).strip()
        try:
            # Validator will handle conversion and range checking
            validated_value = validator_func(user_input)
            return validated_value
        except ValidationError as e:
            print(f"❌ Error: {e}\n")
        except ValueError:
            print(f"❌ Error: Please enter a valid number\n")


def validate_unique_username(username):
    """
    Validate username and check if it doesn't already exist.

    Args:
        username (str): Username to validate

    Returns:
        str: Validated username

    Raises:
        ValidationError: If username is invalid or already exists
    """
    # First do normal validation
    username = validate_username(username)
    
    # Then check if it exists
    all_users = list_all_users()
    for user in all_users:
        if user['username'] == username:
            raise ValidationError(f"Username '{username}' already exists")
    
    return username


def validate_unique_serial_number(serial_number):
    """
    Validate serial number and check if it doesn't already exist.

    Args:
        serial_number (str): Serial number to validate

    Returns:
        str: Validated serial number

    Raises:
        ValidationError: If serial number is invalid or already exists
    """
    # First do normal validation
    serial_number = validate_serial_number(serial_number)
    
    # Then check if it exists
    scooter = get_scooter_by_serial(serial_number)
    if scooter:
        raise ValidationError(f"Serial number '{serial_number}' already exists")
    
    return serial_number


def show_main_menu():
    """
    Display main menu based on user role.

    Different menus for Super Admin, System Admin, and Service Engineer.
    """
    user = get_current_user()

    if not user:
        return False

    clear_screen()
    print_header("URBAN MOBILITY BACKEND SYSTEM")
    print_user_info()

    # Check for suspicious activities (Assignment requirement)
    suspicious_count = check_suspicious_activities()
    if suspicious_count > 0:
        print(f"\n⚠️  WARNING: {suspicious_count} suspicious activities detected!")
        print("   Check system logs for details.")

    print("\nMAIN MENU:")

    if user["role"] == "super_admin":
        # Super Admin menu
        print("  1. Manage System Administrators")
        print("  2. Manage Service Engineers")
        print("  3. Manage Travelers")
        print("  4. Manage Scooters")
        print("  5. View System Logs")
        print("  6. Backup & Restore")
        print("  7. Update My Password")
        print("  8. Logout")

    elif user["role"] == "system_admin":
        # System Admin menu
        print("  1. Manage Service Engineers")
        print("  2. Manage Travelers")
        print("  3. Manage Scooters")
        print("  4. View System Logs")
        print("  5. Backup & Restore")
        print("  6. Update My Password")
        print("  7. Logout")

    elif user["role"] == "service_engineer":
        # Service Engineer menu
        print("  1. Update Scooter Information")
        print("  2. Search Scooters")
        print("  3. Update My Password")
        print("  4. Logout")

    print("\n" + "-" * 70)
    return True


def manage_system_admins_menu():
    """Menu for managing System Administrators."""
    while True:
        clear_screen()
        print_header("MANAGE SYSTEM ADMINISTRATORS")
        print_user_info()

        print("\n1. Create New System Administrator")
        print("2. List All System Administrators")
        print("3. Reset Admin Password")
        print("4. Update Admin Profile")
        print("5. Delete System Administrator")
        print("6. Back to Main Menu")

        choice = input("\nEnter choice (1-6): ").strip()

        if choice == "1":
            create_system_admin_ui()
        elif choice == "2":
            list_system_admins_ui()
        elif choice == "3":
            reset_admin_password_ui()
        elif choice == "4":
            update_admin_profile_ui()
        elif choice == "5":
            delete_system_admin_ui()
        elif choice == "6":
            break
        else:
            print("Invalid choice. Please enter 1-6.")
            wait_for_enter()


def manage_service_engineers_menu():
    """Menu for managing Service Engineers."""
    while True:
        clear_screen()
        print_header("MANAGE SERVICE ENGINEERS")
        print_user_info()

        print("\n1. Create New Service Engineer")
        print("2. List All Service Engineers")
        print("3. Reset Engineer Password")
        print("4. Update Engineer Profile")
        print("5. Delete Service Engineer")
        print("6. Back to Main Menu")

        choice = input("\nEnter choice (1-6): ").strip()

        if choice == "1":
            create_service_engineer_ui()
        elif choice == "2":
            list_service_engineers_ui()
        elif choice == "3":
            reset_engineer_password_ui()
        elif choice == "4":
            update_engineer_profile_ui()
        elif choice == "5":
            delete_service_engineer_ui()
        elif choice == "6":
            break
        else:
            print("Invalid choice. Please enter 1-6.")
            wait_for_enter()


def manage_travelers_menu():
    """Menu for managing Travelers."""
    while True:
        clear_screen()
        print_header("MANAGE TRAVELERS")
        print_user_info()

        print("\n1. Add New Traveler")
        print("2. Search Travelers")
        print("3. List All Travelers")
        print("4. Update Traveler Information")
        print("5. Delete Traveler")
        print("6. Back to Main Menu")

        choice = input("\nEnter choice (1-6): ").strip()

        if choice == "1":
            add_traveler_ui()
        elif choice == "2":
            search_travelers_ui()
        elif choice == "3":
            list_travelers_ui()
        elif choice == "4":
            update_traveler_ui()
        elif choice == "5":
            delete_traveler_ui()
        elif choice == "6":
            break
        else:
            print("Invalid choice. Please enter 1-6.")
            wait_for_enter()


def manage_scooters_menu():
    """Menu for managing Scooters."""
    while True:
        clear_screen()
        print_header("MANAGE SCOOTERS")
        print_user_info()

        print("\n1. Add New Scooter")
        print("2. Search Scooters")
        print("3. List All Scooters")
        print("4. Update Scooter Information")
        print("5. Delete Scooter")
        print("6. Back to Main Menu")

        choice = input("\nEnter choice (1-6): ").strip()

        if choice == "1":
            add_scooter_ui()
        elif choice == "2":
            search_scooters_ui()
        elif choice == "3":
            list_scooters_ui()
        elif choice == "4":
            update_scooter_ui()
        elif choice == "5":
            delete_scooter_ui()
        elif choice == "6":
            break
        else:
            print("Invalid choice. Please enter 1-6.")
            wait_for_enter()


def service_engineer_scooter_menu():
    """Simplified scooter menu for Service Engineers."""
    while True:
        clear_screen()
        print_header("UPDATE SCOOTER INFORMATION")
        print_user_info()

        print("\n1. Update Scooter")
        print("2. Back to Main Menu")

        choice = input("\nEnter choice (1-2): ").strip()

        if choice == "1":
            update_scooter_engineer_ui()
        elif choice == "2":
            break
        else:
            print("Invalid choice. Please enter 1-2.")
            wait_for_enter()


def create_system_admin_ui():
    """Create new System Administrator with per-field validation."""
    clear_screen()
    print_header("CREATE NEW SYSTEM ADMINISTRATOR")
    print_user_info()

    print("\nEnter System Administrator information:")
    print("\nUsername requirements:")
    print("  - Length: 8-10 characters")
    print("  - Start with letter or '_'")
    print("  - Can contain: a-z, 0-9, _, ', .")

    # Username - validated with immediate feedback including uniqueness check
    username = prompt_with_validation("\nEnter username: ", validate_unique_username)

    # First name - validated
    first_name = prompt_with_validation(
        "Enter first name: ", lambda x: validate_name(x, "First name")
    )

    # Last name - validated
    last_name = prompt_with_validation(
        "Enter last name: ", lambda x: validate_name(x, "Last name")
    )

    success, msg, temp_password = create_system_admin(username, first_name, last_name)

    print(f"\n{msg}")
    if success:
        print(f"Temporary password: {temp_password}")
        print("\n⚠️  IMPORTANT: Save this password! User must change it on first login.")

    wait_for_enter()


def list_system_admins_ui():
    """List all System Administrators."""
    clear_screen()
    print_header("SYSTEM ADMINISTRATORS")
    print_user_info()

    users = [u for u in list_all_users() if u["role"] == "system_admin"]

    if not users:
        print("\nNo System Administrators found.")
    else:
        print(f"\nTotal: {len(users)} System Administrator(s)")
        print("\n" + "-" * 70)
        for user in users:
            print(
                f"Username: {user['username']:15s} | Name: {user['first_name']} {user['last_name']}"
            )
            print(f"Created: {user['created_at']}")
            print("-" * 70)

    wait_for_enter()


def reset_admin_password_ui():
    """Reset System Administrator password."""
    clear_screen()
    print_header("RESET ADMIN PASSWORD")
    print_user_info()

    username = input("\nEnter admin username to reset: ").strip()

    success, msg, temp_password = reset_user_password(username)

    print(f"\n{msg}")
    if success:
        print(f"New temporary password: {temp_password}")

    wait_for_enter()


def update_admin_profile_ui():
    """Update System Administrator profile."""
    clear_screen()
    print_header("UPDATE ADMIN PROFILE")
    print_user_info()

    username = input("\nEnter admin username to update: ").strip()
    print("\nLeave blank to keep current value.")
    first_name = input("New first name: ").strip()
    last_name = input("New last name: ").strip()

    updates = {}
    if first_name:
        updates["first_name"] = first_name
    if last_name:
        updates["last_name"] = last_name

    if not updates:
        print("\nNo changes made.")
    else:
        success, msg = update_user_profile(username, **updates)
        print(f"\n{msg}")

    wait_for_enter()


def delete_system_admin_ui():
    """Delete System Administrator."""
    clear_screen()
    print_header("DELETE SYSTEM ADMINISTRATOR")
    print_user_info()

    username = input("\nEnter admin username to delete: ").strip()

    if not username:
        print("\n❌ Username cannot be empty.")
        wait_for_enter()
        return

    # Check if user exists by trying to find them in the list
    all_users = list_all_users()
    user_to_delete = None
    for user in all_users:
        if user["username"] == username and user["role"] == "system_admin":
            user_to_delete = user
            break

    if not user_to_delete:
        print(f"\n❌ System Administrator '{username}' not found.")
        wait_for_enter()
        return

    # Show user information
    print(f"\n✓ System Administrator found:")
    print(f"  Username: {user_to_delete['username']}")
    print(f"  Name: {user_to_delete['first_name']} {user_to_delete['last_name']}")
    print(f"  Created: {user_to_delete['created_at']}")

    # Now ask for confirmation
    confirm = (
        input(f"\n⚠️  Are you sure you want to delete this user? (yes/no): ")
        .strip()
        .lower()
    )

    if confirm == "yes":
        success, msg = delete_user(username)
        print(f"\n{msg}")
    else:
        print("\nDeletion cancelled.")

    wait_for_enter()


def create_service_engineer_ui():
    """Create new Service Engineer with per-field validation."""
    clear_screen()
    print_header("CREATE NEW SERVICE ENGINEER")
    print_user_info()

    print("\nEnter Service Engineer information:")
    print("\nUsername requirements:")
    print("  - Length: 8-10 characters")
    print("  - Start with letter or '_'")
    print("  - Can contain: a-z, 0-9, _, ', .")

    # Username - validated with immediate feedback including uniqueness check
    username = prompt_with_validation("\nEnter username: ", validate_unique_username)

    # First name - validated
    first_name = prompt_with_validation(
        "Enter first name: ", lambda x: validate_name(x, "First name")
    )

    # Last name - validated
    last_name = prompt_with_validation(
        "Enter last name: ", lambda x: validate_name(x, "Last name")
    )

    success, msg, temp_password = create_service_engineer(
        username, first_name, last_name
    )

    print(f"\n{msg}")
    if success:
        print(f"Temporary password: {temp_password}")
        print("\n⚠️  IMPORTANT: Save this password! User must change it on first login.")

    wait_for_enter()


def list_service_engineers_ui():
    """List all Service Engineers."""
    clear_screen()
    print_header("SERVICE ENGINEERS")
    print_user_info()

    users = [u for u in list_all_users() if u["role"] == "service_engineer"]

    if not users:
        print("\nNo Service Engineers found.")
    else:
        print(f"\nTotal: {len(users)} Service Engineer(s)")
        print("\n" + "-" * 70)
        for user in users:
            print(
                f"Username: {user['username']:15s} | Name: {user['first_name']} {user['last_name']}"
            )
            print(f"Created: {user['created_at']}")
            print("-" * 70)

    wait_for_enter()


def reset_engineer_password_ui():
    """Reset Service Engineer password."""
    clear_screen()
    print_header("RESET ENGINEER PASSWORD")
    print_user_info()

    username = input("\nEnter engineer username to reset: ").strip()

    success, msg, temp_password = reset_user_password(username)

    print(f"\n{msg}")
    if success:
        print(f"New temporary password: {temp_password}")

    wait_for_enter()


def update_engineer_profile_ui():
    """Update Service Engineer profile."""
    clear_screen()
    print_header("UPDATE ENGINEER PROFILE")
    print_user_info()

    username = input("\nEnter engineer username to update: ").strip()
    print("\nLeave blank to keep current value.")
    first_name = input("New first name: ").strip()
    last_name = input("New last name: ").strip()

    updates = {}
    if first_name:
        updates["first_name"] = first_name
    if last_name:
        updates["last_name"] = last_name

    if not updates:
        print("\nNo changes made.")
    else:
        success, msg = update_user_profile(username, **updates)
        print(f"\n{msg}")

    wait_for_enter()


def delete_service_engineer_ui():
    """Delete Service Engineer."""
    clear_screen()
    print_header("DELETE SERVICE ENGINEER")
    print_user_info()

    username = input("\nEnter engineer username to delete: ").strip()

    if not username:
        print("\n❌ Username cannot be empty.")
        wait_for_enter()
        return

    # Check if user exists by trying to find them in the list
    all_users = list_all_users()
    user_to_delete = None
    for user in all_users:
        if user["username"] == username and user["role"] == "service_engineer":
            user_to_delete = user
            break

    if not user_to_delete:
        print(f"\n❌ Service Engineer '{username}' not found.")
        wait_for_enter()
        return

    # Show user information
    print(f"\n✓ Service Engineer found:")
    print(f"  Username: {user_to_delete['username']}")
    print(f"  Name: {user_to_delete['first_name']} {user_to_delete['last_name']}")
    print(f"  Created: {user_to_delete['created_at']}")

    # Now ask for confirmation
    confirm = (
        input(f"\n⚠️  Are you sure you want to delete this user? (yes/no): ")
        .strip()
        .lower()
    )

    if confirm == "yes":
        success, msg = delete_user(username)
        print(f"\n{msg}")
    else:
        print("\nDeletion cancelled.")

    wait_for_enter()


def add_traveler_ui():
    """Add new traveler with per-field validation."""
    clear_screen()
    print_header("ADD NEW TRAVELER")
    print_user_info()

    print("\nEnter traveler information:")

    # Predefined cities
    cities = [
        "Amsterdam",
        "Rotterdam",
        "Utrecht",
        "Den Haag",
        "Eindhoven",
        "Groningen",
        "Tilburg",
        "Almere",
        "Breda",
        "Nijmegen",
    ]

    # First name - validated
    first_name = prompt_with_validation(
        "First name: ", lambda x: validate_name(x, "First name")
    )

    # Last name - validated
    last_name = prompt_with_validation(
        "Last name: ", lambda x: validate_name(x, "Last name")
    )

    # Birthday - validated
    birthday = prompt_with_validation(
        "Birthday (DD-MM-YYYY): ", lambda x: validate_date(x, "Birthday")
    )

    # Gender - validated with menu choice
    print("\nGender options:")
    print("  1) Male")
    print("  2) Female")
    while True:
        gender_choice = input("Enter choice (1-2): ").strip()
        if gender_choice in ["1", "2"]:
            gender = "Male" if gender_choice == "1" else "Female"
            break
        else:
            print("❌ Error: Please enter 1 or 2\n")

    # Street name - validated
    street_name = prompt_with_validation(
        "Street name: ", lambda x: validate_name(x, "Street name")
    )

    # House number - validated
    house_number = prompt_with_validation("House number: ", validate_house_number)

    # Zip code - validated
    zip_code = prompt_with_validation("Zip code (1234AB format): ", validate_zipcode)

    # City - validated with menu choice
    print("\nAvailable cities:")
    for i, city in enumerate(cities, 1):
        print(f"  {i}. {city}")
    while True:
        city_choice = input(f"Enter choice (1-{len(cities)}): ").strip()
        try:
            city_idx = int(city_choice) - 1
            if 0 <= city_idx < len(cities):
                city = cities[city_idx]
                break
            else:
                print(f"❌ Error: Please enter a number between 1 and {len(cities)}\n")
        except ValueError:
            print("❌ Error: Please enter a valid number\n")

    # Email - validated
    email = prompt_with_validation("Email: ", validate_email)

    # Mobile phone - validated
    mobile_phone = prompt_with_validation("Mobile phone (8 digits): ", validate_phone)

    # Driving license - validated
    driving_license = prompt_with_validation(
        "Driving license (AB1234567 format): ", validate_driving_license
    )

    success, msg, customer_id = add_traveler(
        first_name,
        last_name,
        birthday,
        gender,
        street_name,
        house_number,
        zip_code,
        city,
        email,
        mobile_phone,
        driving_license,
    )

    print(f"\n{msg}")
    if success:
        print(f"Customer ID: {customer_id}")

    wait_for_enter()


def search_travelers_ui():
    """Search travelers with partial key."""
    clear_screen()
    print_header("SEARCH TRAVELERS")
    print_user_info()

    print("\nSearch by partial key (name, customer ID):")
    search_key = input("Enter search term: ").strip()

    if not search_key:
        print("\nSearch term cannot be empty.")
        wait_for_enter()
        return

    results = search_travelers(search_key)

    if not results:
        print(f"\nNo travelers found matching '{search_key}'.")
    else:
        print(f"\nFound {len(results)} traveler(s):")
        print("\n" + "-" * 70)
        for t in results:
            print(f"Customer ID: {t['customer_id']}")
            print(f"Name: {t['first_name']} {t['last_name']}")
            print(f"Email: {t['email']}")
            print(f"City: {t['city']}")
            print("-" * 70)

    wait_for_enter()


def list_travelers_ui():
    """List all travelers."""
    clear_screen()
    print_header("ALL TRAVELERS")
    print_user_info()

    travelers = list_all_travelers()

    if not travelers:
        print("\nNo travelers found.")
    else:
        print(f"\nTotal: {len(travelers)} traveler(s)")
        print("\n" + "-" * 70)
        for t in travelers:
            print(f"Customer ID: {t['customer_id']}")
            print(f"Name: {t['first_name']} {t['last_name']}")
            print(f"Email: {t['email']}")
            print(f"Phone: {t['mobile_phone']}")
            print(f"City: {t['city']}")
            print("-" * 70)

    wait_for_enter()


def update_traveler_ui():
    """Update traveler information."""
    clear_screen()
    print_header("UPDATE TRAVELER")
    print_user_info()

    customer_id = input("\nEnter customer ID: ").strip()

    # Check if traveler exists
    traveler = get_traveler_by_id(customer_id)
    if not traveler:
        print(f"\nTraveler with ID '{customer_id}' not found.")
        wait_for_enter()
        return

    print(
        f"\nCurrent information for: {traveler['first_name']} {traveler['last_name']}"
    )
    print("Leave blank to keep current value.")

    email = input(f"New email [{traveler['email']}]: ").strip()
    mobile_phone = input(f"New phone (8 digits) [{traveler['mobile_phone']}]: ").strip()

    updates = {}
    if email:
        updates["email"] = email
    if mobile_phone:
        updates["mobile_phone"] = mobile_phone

    if not updates:
        print("\nNo changes made.")
    else:
        success, msg = update_traveler(customer_id, **updates)
        print(f"\n{msg}")

    wait_for_enter()


def delete_traveler_ui():
    """Delete traveler."""
    clear_screen()
    print_header("DELETE TRAVELER")
    print_user_info()

    customer_id = input("\nEnter customer ID to delete: ").strip()

    if not customer_id:
        print("\n❌ Customer ID cannot be empty.")
        wait_for_enter()
        return

    # First check if traveler exists
    traveler = get_traveler_by_id(customer_id)

    if not traveler:
        print(f"\n❌ Traveler with customer ID '{customer_id}' not found.")
        wait_for_enter()
        return

    # Show traveler information
    print(f"\n✓ Traveler found:")
    print(f"  Customer ID: {traveler['customer_id']}")
    print(f"  Name: {traveler['first_name']} {traveler['last_name']}")
    print(f"  Birthday: {traveler['birthday']}")
    print(f"  Gender: {traveler['gender']}")
    print(
        f"  Address: {traveler['street_name']} {traveler['house_number']}, {traveler['zip_code']} {traveler['city']}"
    )
    print(f"  Email: {traveler['email']}")
    print(f"  Phone: {traveler['mobile_phone']}")
    print(f"  License: {traveler['driving_license']}")

    # Now ask for confirmation
    confirm = (
        input(f"\n⚠️  Are you sure you want to delete this traveler? (yes/no): ")
        .strip()
        .lower()
    )

    if confirm == "yes":
        success, msg = delete_traveler(customer_id)
        print(f"\n{msg}")
    else:
        print("\nDeletion cancelled.")

    wait_for_enter()


def add_scooter_ui():
    """
    Add new scooter with per-field validation.

    Each field is validated immediately with feedback loop.
    User can retry invalid input before moving to next field.
    """
    clear_screen()
    print_header("ADD NEW SCOOTER")
    print_user_info()

    print("\nEnter scooter information:")

    # Serial number - validated with uniqueness check
    serial_number = prompt_with_validation(
        "Serial number (6-15 characters): ", validate_unique_serial_number
    )

    # Scooter type/model - validated
    scooter_type = prompt_with_validation(
        "Scooter type/model (2-30 characters): ", validate_scooter_type
    )

    # Battery level - validated as integer with range
    battery_level = prompt_integer_with_validation(
        "Battery level (0-100): ", validate_battery_level
    )

    # Status - validated with menu choice
    print("\nStatus options:")
    print("  1) available")
    print("  2) in_use")
    print("  3) maintenance")

    while True:
        status_choice = input("Enter choice (1-3): ").strip()
        if status_choice in ["1", "2", "3"]:
            status_map = {"1": "available", "2": "in_use", "3": "maintenance"}
            status = status_map[status_choice]
            break
        else:
            print("❌ Error: Please enter 1, 2, or 3\n")

    # Location - validated
    location = prompt_with_validation("Location (2-50 characters): ", validate_location)

    # All fields validated - now add to database
    success, msg = add_scooter(
        serial_number, scooter_type, battery_level, status, location
    )

    print(f"\n{msg}")
    wait_for_enter()


def search_scooters_ui():
    """Search scooters."""
    clear_screen()
    print_header("SEARCH SCOOTERS")
    print_user_info()

    print("\nSearch by: type, location, or status")
    search_key = input("Enter search term: ").strip()

    if not search_key:
        print("\nSearch term cannot be empty.")
        wait_for_enter()
        return

    results = search_scooters(search_key)

    if not results:
        print(f"\nNo scooters found matching '{search_key}'.")
    else:
        print(f"\nFound {len(results)} scooter(s):")
        print("\n" + "-" * 70)
        for s in results:
            print(f"Serial Number: {s['serial_number']}")
            print(f"Type: {s['type']}")
            print(f"Battery: {s['battery_level']}%")
            print(f"Status: {s['status']}")
            print(f"Location: {s['location']}")
            print(f"Last Service: {s['last_service_date'] or 'Never'}")
            print(f"Added: {s['added_date']}")
            print("-" * 70)

    wait_for_enter()


def list_scooters_ui():
    """List all scooters."""
    clear_screen()
    print_header("ALL SCOOTERS")
    print_user_info()

    scooters = list_all_scooters()

    if not scooters:
        print("\nNo scooters found.")
    else:
        print(f"\nTotal: {len(scooters)} scooter(s)")
        print("\n" + "-" * 70)
        for s in scooters:
            print(f"Serial Number: {s['serial_number']}")
            print(f"Type: {s['type']}")
            print(f"Battery: {s['battery_level']}%")
            print(f"Status: {s['status']}")
            print(f"Location: {s['location']}")
            print(f"Last Service: {s['last_service_date'] or 'Never'}")
            print(f"Added: {s['added_date']}")
            print("-" * 70)

    wait_for_enter()


def update_scooter_ui():
    """Update scooter (Super/System Admin - all fields)."""
    clear_screen()
    print_header("UPDATE SCOOTER")
    print_user_info()

    serial_number = input("\nEnter scooter serial number: ").strip()

    # Get current scooter
    scooter = get_scooter_by_serial(serial_number)
    if not scooter:
        print(f"\nScooter '{serial_number}' not found.")
        wait_for_enter()
        return

    print(f"\nCurrent information:")
    print(f"Type: {scooter['type']}")
    print(f"Battery: {scooter['battery_level']}%")
    print(f"Status: {scooter['status']}")
    print(f"Location: {scooter['location']}")

    print("\nLeave blank to keep current value.")

    scooter_type = input("New type: ").strip()
    battery_input = input("New battery level (0-100): ").strip()
    location = input("New location: ").strip()

    print("\nStatus: 1) available  2) in_use  3) maintenance  (blank to keep)")
    status_choice = input("Enter choice: ").strip()
    status_map = {"1": "available", "2": "in_use", "3": "maintenance"}
    status = status_map.get(status_choice, None)

    updates = {}
    if scooter_type:
        updates["type"] = scooter_type
    if battery_input:
        try:
            updates["battery_level"] = int(battery_input)
        except ValueError:
            print("\nInvalid battery level.")
            wait_for_enter()
            return
    if location:
        updates["location"] = location
    if status:
        updates["status"] = status

    if not updates:
        print("\nNo changes made.")
    else:
        success, msg = update_scooter(serial_number, **updates)
        print(f"\n{msg}")

    wait_for_enter()


def update_scooter_engineer_ui():
    """Update scooter (Service Engineer - limited fields)."""
    clear_screen()
    print_header("UPDATE SCOOTER (SERVICE ENGINEER)")
    print_user_info()

    print("\nNote: You can only update battery level, status, and location.")

    serial_number = input("\nEnter scooter serial number: ").strip()

    # Get current scooter
    scooter = get_scooter_by_serial(serial_number)
    if not scooter:
        print(f"\nScooter '{serial_number}' not found.")
        wait_for_enter()
        return

    print(f"\nCurrent information:")
    print(f"Battery: {scooter['battery_level']}%")
    print(f"Status: {scooter['status']}")
    print(f"Location: {scooter['location']}")

    print("\nLeave blank to keep current value.")

    battery_input = input("New battery level (0-100): ").strip()
    location = input("New location: ").strip()

    print("\nStatus: 1) available  2) in_use  3) maintenance  (blank to keep)")
    status_choice = input("Enter choice: ").strip()
    status_map = {"1": "available", "2": "in_use", "3": "maintenance"}
    status = status_map.get(status_choice, None)

    updates = {}
    if battery_input:
        try:
            updates["battery_level"] = int(battery_input)
        except ValueError:
            print("\nInvalid battery level.")
            wait_for_enter()
            return
    if location:
        updates["location"] = location
    if status:
        updates["status"] = status

    if not updates:
        print("\nNo changes made.")
    else:
        success, msg = update_scooter(serial_number, **updates)
        print(f"\n{msg}")

    wait_for_enter()


def delete_scooter_ui():
    """Delete scooter."""
    clear_screen()
    print_header("DELETE SCOOTER")
    print_user_info()

    serial_number = input("\nEnter scooter serial number to delete: ").strip()

    if not serial_number:
        print("\n❌ Serial number cannot be empty.")
        wait_for_enter()
        return

    # First check if scooter exists
    scooter = get_scooter_by_serial(serial_number)

    if not scooter:
        print(f"\n❌ Scooter with serial number '{serial_number}' not found.")
        wait_for_enter()
        return

    # Show scooter information
    print(f"\n✓ Scooter found:")
    print(f"  Serial Number: {scooter['serial_number']}")
    print(f"  Type: {scooter['type']}")
    print(f"  Battery: {scooter['battery_level']}%")
    print(f"  Status: {scooter['status']}")
    print(f"  Location: {scooter['location']}")
    print(f"  Last Service: {scooter['last_service_date'] or 'Never'}")
    print(f"  Added: {scooter['added_date']}")

    # Now ask for confirmation
    confirm = (
        input(f"\n⚠️  Are you sure you want to delete this scooter? (yes/no): ")
        .strip()
        .lower()
    )

    if confirm == "yes":
        success, msg = delete_scooter(serial_number)
        print(f"\n{msg}")
    else:
        print("\nDeletion cancelled.")

    wait_for_enter()


def view_logs_menu():
    """View system logs menu."""
    while True:
        clear_screen()
        print_header("SYSTEM LOGS")
        print_user_info()

        print("\n1. View All Logs")
        print("2. View Recent Logs (last 20)")
        print("3. View Suspicious Activities Only")
        print("4. Back to Main Menu")

        choice = input("\nEnter choice (1-4): ").strip()

        if choice == "1":
            view_all_logs_ui()
        elif choice == "2":
            view_recent_logs_ui()
        elif choice == "3":
            view_suspicious_logs_ui()
        elif choice == "4":
            break
        else:
            print("Invalid choice. Please enter 1-4.")
            wait_for_enter()


def view_all_logs_ui():
    """View all system logs."""
    clear_screen()
    print_header("ALL SYSTEM LOGS")
    print_user_info()

    logs = get_all_logs()

    if not logs:
        print("\nNo logs found.")
    else:
        display_logs(logs)

    wait_for_enter()


def view_recent_logs_ui():
    """View recent logs."""
    clear_screen()
    print_header("RECENT LOGS (Last 20)")
    print_user_info()

    logs = get_all_logs()

    if not logs:
        print("\nNo logs found.")
    else:
        recent = logs[-20:]
        display_logs(recent)

    wait_for_enter()


def view_suspicious_logs_ui():
    """View suspicious activities only."""
    clear_screen()
    print_header("SUSPICIOUS ACTIVITIES")
    print_user_info()

    logs = get_all_logs()
    suspicious = [log for log in logs if log.get("suspicious") == "Yes"]

    if not suspicious:
        print("\nNo suspicious activities found.")
    else:
        print(f"\n⚠️  Found {len(suspicious)} suspicious activities:")
        display_logs(suspicious)

    wait_for_enter()


def backup_restore_menu():
    """Backup and restore menu."""
    user = get_current_user()

    while True:
        clear_screen()
        print_header("BACKUP & RESTORE")
        print_user_info()

        print("\n1. Create Backup")
        print("2. List Backups")
        print("3. Restore Backup")

        if user["role"] == "super_admin":
            print("4. Generate Restore Code")
            print("5. Revoke Restore Code")
            print("6. List Restore Codes")
            print("7. Back to Main Menu")
        else:
            print("4. Back to Main Menu")

        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            create_backup_ui()
        elif choice == "2":
            list_backups_ui()
        elif choice == "3":
            restore_backup_ui()
        elif choice == "4":
            if user["role"] == "super_admin":
                generate_restore_code_ui()
            else:
                break
        elif choice == "5" and user["role"] == "super_admin":
            revoke_restore_code_ui()
        elif choice == "6" and user["role"] == "super_admin":
            list_restore_codes_ui()
        elif choice == "7" and user["role"] == "super_admin":
            break
        else:
            print("Invalid choice.")
            wait_for_enter()


def create_backup_ui():
    """Create backup."""
    clear_screen()
    print_header("CREATE BACKUP")
    print_user_info()

    print("\nCreating backup...")
    success, msg, filename = create_backup()

    print(f"\n{msg}")
    if success:
        print(f"Backup file: {filename}")

    wait_for_enter()


def list_backups_ui():
    """List available backups."""
    clear_screen()
    print_header("AVAILABLE BACKUPS")
    print_user_info()

    backups = list_backups()

    if not backups:
        print("\nNo backups found.")
    else:
        print(f"\nTotal: {len(backups)} backup(s)")
        print("\n" + "-" * 70)
        for b in backups:
            print(f"Filename: {b['filename']}")
            print(f"Size: {b['size']} bytes")
            print(f"Created: {b['created']}")
            print("-" * 70)

    wait_for_enter()


def restore_backup_ui():
    """Restore from backup."""
    user = get_current_user()

    clear_screen()
    print_header("RESTORE BACKUP")
    print_user_info()

    backups = list_backups()

    if not backups:
        print("\nNo backups found.")
        wait_for_enter()
        return

    print("\nAvailable backups:")
    for i, b in enumerate(backups, 1):
        print(f"{i}. {b['filename']} ({b['created']})")

    choice = input(f"\nEnter backup number (1-{len(backups)}): ").strip()

    try:
        backup_idx = int(choice) - 1
        backup_filename = backups[backup_idx]["filename"]
    except (ValueError, IndexError):
        print("\nInvalid choice.")
        wait_for_enter()
        return

    # System Admin needs restore code
    restore_code = None
    if user["role"] == "system_admin":
        restore_code = input("\nEnter restore code: ").strip()

    confirm = (
        input(
            f"\n⚠️  Restore from '{backup_filename}'? This will overwrite current data. (yes/no): "
        )
        .strip()
        .lower()
    )

    if confirm == "yes":
        success, msg = restore_backup(backup_filename, restore_code)
        print(f"\n{msg}")
    else:
        print("\nRestore cancelled.")

    wait_for_enter()


def generate_restore_code_ui():
    """Generate restore code (Super Admin only)."""
    clear_screen()
    print_header("GENERATE RESTORE CODE")
    print_user_info()

    backups = list_backups()

    if not backups:
        print("\nNo backups found.")
        wait_for_enter()
        return

    print("\nAvailable backups:")
    for i, b in enumerate(backups, 1):
        print(f"{i}. {b['filename']}")

    choice = input(f"\nEnter backup number (1-{len(backups)}): ").strip()

    try:
        backup_idx = int(choice) - 1
        backup_filename = backups[backup_idx]["filename"]
    except (ValueError, IndexError):
        print("\nInvalid choice.")
        wait_for_enter()
        return

    target_username = input("Enter System Admin username: ").strip()

    success, msg, code = generate_restore_code(backup_filename, target_username)

    print(f"\n{msg}")
    if success:
        print(f"\n✓ Restore code: {code}")
        print(f"  Valid for: {target_username}")
        print(f"  Backup: {backup_filename}")

    wait_for_enter()


def revoke_restore_code_ui():
    """Revoke restore code (Super Admin only)."""
    clear_screen()
    print_header("REVOKE RESTORE CODE")
    print_user_info()

    codes = list_restore_codes()

    if not codes:
        print("\nNo active restore codes found.")
        wait_for_enter()
        return

    print("\nActive restore codes:")
    for i, c in enumerate(codes, 1):
        print(
            f"{i}. {c['code']} - User: {c['target_username']} - Backup: {c['backup_filename']}"
        )

    choice = input(f"\nEnter code number to revoke (1-{len(codes)}): ").strip()

    try:
        code_idx = int(choice) - 1
        selected_code = codes[code_idx]
    except (ValueError, IndexError):
        print("\n❌ Invalid choice.")
        wait_for_enter()
        return

    # Show selected restore code information
    print(f"\n✓ Restore code selected:")
    print(f"  Code: {selected_code['code']}")
    print(f"  Target User: {selected_code['target_username']}")
    print(f"  Backup File: {selected_code['backup_filename']}")
    print(f"  Created: {selected_code['created_at']}")

    # Now ask for confirmation
    confirm = (
        input(f"\n⚠️  Are you sure you want to revoke this restore code? (yes/no): ")
        .strip()
        .lower()
    )

    if confirm == "yes":
        success, msg = revoke_restore_code(selected_code["code"])
        print(f"\n{msg}")
    else:
        print("\nRevocation cancelled.")

    wait_for_enter()


def list_restore_codes_ui():
    """List active restore codes (Super Admin only)."""
    clear_screen()
    print_header("ACTIVE RESTORE CODES")
    print_user_info()

    codes = list_restore_codes()

    if not codes:
        print("\nNo active restore codes found.")
    else:
        print(f"\nTotal: {len(codes)} active code(s)")
        print("\n" + "-" * 70)
        for c in codes:
            print(f"Code: {c['code']}")
            print(f"User: {c['target_username']}")
            print(f"Backup: {c['backup_filename']}")
            print(f"Created: {c['created_at']}")
            print("-" * 70)

    wait_for_enter()


def update_my_password_ui():
    """Update current user's password with per-field validation."""
    clear_screen()
    print_header("UPDATE MY PASSWORD")
    print_user_info()

    print("\nPassword requirements:")
    print("  - Length: 12-30 characters")
    print("  - At least 1 lowercase letter")
    print("  - At least 1 uppercase letter")
    print("  - At least 1 digit")
    print("  - At least 1 special character (~!@#$%&_-+=|\\(){}[]:;'<>,.?/)")

    # Step 1: Verify current password first
    current_password = input("\nEnter current password: ").strip()

    if not current_password:
        print("\n❌ Current password cannot be empty.")
        wait_for_enter()
        return

    # Verify current password before asking for new one
    user = get_current_user()
    from database import get_connection
    from auth import verify_password

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user["user_id"],))
    result = cursor.fetchone()
    conn.close()

    if not result or not verify_password(current_password, user["username"], result[0]):
        print("\n❌ Incorrect current password.")
        wait_for_enter()
        return

    # Step 2: Get new password with immediate validation
    print("\n✓ Current password verified.")
    new_password = prompt_with_validation("Enter new password: ", validate_password)

    # Step 3: Confirm new password
    confirm_password = input("Confirm new password: ").strip()

    if not confirm_password:
        print("\n❌ Confirmation password cannot be empty.")
        wait_for_enter()
        return

    if new_password != confirm_password:
        print("\n❌ Passwords do not match.")
        wait_for_enter()
        return

    # Step 4: Update password
    success, msg = update_password(current_password, new_password)

    print(f"\n{msg}")
    wait_for_enter()


def login_screen():
    """Login screen."""
    clear_screen()
    print_header("URBAN MOBILITY BACKEND SYSTEM - LOGIN")

    print("\n" + "=" * 70)
    print("  HARDCODED SUPER ADMIN CREDENTIALS:")
    print("  Username: super_admin")
    print("  Password: Admin_123?")
    print("=" * 70)

    username = input("\nUsername: ").strip()
    password = input("Password: ").strip()

    success, message = login(username, password)

    if success:
        print(f"\n✓ {message}")
        wait_for_enter()
        return True
    else:
        print(f"\n❌ {message}")
        wait_for_enter()
        return False


def main():
    """
    Main program loop.

    Flow:
    1. Login screen
    2. Role-based main menu
    3. Handle menu choices
    4. Logout
    """
    print("\n" + "=" * 70)
    print("  URBAN MOBILITY BACKEND SYSTEM")
    print("  Software Quality - Analysis 8")
    print("=" * 70)
    print("\nInitializing system...")

    # Initialize database (creates tables and super admin)
    try:
        from database import init_database

        init_database()
        print("✓ Database initialized")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return

    print("✓ System ready")
    wait_for_enter()

    # Main loop
    while True:
        # Login
        if not login_screen():
            retry = input("\nRetry login? (yes/no): ").strip().lower()
            if retry != "yes":
                print("\nGoodbye!")
                break
            continue

        # Main menu loop (after successful login)
        while True:
            user = get_current_user()

            if not user:
                break

            if not show_main_menu():
                break

            choice = input("\nEnter choice: ").strip()

            # Route based on role
            if user["role"] == "super_admin":
                if choice == "1":
                    manage_system_admins_menu()
                elif choice == "2":
                    manage_service_engineers_menu()
                elif choice == "3":
                    manage_travelers_menu()
                elif choice == "4":
                    manage_scooters_menu()
                elif choice == "5":
                    view_logs_menu()
                elif choice == "6":
                    backup_restore_menu()
                elif choice == "7":
                    update_my_password_ui()
                elif choice == "8":
                    logout()
                    print("\n✓ Logged out successfully")
                    wait_for_enter()
                    break
                else:
                    print("\nInvalid choice. Please try again.")
                    wait_for_enter()

            elif user["role"] == "system_admin":
                if choice == "1":
                    manage_service_engineers_menu()
                elif choice == "2":
                    manage_travelers_menu()
                elif choice == "3":
                    manage_scooters_menu()
                elif choice == "4":
                    view_logs_menu()
                elif choice == "5":
                    backup_restore_menu()
                elif choice == "6":
                    update_my_password_ui()
                elif choice == "7":
                    logout()
                    print("\n✓ Logged out successfully")
                    wait_for_enter()
                    break
                else:
                    print("\nInvalid choice. Please try again.")
                    wait_for_enter()

            elif user["role"] == "service_engineer":
                if choice == "1":
                    service_engineer_scooter_menu()
                elif choice == "2":
                    search_scooters_ui()
                elif choice == "3":
                    update_my_password_ui()
                elif choice == "4":
                    logout()
                    print("\n✓ Logged out successfully")
                    wait_for_enter()
                    break
                else:
                    print("\nInvalid choice. Please try again.")
                    wait_for_enter()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram terminated by user.")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
