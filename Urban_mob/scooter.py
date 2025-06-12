import re
from data.db_context import DatabaseContext
from datetime import datetime


def is_valid_serial_number(serial_number):
    """Check if serial number is 10-17 alphabetic characters."""
    return bool(re.fullmatch(r"[A-Za-z]{10,17}", serial_number))


def prompt_serial_number():
    """Prompt user for a valid serial number."""
    serial_number = input("Serial Number: ")
    while not is_valid_serial_number(serial_number):
        print("Serial Number must be 10 to 17 alphabetic characters (A-Z, a-z). Please try again.")
        serial_number = input("Serial Number: ")
    return serial_number


def is_valid_location(value):
    """Check if value is a float with up to 5 decimal places."""
    try:
        float_val = float(value)
        # Check for 5 decimal places
        if re.fullmatch(r"-?\d+\.\d{5}$", value):
            return True
        # Accept also if user enters e.g. 51.00000 (trailing zeros)
        if '.' in value and len(value.split('.')[-1]) == 5:
            return True
        return False
    except ValueError:
        return False


def prompt_location(field_name):
    """Prompt user for a valid latitude or longitude with 5 decimal places."""
    value = input(f"{field_name} (5 decimal places): ")
    while not is_valid_location(value):
        print(f"{field_name} must be a number with exactly 5 decimal places (e.g., 51.92250). Please try again.")
        value = input(f"{field_name} (5 decimal places): ")
    return float(value)


def is_valid_iso_date(date_str):
    """Check if date is in ISO 8601 format: YYYY-MM-DD."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def prompt_iso_date(field_name):
    """Prompt user for a valid ISO 8601 date (YYYY-MM-DD)."""
    date_str = input(f"{field_name} (YYYY-MM-DD): ")
    while date_str and not is_valid_iso_date(date_str):
        print(
            f"{field_name} must be in format YYYY-MM-DD (e.g., 2024-06-12). Please try again.")
        date_str = input(f"{field_name} (YYYY-MM-DD): ")
    return date_str


def prompt_int(field_name):
    """Prompt user for a valid integer."""
    while True:
        value = input(f"{field_name}: ")
        try:
            return int(value)
        except ValueError:
            print(f"{field_name} must be a valid integer. Please try again.")


def prompt_str(field_name):
    """Prompt user for a non-empty string."""
    while True:
        value = input(f"{field_name}: ")
        if value.strip():
            return value
        print(f"{field_name} cannot be empty. Please try again.")


def add_new_scooter():
    """Prompt user for scooter details and add to database."""
    print("\n--- Add New Scooter ---")
    brand = prompt_str("Brand")
    model = prompt_str("Model")
    serial_number = prompt_serial_number()
    top_speed = prompt_int("Top Speed (km/h)")
    battery_capacity = prompt_int("Battery Capacity (Wh)")
    state_of_charge = prompt_int("State of Charge (%)")
    target_range_min = prompt_int("Target Range Min (km)")
    target_range_max = prompt_int("Target Range Max (km)")
    latitude = prompt_location("Latitude")
    longitude = prompt_location("Longitude")
    mileage = prompt_int("Milage (km)")
    out_of_service_status = input(
        "Out of Service status (leave empty if not out of service): ")
    last_maintenance_date = prompt_iso_date("Last Maintenance Date")

    db = DatabaseContext()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO scooters (
                    brand, model, serial_number, top_speed, battery_capacity,
                    state_of_charge, target_range_min, target_range_max,
                    latitude, longitude, out_of_service_status, mileage,
                    last_maintenance_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    brand, model, serial_number, top_speed, battery_capacity,
                    state_of_charge, target_range_min, target_range_max,
                    latitude, longitude, out_of_service_status, mileage,
                    last_maintenance_date
                )
            )
            conn.commit()
            print("Scooter added successfully!")
        except Exception as e:
            print("Failed to add scooter:", e)


def manage_scooters_menu(role_manager):
    """Scooter management submenu with RBAC check."""
    can_manage = role_manager.check_permission("manage_scooters")
    can_modify = role_manager.check_permission("update_scooter_info")

    if not (can_manage or can_modify):
        print("You do not have permission to manage scooters.")
        input("Press Enter to continue...")
        return

    running = True
    while running:
        print("\n--- Manage Scooters ---")
        menu_options = []
        print("1. Modify scooter")
        menu_options.append("modify")
        if can_manage:
            print("2. Add new scooter")
            print("3. Delete scooter")
            print("4. Back to main menu")
            menu_options.extend(["add", "delete", "back"])
        else:
            print("2. Back to main menu")
            menu_options.append("back")

        choice = input("Select an option: ")

        if choice == "1":
            print("Modify scooter - Feature not yet implemented.")
            input("Press Enter to continue...")
        elif can_manage and choice == "2":
            add_new_scooter()
            input("Press Enter to continue...")
        elif can_manage and choice == "3":
            print("Delete scooter - Feature not yet implemented.")
            input("Press Enter to continue...")
        elif (can_manage and choice == "4") or (not can_manage and choice == "2"):
            running = False
        else:
            print("Invalid choice. Please try again.")
