# Urban_mob/managers/travelers_manager.py
import re
from datetime import datetime
from data.encryption import decrypt_field, encrypt_field


class TravelersManager:
    def __init__(self, auth_service):
        self.auth = auth_service
        self.db = auth_service.db

        # Predefined cities as required by assignment
        self.PREDEFINED_CITIES = [
            "Rotterdam",
            "Amsterdam",
            "The Hague",
            "Utrecht",
            "Eindhoven",
            "Tilburg",
            "Groningen",
            "Almere",
            "Breda",
            "Nijmegen",
        ]

        # Verify encryption system is working
        self._verify_encryption_system()

    def _verify_encryption_system(self):
        """Verify that the encryption system is working properly"""
        try:
            # Test encryption/decryption
            test_value = "test@example.com"
            encrypted = encrypt_field(test_value)
            decrypted = decrypt_field(encrypted)

            if decrypted != test_value:
                raise Exception(
                    "Encryption test failed: decrypted value doesn't match original"
                )

        except Exception as e:
            print(f"❌ Encryption system error: {e}")
            print(
                "❌ Please check that the encryption key file exists and is accessible."
            )
            raise Exception(f"Encryption system initialization failed: {e}")

    def can_manage_travelers(self):
        """Check if current user can manage travelers"""
        if not self.auth.current_user:
            return False

        user_role = self.auth.current_user["role"]
        return user_role in ["super_admin", "system_admin"]

    def display_travelers_menu(self):
        """Display travelers management menu"""
        if not self.can_manage_travelers():
            print("Access denied: Insufficient permissions!")
            return None

        print("\n--- TRAVELERS MANAGEMENT ---")
        print("1. View All Travelers")
        print("2. Search Traveler")
        print("3. Add New Traveler")
        print("4. Update Traveler")
        print("5. Delete Traveler")
        print("6. Back to Main Menu")

        choice = input("Select an option: ")
        return choice

    def handle_travelers_menu(self):
        """Handle travelers management menu operations"""
        while True:
            choice = self.display_travelers_menu()

            if choice == "1":
                self.view_all_travelers()
            elif choice == "2":
                self.search_traveler()
            elif choice == "3":
                self.add_traveler()
            elif choice == "4":
                self.update_traveler()
            elif choice == "5":
                self.delete_traveler()
            elif choice == "6":
                break
            else:
                print("Invalid choice! Please try again.")

            input("\nPress Enter to continue...")

    def view_all_travelers(self):
        """Display all travelers with decrypted data"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT customer_id, first_name, last_name, email, mobile_phone, city, registration_date
                    FROM travelers
                    ORDER BY registration_date DESC
                """
                )

                travelers = cursor.fetchall()

                if not travelers:
                    print("No travelers found.")
                    return

                print(
                    f"\n{'Customer ID':<12} {'Name':<25} {'Email':<30} {'Phone':<18} {'City':<15} {'Registered':<12}"
                )
                print("-" * 115)

                for traveler in travelers:
                    customer_id, first_name, last_name, email, phone, city, reg_date = (
                        traveler
                    )

                    # Decrypt sensitive data for display
                    try:
                        decrypted_email = decrypt_field(email)
                        decrypted_phone = decrypt_field(phone)
                    except Exception:
                        # Fallback for any decryption issues
                        decrypted_email = "[ENCRYPTED]"
                        decrypted_phone = "[ENCRYPTED]"

                    full_name = f"{first_name} {last_name}"
                    reg_date_short = reg_date[:10] if reg_date else "N/A"

                    print(
                        f"{customer_id:<12} {full_name:<25} {decrypted_email:<30} {decrypted_phone:<18} {city:<15} {reg_date_short:<12}"
                    )

                print(f"\nTotal travelers: {len(travelers)}")

        except Exception as e:
            print(f"Error retrieving travelers: {e}")

    def search_traveler(self):
        """Search for a specific traveler with decrypted display"""
        search_term = input("Enter customer ID, name, or email to search: ").strip()

        if not search_term:
            print("Search term cannot be empty!")
            return

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                # Search in non-encrypted fields and encrypted email field
                cursor.execute(
                    """
                    SELECT * FROM travelers
                    WHERE customer_id LIKE ? OR
                          first_name LIKE ? OR
                          last_name LIKE ?
                """,
                    (
                        f"%{search_term}%",
                        f"%{search_term}%",
                        f"%{search_term}%",
                    ),
                )

                travelers = cursor.fetchall()

                # Also search in encrypted email field
                cursor.execute("SELECT * FROM travelers")
                all_travelers = cursor.fetchall()

                # Check encrypted email fields
                for traveler in all_travelers:
                    try:
                        decrypted_email = decrypt_field(traveler[10])  # email field
                        if search_term.lower() in decrypted_email.lower():
                            if traveler not in travelers:
                                travelers.append(traveler)
                    except Exception as e:
                        # Skip travelers with corrupted encryption or invalid tokens
                        continue

                if not travelers:
                    print("No travelers found matching your search.")
                    return

                for traveler in travelers:
                    self._display_traveler_details(traveler)
                    print("-" * 50)

        except Exception as e:
            print(f"Error searching travelers: {e}")

    def add_traveler(self):
        """Add a new traveler using encrypted storage"""
        print("\n--- ADD NEW TRAVELER ---")
        print("📝 Please enter the traveler information")
        print("   You can retry any field if you make a mistake")

        try:
            # Collect traveler information
            traveler_data = self._collect_traveler_data()
            if not traveler_data:
                return

            # Generate customer ID
            customer_id = self._generate_customer_id()
            traveler_data["customer_id"] = customer_id
            traveler_data["registration_date"] = datetime.now().isoformat()

            # Show summary for confirmation
            print("\n📋 TRAVELER INFORMATION SUMMARY:")
            print(f"   Customer ID: {customer_id}")
            print(
                f"   Name: {traveler_data['first_name']} {traveler_data['last_name']}"
            )
            print(f"   Birthday: {traveler_data['birthday']}")
            print(f"   Gender: {traveler_data['gender']}")
            print(
                f"   Address: {traveler_data['house_number']} {traveler_data['street_name']}"
            )
            print(f"   City: {traveler_data['zip_code']} {traveler_data['city']}")
            print(f"   Email: {traveler_data['email']}")
            print(f"   Mobile: {traveler_data['mobile_phone']}")
            print(f"   Driving License: {traveler_data['driving_license']}")

            confirm = self._get_yes_no_input("\n✅ Save this traveler?")
            if not confirm:
                print("Traveler not saved.")
                return

            # Use the existing insert_traveler method that handles encryption
            self.db.insert_traveler(traveler_data)

            print(f"\n🎉 Traveler added successfully!")
            print(f"📋 Customer ID: {customer_id}")
            print(
                f"👤 Name: {traveler_data['first_name']} {traveler_data['last_name']}"
            )

        except Exception as e:
            print(f"Error adding traveler: {e}")
        except KeyboardInterrupt:
            print("\nOperation cancelled.")

    def update_traveler(self):
        """Update an existing traveler with encrypted data handling"""
        customer_id = input("Enter Customer ID to update: ").strip()

        if not customer_id:
            print("Customer ID cannot be empty!")
            return

        # First, check if traveler exists
        traveler = self._get_traveler_by_id(customer_id)
        if not traveler:
            print("Traveler not found!")
            return

        print("\nCurrent traveler information:")
        self._display_traveler_details(traveler)

        print("\n📝 UPDATE TRAVELER INFORMATION")
        print("Enter new information (press Enter to keep current value)")
        print("Type 'skip' to skip a field, or 'cancel' to cancel the update")

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Collect updates
                updates = {}

                # Get current decrypted values for display
                try:
                    current_email = decrypt_field(traveler[10])
                    current_phone = decrypt_field(traveler[11])
                    current_license = decrypt_field(traveler[12])
                except Exception as e:
                    # Handle encryption errors gracefully
                    print(f"Warning: Could not decrypt current traveler data: {e}")
                    current_email = "[ENCRYPTED]"
                    current_phone = "[ENCRYPTED]"
                    current_license = "[ENCRYPTED]"

                # Email update
                while True:
                    new_email = input(f"\nEmail ({current_email}): ").strip()
                    if not new_email:
                        break  # Keep current value
                    if new_email.lower() == "skip":
                        break
                    if new_email.lower() == "cancel":
                        print("Update cancelled.")
                        return
                    if self._validate_email(new_email):
                        updates["email"] = encrypt_field(new_email)
                        break
                    else:
                        print("❌ Invalid email format!")
                        retry = self._get_yes_no_input("Try again?")
                        if not retry:
                            break

                # Phone update with clear instructions
                while True:
                    print(f"\n📱 Current Mobile Phone: {current_phone}")
                    print("   Format: +31 6 XXXXXXXX")
                    print("   Enter only the 8 digits after '+31 6'")
                    new_phone = input("Phone (+31 6): ").strip()
                    if not new_phone:
                        break  # Keep current value
                    if new_phone.lower() == "skip":
                        break
                    if new_phone.lower() == "cancel":
                        print("Update cancelled.")
                        return
                    if self._validate_dutch_mobile(new_phone):
                        formatted_phone = self._format_dutch_mobile(new_phone)
                        updates["mobile_phone"] = encrypt_field(formatted_phone)
                        break
                    else:
                        print("❌ Invalid phone format! Enter exactly 8 digits")
                        retry = self._get_yes_no_input("Try again?")
                        if not retry:
                            break

                # Driving License update
                while True:
                    new_license = input(
                        f"\nDriving License ({current_license}): "
                    ).strip()
                    if not new_license:
                        break
                    if new_license.lower() == "skip":
                        break
                    if new_license.lower() == "cancel":
                        print("Update cancelled.")
                        return
                    if self._validate_driving_license(new_license):
                        updates["driving_license"] = encrypt_field(new_license.upper())
                        break
                    else:
                        print(
                            "❌ Invalid driving license format! Use XXDDDDDDD or XDDDDDDDD"
                        )
                        retry = input("Try again? (y/n): ").lower()
                        if retry != "y":
                            break

                # Street Name update
                while True:
                    new_street = input(f"\nStreet Name ({traveler[6]}): ").strip()
                    if not new_street:
                        break
                    if new_street.lower() == "skip":
                        break
                    if new_street.lower() == "cancel":
                        print("Update cancelled.")
                        return
                    updates["street_name"] = new_street
                    break

                # House Number update
                while True:
                    new_house = input(f"\nHouse Number ({traveler[7]}): ").strip()
                    if not new_house:
                        break
                    if new_house.lower() == "skip":
                        break
                    if new_house.lower() == "cancel":
                        print("Update cancelled.")
                        return
                    updates["house_number"] = new_house
                    break

                # Zip Code update
                while True:
                    new_zip = input(
                        f"\nZip Code ({traveler[8]}) - Format 1234AB: "
                    ).strip()
                    if not new_zip:
                        break
                    if new_zip.lower() == "skip":
                        break
                    if new_zip.lower() == "cancel":
                        print("Update cancelled.")
                        return
                    if self._validate_dutch_zipcode(new_zip):
                        updates["zip_code"] = new_zip.upper()
                        break
                    else:
                        print("❌ Invalid zip code format! Use format like 1234AB")
                        retry = self._get_yes_no_input("Try again?")
                        if not retry:
                            break

                # City update with predefined list
                while True:
                    print(f"\nCurrent City: {traveler[9]}")
                    print("Available cities:")
                    for i, city in enumerate(self.PREDEFINED_CITIES, 1):
                        print(f"  {i}. {city}")
                    print("  0. Keep current city")

                    city_choice = input(
                        "Select city number (or enter 'cancel'): "
                    ).strip()
                    if not city_choice or city_choice == "0":
                        break
                    if city_choice.lower() == "cancel":
                        print("Update cancelled.")
                        return

                    try:
                        city_index = int(city_choice) - 1
                        if 0 <= city_index < len(self.PREDEFINED_CITIES):
                            updates["city"] = self.PREDEFINED_CITIES[city_index]
                            break
                        else:
                            print("❌ Invalid selection!")
                    except ValueError:
                        print("❌ Please enter a valid number!")

                if not updates:
                    print("No changes made.")
                    return

                # Show summary of changes (decrypt for display)
                print("\n📋 SUMMARY OF CHANGES:")
                for field, value in updates.items():
                    if field in ["email", "mobile_phone", "driving_license"]:
                        try:
                            display_value = decrypt_field(value)
                        except Exception as e:
                            print(f"Debug: Could not decrypt {field} for display: {e}")
                            display_value = "[ENCRYPTED VALUE]"
                    else:
                        display_value = value
                    print(f"   {field.replace('_', ' ').title()}: {display_value}")

                confirm = self._get_yes_no_input("\nConfirm these changes?")
                if not confirm:
                    print("Update cancelled.")
                    return

                # Build UPDATE query
                set_clause = ", ".join([f"{field} = ?" for field in updates.keys()])
                values = list(updates.values()) + [customer_id]

                cursor.execute(
                    f"""
                    UPDATE travelers
                    SET {set_clause}
                    WHERE customer_id = ?
                """,
                    values,
                )

                conn.commit()

                if cursor.rowcount > 0:
                    print("✅ Traveler updated successfully!")
                else:
                    print("No changes were made.")

        except Exception as e:
            print(f"Error updating traveler: {e}")
        except KeyboardInterrupt:
            print("\nUpdate cancelled.")

    def delete_traveler(self):
        """Delete a traveler"""
        customer_id = input("Enter Customer ID to delete: ").strip()

        if not customer_id:
            print("Customer ID cannot be empty!")
            return

        # First, check if traveler exists
        traveler = self._get_traveler_by_id(customer_id)
        if not traveler:
            print("Traveler not found!")
            return

        print("\nTraveler to be deleted:")
        self._display_traveler_details(traveler)

        # Extra confirmation for deletion (more explicit)
        print("\n⚠️  WARNING: This action cannot be undone!")
        confirmation = input("Type 'DELETE' to confirm deletion: ").strip()

        if confirmation != "DELETE":
            print("Deletion cancelled.")
            return

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM travelers WHERE customer_id = ?", (customer_id,)
                )
                conn.commit()

                if cursor.rowcount > 0:
                    print("✅ Traveler deleted successfully!")
                else:
                    print("Error: Traveler could not be deleted.")

        except Exception as e:
            print(f"Error deleting traveler: {e}")

    def _collect_traveler_data(self):
        """Collect traveler data from user input with complete validation"""
        try:
            data = {}

            # Basic information
            data["first_name"] = self._get_required_input("First Name")
            if not data["first_name"]:
                return None

            data["last_name"] = self._get_required_input("Last Name")
            if not data["last_name"]:
                return None

            # Birthday with validation (European format)
            data["birthday"] = self._get_validated_input(
                "Birthday (DD-MM-YYYY)",
                self._validate_date,
                "Invalid date format! Please use DD-MM-YYYY (e.g., 15-05-1990)",
            )
            if not data["birthday"]:
                return None

            # Gender with validation (assignment specifies male/female)
            data["gender"] = self._get_validated_input(
                "Gender (M/F)",
                lambda x: x.upper() in ["M", "F"],
                "Gender must be M or F",
                transform=lambda x: "Male" if x.upper() == "M" else "Female",
            )
            if not data["gender"]:
                return None

            # Address information
            data["street_name"] = self._get_required_input("Street Name")
            if not data["street_name"]:
                return None

            data["house_number"] = self._get_validated_input(
                "House Number",
                self._validate_house_number,
                "Invalid house number! Must contain at least one digit and be reasonable (1-9999). Examples: 1, 10, 25a, 123b",
            )
            if not data["house_number"]:
                return None

            data["zip_code"] = self._get_validated_input(
                "Zip Code (4 digits + 2 letters, e.g., 1234AB)",
                self._validate_dutch_zipcode,
                "Invalid zip code format! Use format like 1234AB",
                transform=lambda x: x.upper(),
            )
            if not data["zip_code"]:
                return None

            # City selection from predefined list
            data["city"] = self._get_city_selection()
            if not data["city"]:
                return None

            # Contact information
            data["email"] = self._get_validated_input(
                "Email",
                self._validate_email,
                "Invalid email format! Please enter a valid email address",
            )
            if not data["email"]:
                return None

            data["mobile_phone"] = self._get_validated_input(
                "Phone number (+31 6)",
                self._validate_dutch_mobile,
                "Invalid phone format! Enter exactly 8 digits (e.g., 12345678)",
                transform=self._format_dutch_mobile,
            )
            if not data["mobile_phone"]:
                return None

            data["driving_license"] = self._get_validated_input(
                "Driving License Number",
                self._validate_driving_license,
                "Invalid format! Use XXDDDDDDD (e.g., AB1234567) or XDDDDDDDD (e.g., A12345678)",
                transform=lambda x: x.upper(),
            )
            if not data["driving_license"]:
                return None

            return data

        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return None

    def _get_city_selection(self):
        """Get city selection from predefined list"""
        while True:
            try:
                print("\n🏙️ City Selection:")
                print("   Select from the following predefined cities:")
                for i, city in enumerate(self.PREDEFINED_CITIES, 1):
                    print(f"   {i}. {city}")

                choice = input("Enter city number (1-10): ").strip()
                if not choice:
                    print("❌ City selection is required!")
                    retry = input("Try again? (y/n): ").lower()
                    if retry != "y":
                        return None
                    continue

                try:
                    city_index = int(choice) - 1
                    if 0 <= city_index < len(self.PREDEFINED_CITIES):
                        return self.PREDEFINED_CITIES[city_index]
                    else:
                        print("❌ Invalid selection! Please choose 1-10")
                        retry = input("Try again? (y/n): ").lower()
                        if retry != "y":
                            return None
                except ValueError:
                    print("❌ Please enter a valid number!")
                    retry = input("Try again? (y/n): ").lower()
                    if retry != "y":
                        return None
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return None

    def _get_required_input(self, field_name):
        """Get required input with retry capability"""
        while True:
            try:
                value = input(f"{field_name}: ").strip()
                if value:
                    return value
                else:
                    print(f"❌ {field_name} is required!")
                    retry = self._get_yes_no_input("Try again?")
                    if not retry:
                        return None
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return None

    def _get_yes_no_input(self, question):
        """Get a strict yes/no input"""
        while True:
            try:
                response = input(f"{question} (y/n): ").strip().lower()
                if response == "y":
                    return True
                elif response == "n":
                    return False
                else:
                    print("❌ Please enter 'y' for yes or 'n' for no.")
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return False

    def _get_validated_input(
        self, field_name, validator, error_message, transform=None
    ):
        """Get validated input with retry capability"""
        while True:
            try:
                value = input(f"{field_name}: ").strip()
                if not value:
                    print(f"❌ {field_name} is required!")
                    retry = self._get_yes_no_input("Try again?")
                    if not retry:
                        return None
                    continue

                if validator(value):
                    return transform(value) if transform else value
                else:
                    print(f"❌ {error_message}")
                    retry = self._get_yes_no_input("Try again?")
                    if not retry:
                        return None
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return None

    def _generate_customer_id(self):
        """Generate a unique customer ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM travelers")
            count = cursor.fetchone()[0]

            # Generate ID in format CUST000001
            return f"CUST{(count + 1):06d}"

    def _get_traveler_by_id(self, customer_id):
        """Get traveler by customer ID"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM travelers WHERE customer_id = ?", (customer_id,)
                )
                return cursor.fetchone()
        except Exception:
            return None

    def _display_traveler_details(self, traveler):
        """Display detailed traveler information with decrypted sensitive data"""
        if not traveler:
            return

        labels = [
            "ID",
            "Customer ID",
            "First Name",
            "Last Name",
            "Birthday",
            "Gender",
            "Street Name",
            "House Number",
            "Zip Code",
            "City",
            "Email",
            "Mobile Phone",
            "Driving License",
            "Registration Date",
        ]

        print("\nTraveler Details:")
        for i, label in enumerate(labels):
            if i < len(traveler) and traveler[i] is not None:
                value = traveler[i]
                # Decrypt sensitive fields for display
                if label in ["Email", "Mobile Phone", "Driving License"]:
                    try:
                        value = decrypt_field(value)
                    except Exception as e:
                        # Handle Fernet decryption errors (invalid token, corrupted data)
                        print(f"Debug: Decryption error for {label}: {e}")
                        value = "[ENCRYPTED]"
            else:
                value = "N/A"
            print(f"{label}: {value}")

    def _validate_email(self, email):
        """Validate email format"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def _validate_date(self, date_string):
        """Validate date format DD-MM-YYYY (European style)"""
        try:
            datetime.strptime(date_string, "%d-%m-%Y")
            return True
        except ValueError:
            return False

    def _validate_dutch_zipcode(self, zipcode):
        """Validate Dutch zip code format (DDDDXX)"""
        pattern = r"^\d{4}[A-Za-z]{2}$"
        return re.match(pattern, zipcode) is not None

    def _validate_dutch_mobile(self, phone):
        """Validate Dutch mobile phone format (8 digits)"""
        pattern = r"^\d{8}$"
        return re.match(pattern, phone) is not None

    def _format_dutch_mobile(self, phone):
        """Format Dutch mobile phone with +31 6 prefix"""
        return f"+31 6 {phone}"

    def _validate_driving_license(self, license_num):
        """Validate driving license format: XXDDDDDDD or XDDDDDDDD"""
        # Pattern for 1-2 uppercase letters followed by 7 digits
        pattern = r"^[A-Z]{1,2}\d{7}$"
        return re.match(pattern, license_num.upper()) is not None

    def _validate_house_number(self, house_num):
        """Validate house number: must contain at least one digit and be reasonable"""
        # Must contain at least one digit
        if not re.search(r"\d", house_num):
            return False

        # Extract the numeric part
        numbers = re.findall(r"\d+", house_num)
        if not numbers:
            return False

        # Check if the main number is reasonable (1-9999)
        main_number = int(numbers[0])
        if main_number < 1 or main_number > 9999:
            return False

        # Check length is reasonable (not more than 10 characters total)
        if len(house_num) > 10:
            return False

        return True
