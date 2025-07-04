import re
from data.db_context import DatabaseContext
from data.encryption import decrypt_field
from datetime import datetime


def is_valid_serial_number(serial_number):
    """Check if serial number is 10-17 alphanumeric characters."""
    return bool(re.fullmatch(r"[A-Za-z0-9]{10,17}", serial_number))


def prompt_serial_number():
    """Prompt user for a valid serial number."""
    serial_number = input("Serial Number: ")
    while not is_valid_serial_number(serial_number):
        print(
            "Serial Number must be 10 to 17 alphanumeric characters (A-Z, a-z, 0-9). Please try again."
        )
        serial_number = input("Serial Number: ")
    return serial_number


def is_valid_location(value):
    """Check if value is a float with up to 5 decimal places."""
    try:
        # float_val = float(value)
        # Check for 5 decimal places
        if re.fullmatch(r"-?\d+\.\d{5}$", value):
            return True
        # Accept also if user enters e.g. 51.00000 (trailing zeros)
        if "." in value and len(value.split(".")[-1]) == 5:
            return True
        return False
    except ValueError:
        return False


def is_rotterdam_location(latitude, longitude):
    """Check if latitude/longitude are within the Rotterdam region."""
    return 51.8 <= latitude <= 52.0 and 4.2 <= longitude <= 4.6


def prompt_location(field_name):
    """Prompt user for a valid latitude or longitude with 5 decimal places."""
    value = input(f"{field_name} (5 decimal places): ")
    while not is_valid_location(value):
        print(
            f"{field_name} must be a number with exactly 5 decimal places (e.g., 51.92250). Please try again."
        )
        value = input(f"{field_name} (5 decimal places): ")
    return float(value)


def prompt_rotterdam_location():
    """Prompt user for latitude and longitude, both with 5 decimals, and check Rotterdam bounds."""
    while True:
        latitude = prompt_location("Latitude")
        longitude = prompt_location("Longitude")
        if is_rotterdam_location(latitude, longitude):
            return latitude, longitude
        print("Coordinates must be within the Rotterdam region (lat: 51.8-52.0, long: 4.2-4.6). Please try again.")


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
            f"{field_name} must be in format YYYY-MM-DD (e.g., 2024-06-12). Please try again."
        )
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


def add_new_scooter(role_manager):
    """Prompt user for scooter details and add to database using db_context insert_scooter."""
    # Permission check
    permissions = role_manager.get_available_permissions()
    if "add_scooter" not in permissions:
        print("You do not have permission to add scooters.")
        return

    print("\n--- Add New Scooter ---")
    brand = prompt_str("Brand")
    model = prompt_str("Model")
    serial_number = prompt_serial_number()
    top_speed = prompt_int("Top Speed (km/h)")
    battery_capacity = prompt_int("Battery Capacity (Wh)")
    state_of_charge = prompt_int("State of Charge (%)")
    target_range_min = prompt_int("Target Range Min (km)")
    target_range_max = prompt_int("Target Range Max (km)")
    latitude, longitude = prompt_rotterdam_location()
    mileage = prompt_int("Milage (km)")
    out_of_service_status = input(
        "Out of Service status (leave empty if not out of service): "
    )
    last_maintenance_date = prompt_iso_date("Last Maintenance Date")
    in_service_date = datetime.now().isoformat()

    scooter = {
        "brand": brand,
        "model": model,
        "serial_number": serial_number,
        "top_speed": top_speed,
        "battery_capacity": battery_capacity,
        "state_of_charge": state_of_charge,
        "target_range_min": target_range_min,
        "target_range_max": target_range_max,
        "latitude": latitude,
        "longitude": longitude,
        "out_of_service_status": out_of_service_status,
        "mileage": mileage,
        "last_maintenance_date": last_maintenance_date,
        "in_service_date": in_service_date,
    }

    db = DatabaseContext()
    try:
        db.insert_scooter(scooter)
        print("Scooter added successfully!")
        role_manager.auth.logger.log_activity(
            username=role_manager.auth.current_user["username"],
            activity="Add Scooter",
            details=f"Scooter with serial number: {serial_number} added.",
        )
    except Exception as e:
        print("Failed to add scooter:", e)


def delete_scooter(role_manager):
    """Show all scooters and delete one by ID."""
    # Permission check
    permissions = role_manager.get_available_permissions()
    if "delete_scooter" not in permissions:
        print("You do not have permission to delete scooters.")
        return

    db = DatabaseContext()
    try:
        scooters = db.show_all_scooters()
        if not scooters:
            print("There are no scooters to delete.")
            return

        print("\nAvailable scooters:")
        for s in scooters:
            print(
                f"ID: {s['id']} | Brand: {s['brand']} | Model: {s['model']} | Serial number: {s['serial_number']} | Status: {s['out_of_service_status']}"
            )

        scooter_id = input("Enter the ID of the scooter you want to delete: ")
        if not scooter_id.isdigit():
            print("Scooter ID must be a valid number.")
            return
        scooter_id = int(scooter_id)
        # Get scooter info before deleting
        scooter_to_delete = next(
            (s for s in scooters if s["id"] == scooter_id), None)
        if not scooter_to_delete:
            print(f"No scooter found with ID {scooter_id}.")
            return

        deleted = db.delete_scooter_by_id(scooter_id)
        if deleted:
            print(f"Scooter with ID {scooter_id} successfully deleted.")
            role_manager.auth.logger.log_activity(
                username=role_manager.auth.current_user["username"],
                activity="Delete Scooter",
                details=f"Scooter with ID: {scooter_id} & serial number: {scooter_to_delete['serial_number']} deleted.",
            )
        else:
            print(f"Failed to delete scooter with ID {scooter_id}.")
    except Exception as e:
        print("Failed to delete scooter:", e)


def modify_scooter(role_manager):
    """Show all scooters, select one by ID, and modify its details based on user permissions."""
    db = DatabaseContext()
    permissions = role_manager.get_available_permissions()
    can_update_all = "update_scooter_info" in permissions
    can_update_selected = "update_selected_scooter_info" in permissions

    if not (can_update_all or can_update_selected):
        print("You do not have permission to modify scooters.")
        return

    try:
        scooters = db.show_all_scooters()
        if not scooters:
            print("There are no scooters to modify.")
            return

        print("\nAvailable scooters:")
        for s in scooters:
            print(
                f"ID: {s['id']} | Brand: {s['brand']} | Model: {s['model']} | Serial number: {s['serial_number']} | Status: {s['out_of_service_status']}"
            )

        scooter_id = input("Enter the ID of the scooter you want to modify: ")
        if not scooter_id.isdigit():
            print("Scooter ID must be a valid number.")
            return
        scooter_id = int(scooter_id)

        # Find the selected scooter
        scooter = next((s for s in scooters if s["id"] == scooter_id), None)
        if not scooter:
            print(f"No scooter found with ID {scooter_id}.")
            return

        print("\nPress Enter to keep the current value shown in [brackets].")

        # Helper functions for input with validation
        def prompt_int_with_default(field, current):
            while True:
                val = input(f"{field} [{current}]: ")
                if val.strip() == "":
                    return current
                try:
                    return int(val)
                except ValueError:
                    print(f"{field} must be a valid integer. Please try again.")

        def prompt_float_with_default(field, current):
            while True:
                val = input(f"{field} [{current}]: ")
                if val.strip() == "":
                    return current
                try:
                    float_val = float(val)
                    # Check for 5 decimal places
                    if "." in val and len(val.split(".")[-1]) == 5:
                        return float_val
                    else:
                        print(
                            f"{field} must have exactly 5 decimal places. Please try again."
                        )
                except ValueError:
                    print(f"{field} must be a valid number. Please try again.")

        def prompt_str_with_default(field, current):
            val = input(f"{field} [{current}]: ")
            return val if val.strip() else current

        def prompt_date_with_default(field, current):
            while True:
                val = input(f"{field} [{current}]: ")
                if val.strip() == "":
                    return current
                if is_valid_iso_date(val):
                    return val
                else:
                    print(
                        f"{field} must be in format YYYY-MM-DD. Please try again.")

        # Build updated_scooter dict based on permissions
        updated_scooter = {}

        # Fields editable by all (Super Admin/System Admin)
        if can_update_all:
            updated_scooter["brand"] = prompt_str_with_default(
                "Brand", scooter["brand"]
            )
            updated_scooter["model"] = prompt_str_with_default(
                "Model", scooter["model"]
            )
            # Serial number validation
            while True:
                serial_number = input(
                    f"Serial Number [{scooter['serial_number']}]: ")
                if serial_number.strip() == "":
                    updated_scooter["serial_number"] = scooter["serial_number"]
                    break
                if is_valid_serial_number(serial_number):
                    updated_scooter["serial_number"] = serial_number
                    break
                else:
                    print(
                        "Serial Number must be 10 to 17 alphanumeric characters (A-Z, a-z, 0-9). Please try again."
                    )
            updated_scooter["top_speed"] = prompt_int_with_default(
                "Top Speed (km/h)", scooter["top_speed"]
            )
            updated_scooter["battery_capacity"] = prompt_int_with_default(
                "Battery Capacity (Wh)", scooter["battery_capacity"]
            )
        else:
            # Keep current values for fields not allowed to edit
            updated_scooter["brand"] = scooter["brand"]
            updated_scooter["model"] = scooter["model"]
            updated_scooter["serial_number"] = scooter["serial_number"]
            updated_scooter["top_speed"] = scooter["top_speed"]
            updated_scooter["battery_capacity"] = scooter["battery_capacity"]

        # Fields editable by both roles
        updated_scooter["state_of_charge"] = prompt_int_with_default(
            "State of Charge (%)", scooter["state_of_charge"]
        )
        updated_scooter["target_range_min"] = prompt_int_with_default(
            "Target Range Min (km)", scooter["target_range_min"]
        )
        updated_scooter["target_range_max"] = prompt_int_with_default(
            "Target Range Max (km)", scooter["target_range_max"]
        )
        while True:
            lat = prompt_float_with_default("Latitude", scooter["latitude"])
            lon = prompt_float_with_default("Longitude", scooter["longitude"])
            if is_rotterdam_location(lat, lon):
                updated_scooter["latitude"] = lat
                updated_scooter["longitude"] = lon
                break
            print("Coordinates must be within the Rotterdam region (lat: 51.8-52.0, long: 4.2-4.6). Please try again.")
        updated_scooter["out_of_service_status"] = prompt_str_with_default(
            "Out of Service status", scooter["out_of_service_status"]
        )
        updated_scooter["mileage"] = prompt_float_with_default(
            "Mileage (km)", scooter["mileage"]
        )
        updated_scooter["last_maintenance_date"] = prompt_date_with_default(
            "Last Maintenance Date", scooter["last_maintenance_date"]
        )

        # Keep unchanged fields
        updated_scooter["in_service_date"] = scooter["in_service_date"]

        updated = db.update_scooter_by_id(scooter_id, updated_scooter)
        if updated:
            print(f"Scooter with ID {scooter_id} successfully updated.")

            role_manager.auth.logger.log_activity(
                username=role_manager.auth.current_user["username"],
                activity="Modify Scooter",
                details=f"Scooter with ID: {scooter_id} & serial number: {updated_scooter['serial_number']} modified.",
            )
        else:
            print(f"Failed to update scooter with ID {scooter_id}.")

    except Exception as e:
        print("Failed to modify scooter:", e)


def search_scooters(role_manager):
    """Search scooters by partial key matching across multiple fields."""

    db = DatabaseContext()
    print("\n--- Search Scooters ---")
    search_key = input("Enter search term (partial match across all fields): ").strip()

    if not search_key:
        print("Search term cannot be empty.")
        return

    try:
        all_scooters = db.show_all_scooters()
        if not all_scooters:
            print("No scooters available to search.")
            return

        # Convert search key to lowercase for case-insensitive matching
        search_key_lower = search_key.lower()

        # Search across all relevant fields
        matching_scooters = []
        for scooter in all_scooters:
            # Convert all searchable fields to strings and check for partial matches
            searchable_fields = [
                str(scooter['id']),
                str(scooter['brand']),
                str(scooter['model']),
                str(scooter['serial_number']),
                str(scooter['state_of_charge']),
                str(scooter['latitude']),
                str(scooter['longitude']),
                str(scooter['out_of_service_status']),
                str(scooter['mileage']),
                str(scooter['top_speed']),
                str(scooter['battery_capacity']),
                str(scooter['target_range_min']),
                str(scooter['target_range_max']),
                str(scooter['last_maintenance_date']),
                str(scooter['in_service_date'])
            ]

            # Check if search key appears in any field (case-insensitive)
            if any(search_key_lower in field.lower() for field in searchable_fields):
                matching_scooters.append(scooter)

        # Display results
        if not matching_scooters:
            print(f"No scooters found matching '{search_key}'.")
            return

        print(f"\n--- Search Results for '{search_key}' ({len(matching_scooters)} found) ---")
        print(f"{'ID':<4} {'Brand':<12} {'Model':<12} {'Serial':<15} {'Battery':<8} {'Location':<20} {'Status':<15}")
        print("-" * 95)

        for s in matching_scooters:
            location_str = f"{s['latitude']:.3f},{s['longitude']:.3f}"
            status_str = s['out_of_service_status'] if s['out_of_service_status'] else "In Service"
            print(f"{s['id']:<4} {s['brand']:<12} {s['model']:<12} {s['serial_number']:<15} {s['state_of_charge']}%{'':<4} {location_str:<20} {status_str:<15}")

        # Log the search activity
        role_manager.auth.logger.log_activity(
            username=role_manager.auth.current_user["username"],
            activity="Search Scooters",
            details=f"Searched scooters with term '{search_key}', found {len(matching_scooters)} results."
        )

    except Exception as e:
        print(f"Error during search: {e}")


def manage_scooters_menu(role_manager):
    """Scooter management submenu with RBAC, just like the main menu."""
    # Get permissions for current user
    permissions = role_manager.get_available_permissions()
    print("\n--- Manage Scooters ---")

    menu_options = []
    option_num = 1

    # Always possible for Service Engineer, System Admin, Super Admin
    if "update_scooter_info" in permissions or "manage_scooters" in permissions:
        menu_options.append((option_num, "Search scooters"))
        option_num += 1
        menu_options.append((option_num, "Modify scooter"))
        option_num += 1

    # Only for System Admin & Super Admin
    if "manage_scooters" in permissions:
        menu_options.append((option_num, "Add new scooter"))
        option_num += 1
        menu_options.append((option_num, "Delete scooter"))
        option_num += 1

    # Always available
    menu_options.append((option_num, "Back to main menu"))

    # Show menu
    for num, option in menu_options:
        print(f"{num}. {option}")

    # Handle choice
    choice = input("Select an option: ")
    try:
        choice_num = int(choice)
        selected_option = None
        for num, option in menu_options:
            if num == choice_num:
                selected_option = option
                break

        if not selected_option:
            print("Invalid choice!")
            return

        if selected_option == "Search scooters":
            search_scooters(role_manager)
            input("Press Enter to continue...")
        elif selected_option == "Modify scooter":
            modify_scooter(role_manager)
            input("Press Enter to continue...")
        elif selected_option == "Add new scooter":
            add_new_scooter(role_manager)
            input("Press Enter to continue...")
        elif selected_option == "Delete scooter":
            delete_scooter(role_manager)
            input("Press Enter to continue...")
        elif selected_option == "Back to main menu":
            return
        else:
            print("Invalid choice. Please try again.")
    except ValueError:
        print("Please enter a valid number!")
