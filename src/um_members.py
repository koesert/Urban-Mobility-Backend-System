"""
Urban Mobility Backend System - Main Program

Entry point for the Urban Mobility Backend System.
Provides console-based interface with role-based menus.

Features:
- Login/logout system
- Role-based access control (Super Admin, System Admin, Service Engineer)
- Complete CRUD operations for users, travelers, and scooters
- Activity logging and monitoring
- Backup and restore functionality
- Input validation and SQL injection prevention
- Password hashing (SHA-256)
- Data encryption (symmetric)

Users:
- Super Administrator (hardcoded): username='super_admin', password='Admin_123?'
- System Administrators (created by Super Admin)
- Service Engineers (created by Super/System Admin)

Security:
- All SQL queries use prepared statements (L02)
- All passwords hashed with SHA-256 (L05)
- All inputs validated (L03)
- All sensitive data encrypted (Assignment)
- All activities logged (Assignment)

How to run:
    python um_members.py
"""

# Standard library imports
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
# Import from local logging module (not standard library)
import logging as logging_module
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


# ===========================
# MAIN MENU FUNCTIONS
# ===========================


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
        # Service Engineer menu (limited)
        print("  1. Update Scooter Information")
        print("  2. Search Scooters")
        print("  3. Update My Password")
        print("  4. Logout")

    print("\n" + "-" * 70)
    return True


# ===========================
# USER MANAGEMENT MENUS
# ===========================


def manage_system_admins_menu():
    """Menu for managing System Administrators (Super Admin only)."""
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
    """Menu for managing Service Engineers (Super Admin & System Admin)."""
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


# ===========================
# TRAVELER MANAGEMENT MENUS
# ===========================


def manage_travelers_menu():
    """Menu for managing Travelers (Super Admin & System Admin)."""
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


# ===========================
# SCOOTER MANAGEMENT MENUS
# ===========================


def manage_scooters_menu():
    """Menu for managing Scooters (Super Admin & System Admin)."""
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
    """Simplified scooter menu for Service Engineers (update only)."""
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


# ===========================
# USER MANAGEMENT UI FUNCTIONS
# ===========================


def create_system_admin_ui():
    """Create new System Administrator."""
    clear_screen()
    print_header("CREATE NEW SYSTEM ADMINISTRATOR")
    print_user_info()

    print("\nUsername requirements:")
    print("  - Length: 8-10 characters")
    print("  - Start with letter or '_'")
    print("  - Can contain: a-z, 0-9, _, ', .")

    username = input("\nEnter username: ").strip()
    first_name = input("Enter first name: ").strip()
    last_name = input("Enter last name: ").strip()

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

    confirm = (
        input(f"\n⚠️  Are you sure you want to delete '{username}'? (yes/no): ")
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
    """Create new Service Engineer."""
    clear_screen()
    print_header("CREATE NEW SERVICE ENGINEER")
    print_user_info()

    print("\nUsername requirements:")
    print("  - Length: 8-10 characters")
    print("  - Start with letter or '_'")
    print("  - Can contain: a-z, 0-9, _, ', .")

    username = input("\nEnter username: ").strip()
    first_name = input("Enter first name: ").strip()
    last_name = input("Enter last name: ").strip()

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

    confirm = (
        input(f"\n⚠️  Are you sure you want to delete '{username}'? (yes/no): ")
        .strip()
        .lower()
    )

    if confirm == "yes":
        success, msg = delete_user(username)
        print(f"\n{msg}")
    else:
        print("\nDeletion cancelled.")

    wait_for_enter()


# ===========================
# TRAVELER UI FUNCTIONS
# ===========================


def add_traveler_ui():
    """Add new traveler."""
    clear_screen()
    print_header("ADD NEW TRAVELER")
    print_user_info()

    print("\nEnter traveler information:")

    # Predefined cities (Assignment requirement)
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

    first_name = input("First name: ").strip()
    last_name = input("Last name: ").strip()
    birthday = input("Birthday (DD-MM-YYYY): ").strip()

    print("\nGender: 1) Male  2) Female")
    gender_choice = input("Enter choice (1-2): ").strip()
    gender = "Male" if gender_choice == "1" else "Female"

    street_name = input("Street name: ").strip()
    house_number = input("House number: ").strip()
    zip_code = input("Zip code (1234AB): ").strip()

    print("\nAvailable cities:")
    for i, city in enumerate(cities, 1):
        print(f"  {i}. {city}")
    city_choice = input(f"Enter choice (1-{len(cities)}): ").strip()
    try:
        city = cities[int(city_choice) - 1]
    except (ValueError, IndexError):
        print("\nInvalid city choice.")
        wait_for_enter()
        return

    email = input("Email: ").strip()
    mobile_phone = input("Mobile phone (8 digits): ").strip()
    driving_license = input("Driving license (AB1234567): ").strip()

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

    confirm = (
        input(
            f"\n⚠️  Are you sure you want to delete traveler '{customer_id}'? (yes/no): "
        )
        .strip()
        .lower()
    )

    if confirm == "yes":
        success, msg = delete_traveler(customer_id)
        print(f"\n{msg}")
    else:
        print("\nDeletion cancelled.")

    wait_for_enter()


# ===========================
# SCOOTER UI FUNCTIONS
# ===========================


def add_scooter_ui():
    """Add new scooter."""
    clear_screen()
    print_header("ADD NEW SCOOTER")
    print_user_info()

    print("\nEnter scooter information:")

    serial_number = input("Serial number: ").strip()
    scooter_type = input("Scooter type/model: ").strip()

    try:
        battery_level = int(input("Battery level (0-100): ").strip())
    except ValueError:
        print("\nInvalid battery level.")
        wait_for_enter()
        return

    print("\nStatus: 1) available  2) in_use  3) maintenance")
    status_choice = input("Enter choice (1-3): ").strip()
    status_map = {"1": "available", "2": "in_use", "3": "maintenance"}
    status = status_map.get(status_choice, "available")

    location = input("Location: ").strip()

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
            print(f"Type: {s['type']}")
            print(f"Battery: {s['battery_level']}%")
            print(f"Status: {s['status']}")
            print(f"Location: {s['location']}")
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
            print(f"Type: {s['type']}")
            print(f"Battery: {s['battery_level']}%")
            print(f"Status: {s['status']}")
            print(f"Location: {s['location']}")
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

    confirm = (
        input(
            f"\n⚠️  Are you sure you want to delete scooter '{serial_number}'? (yes/no): "
        )
        .strip()
        .lower()
    )

    if confirm == "yes":
        success, msg = delete_scooter(serial_number)
        print(f"\n{msg}")
    else:
        print("\nDeletion cancelled.")

    wait_for_enter()


# ===========================
# LOGGING UI FUNCTIONS
# ===========================


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


# ===========================
# BACKUP UI FUNCTIONS
# ===========================


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
        code_to_revoke = codes[code_idx]["code"]
    except (ValueError, IndexError):
        print("\nInvalid choice.")
        wait_for_enter()
        return

    confirm = input(f"\n⚠️  Revoke code '{code_to_revoke}'? (yes/no): ").strip().lower()

    if confirm == "yes":
        success, msg = revoke_restore_code(code_to_revoke)
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


# ===========================
# PASSWORD UPDATE UI
# ===========================


def update_my_password_ui():
    """Update current user's password."""
    clear_screen()
    print_header("UPDATE MY PASSWORD")
    print_user_info()

    print("\nPassword requirements:")
    print("  - Length: 12-30 characters")
    print("  - At least 1 lowercase letter")
    print("  - At least 1 uppercase letter")
    print("  - At least 1 digit")
    print("  - At least 1 special character (~!@#$%&_-+=|\\(){}[]:;'<>,.?/)")

    current_password = input("\nEnter current password: ").strip()
    new_password = input("Enter new password: ").strip()
    confirm_password = input("Confirm new password: ").strip()

    if new_password != confirm_password:
        print("\n❌ Passwords do not match.")
        wait_for_enter()
        return

    user = get_current_user()
    success, msg = update_password(user["username"], current_password, new_password)

    print(f"\n{msg}")
    wait_for_enter()


# ===========================
# MAIN LOGIN LOOP
# ===========================


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
