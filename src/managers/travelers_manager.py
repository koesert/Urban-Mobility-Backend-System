import re
from datetime import datetime
from data.encryption import decrypt_field, encrypt_field
from validation.validation import InputValidator, ValidationError
from validation.validation_helper import ValidationHelper


class TravelersManager:
    def __init__(self, auth_service):
        self.auth = auth_service
        self.db = auth_service.db

        self.validator = InputValidator()
        self.validation_helper = ValidationHelper()
        self.PREDEFINED_CITIES = self.validator.VALID_CITIES

        self._verify_encryption_system()

    def _verify_encryption_system(self):
        try:
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
        if not self.auth.current_user:
            return False

        user_role = self.auth.current_user["role"]
        return user_role in ["super_admin", "system_admin"]

    def _validate_email(self, email: str) -> bool:
        try:
            self.validator.validate_email(email)
            return True
        except ValidationError:
            return False

    def _validate_date(self, date_str: str) -> bool:
        try:
            self.validator.validate_date(date_str)
            return True
        except ValidationError:
            return False

    def _validate_dutch_zipcode(self, zipcode: str) -> bool:
        try:
            self.validator.validate_dutch_zipcode(zipcode)
            return True
        except ValidationError:
            return False

    def _validate_dutch_mobile(self, phone: str) -> bool:
        try:
            self.validator.validate_dutch_mobile(phone)
            return True
        except ValidationError:
            return False

    def _format_dutch_mobile(self, phone: str) -> str:
        return self.validator.validate_dutch_mobile(phone)

    def _validate_driving_license(self, license_num: str) -> bool:
        try:
            self.validator.validate_driving_license(license_num)
            return True
        except ValidationError:
            return False

    def _validate_house_number(self, house_num: str) -> bool:
        try:
            self.validator.validate_house_number(house_num)
            return True
        except ValidationError:
            return False

    def display_travelers_menu(self):
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

                    try:
                        decrypted_email = decrypt_field(email)
                        decrypted_phone = decrypt_field(phone)
                    except Exception:
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
        try:
            search_term = input("Enter search term: ").strip()

            self.validator._check_sql_injection(search_term, "search_term")

            if len(search_term) < 1:
                print("Search term cannot be empty!")
                return

        except ValidationError as e:
            print(f"Invalid search term: {e.message}")
            return

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
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

                cursor.execute("SELECT * FROM travelers")
                all_travelers = cursor.fetchall()

                for traveler in all_travelers:
                    try:
                        decrypted_email = decrypt_field(traveler[10])
                        if search_term.lower() in decrypted_email.lower():
                            if traveler not in travelers:
                                travelers.append(traveler)
                    except Exception as e:
                        continue

                if not travelers:
                    print("No travelers found matching your search.")
                    return

                for traveler in travelers:
                    self.display_traveler_details(traveler)
                    print("-" * 50)

        except Exception as e:
            print(f"Error searching travelers: {e}")

    def add_traveler(self):
        print("\n--- ADD NEW TRAVELER ---")

        try:
            traveler_data = self._collect_traveler_data()
            if not traveler_data:
                return

            # Validate user input first
            validated_data = self.validator.validate_traveler_data(
                traveler_data)

            # Add system-generated fields after validation
            customer_id = self._generate_customer_id()
            validated_data["customer_id"] = customer_id
            validated_data["registration_date"] = datetime.now().isoformat()

            self._show_traveler_summary(validated_data)

            confirm = self._get_yes_no_input("\nSave this traveler?")
            if not confirm:
                print("Traveler not saved.")
                return

            self.db.insert_traveler(validated_data)

            print(f"\nTraveler added successfully!")
            print(f"Customer ID: {customer_id}")
            print(
                f"Name: {validated_data['first_name']} {validated_data['last_name']}")

            self.auth.logger.log_activity(
                username=self.auth.current_user["username"],
                activity="Add traveler",
                details=f"Traveler with customer ID: {customer_id} added."
            )

        except ValidationError as e:
            print(f"Validation failed: {e.message}")
        except Exception as e:
            print(f"Error adding traveler: {e}")

    def update_traveler(self):
        customer_id = input("Enter Customer ID to update: ").strip()

        if not customer_id:
            print("Customer ID cannot be empty!")
            return

        traveler = self._get_traveler_by_id(customer_id)
        if not traveler:
            print("Traveler not found!")
            return

        print("\nCurrent traveler information:")
        self.display_traveler_details(traveler)

        print("\n📝 UPDATE TRAVELER INFORMATION")
        print("Enter new information (press Enter to keep current value)")
        print("Type 'skip' to skip a field, or 'cancel' to cancel the update")

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                updates = {}

                try:
                    current_email = decrypt_field(traveler[10])
                    current_phone = decrypt_field(traveler[11])
                    current_license = decrypt_field(traveler[12])
                except Exception as e:
                    print(
                        f"Warning: Could not decrypt current traveler data: {e}")
                    current_email = "[ENCRYPTED]"
                    current_phone = "[ENCRYPTED]"
                    current_license = "[ENCRYPTED]"

                while True:
                    new_email = input(f"\nEmail ({current_email}): ").strip()
                    if not new_email:
                        break
                    if new_email.lower() == "skip":
                        break
                    if new_email.lower() == "cancel":
                        print("Update cancelled.")
                        return
                    try:
                        validated_email = self.validator.validate_email(
                            new_email)
                        updates["email"] = encrypt_field(validated_email)
                        print("✓ Email validated")
                        break
                    except ValidationError as e:
                        print(f"✗ {e.message}")
                        retry = self._get_yes_no_input("Try again?")
                        if not retry:
                            break

                while True:
                    print(f"\n📱 Current Mobile Phone: {current_phone}")
                    print("   Format: +31 6 XXXXXXXX")
                    print("   Enter only the 8 digits after '+31 6'")
                    new_phone = input("Phone (+31 6): ").strip()
                    if not new_phone:
                        break
                    if new_phone.lower() == "skip":
                        break
                    if new_phone.lower() == "cancel":
                        print("Update cancelled.")
                        return
                    try:
                        validated_phone = self.validator.validate_dutch_mobile(
                            new_phone
                        )
                        updates["mobile_phone"] = encrypt_field(
                            validated_phone)
                        print("✓ Phone validated and formatted")
                        break
                    except ValidationError as e:
                        print(f"✗ {e.message}")
                        retry = self._get_yes_no_input("Try again?")
                        if not retry:
                            break

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
                    try:
                        validated_license = self.validator.validate_driving_license(
                            new_license
                        )
                        updates["driving_license"] = encrypt_field(
                            validated_license)
                        print("✓ Driving license validated")
                        break
                    except ValidationError as e:
                        print(f"✗ {e.message}")
                        retry = self._get_yes_no_input("Try again?")
                        if not retry:
                            break

                while True:
                    new_street = input(
                        f"\nStreet Name ({traveler[6]}): ").strip()
                    if not new_street:
                        break
                    if new_street.lower() == "skip":
                        break
                    if new_street.lower() == "cancel":
                        print("Update cancelled.")
                        return
                    try:
                        validated_street = self.validator.validate_street_name(
                            new_street
                        )
                        updates["street_name"] = validated_street
                        print("✓ Street name validated")
                        break
                    except ValidationError as e:
                        print(f"✗ {e.message}")
                        retry = self._get_yes_no_input("Try again?")
                        if not retry:
                            break

                while True:
                    new_house = input(
                        f"\nHouse Number ({traveler[7]}): ").strip()
                    if not new_house:
                        break
                    if new_house.lower() == "skip":
                        break
                    if new_house.lower() == "cancel":
                        print("Update cancelled.")
                        return
                    try:
                        validated_house = self.validator.validate_house_number(
                            new_house
                        )
                        updates["house_number"] = validated_house
                        print("✓ House number validated")
                        break
                    except ValidationError as e:
                        print(f"✗ {e.message}")
                        retry = self._get_yes_no_input("Try again?")
                        if not retry:
                            break

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
                    try:
                        validated_zip = self.validator.validate_dutch_zipcode(
                            new_zip)
                        updates["zip_code"] = validated_zip
                        print("✓ Zip code validated")
                        break
                    except ValidationError as e:
                        print(f"✗ {e.message}")
                        retry = self._get_yes_no_input("Try again?")
                        if not retry:
                            break

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
                            selected_city = self.PREDEFINED_CITIES[city_index]
                            updates["city"] = selected_city
                            print(f"✓ City validated: {selected_city}")
                            break
                        else:
                            print("✗ Invalid selection!")
                    except ValueError:
                        print("✗ Please enter a valid number!")

                if not updates:
                    print("No changes made.")
                    return

                print("\n📋 SUMMARY OF CHANGES:")
                for field, value in updates.items():
                    if field in ["email", "mobile_phone", "driving_license"]:
                        try:
                            display_value = decrypt_field(value)
                        except Exception as e:
                            display_value = "[ENCRYPTED VALUE]"
                    else:
                        display_value = value
                    print(
                        f"   {field.replace('_', ' ').title()}: {display_value}")

                confirm = self._get_yes_no_input("\nConfirm these changes?")
                if not confirm:
                    print("Update cancelled.")
                    return

                set_clause = ", ".join(
                    [f"{field} = ?" for field in updates.keys()])
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

                    self.auth.logger.log_activity(
                        username=self.auth.current_user["username"],
                        activity="Update traveler",
                        details=f"Traveler with customer ID: {customer_id} updated."
                    )
                else:
                    print("No changes were made.")

        except Exception as e:
            print(f"Error updating traveler: {e}")
        except KeyboardInterrupt:
            print("\nUpdate cancelled.")

    def delete_traveler(self):
        customer_id = input("Enter Customer ID to delete: ").strip()

        if not customer_id:
            print("Customer ID cannot be empty!")
            return

        traveler = self._get_traveler_by_id(customer_id)
        if not traveler:
            print("Traveler not found!")
            return

        print("\nTraveler to be deleted:")
        self.display_traveler_details(traveler)

        print("\n⚠️  WARNING: This action cannot be undone!")
        confirmation = input("Type 'DELETE' to confirm deletion: ").strip()

        if confirmation != "DELETE":
            print("Deletion cancelled.")
            return

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM travelers WHERE customer_id = ?", (
                        customer_id,)
                )
                conn.commit()

                if cursor.rowcount > 0:
                    print("✅ Traveler deleted successfully!")

                    self.auth.logger.log_activity(
                        username=self.auth.current_user["username"],
                        activity="Delete traveler",
                        details=f"Traveler with customer ID: {customer_id} deleted."
                    )
                else:
                    print("Error: Traveler could not be deleted.")

        except Exception as e:
            print(f"Error deleting traveler: {e}")

    def _collect_traveler_data(self):
        try:
            data = self.validation_helper.validate_traveler_interactive()
            print("All data validated successfully!")
            return data
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return None

    def _get_city_selection(self):
        while True:
            try:
                print("\n🏙️ City Selection:")
                print("   Select from the following predefined cities:")
                for i, city in enumerate(self.PREDEFINED_CITIES, 1):
                    print(f"   {i}. {city}")

                choice = input("Enter city number (1-10): ").strip()
                if not choice:
                    print("City selection is required!")
                    continue

                try:
                    city_index = int(choice) - 1
                    if 0 <= city_index < len(self.PREDEFINED_CITIES):
                        return self.PREDEFINED_CITIES[city_index]
                    else:
                        print("Invalid selection! Please choose 1-10")
                except ValueError:
                    print("Please enter a valid number!")

            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return None

    def _get_required_input(self, field_name):
        while True:
            try:
                value = input(f"{field_name}: ").strip()
                if value:
                    return value
                else:
                    print(f"{field_name} is required!")
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return None

    def _get_yes_no_input(self, question):
        while True:
            try:
                response = input(f"{question} (y/n): ").strip().lower()
                if response == "y":
                    return True
                elif response == "n":
                    return False
                else:
                    print("Please enter 'y' for yes or 'n' for no.")
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return False

    def _get_validated_input(
        self, field_name, validator, error_message, transform=None
    ):
        while True:
            try:
                value = input(f"{field_name}: ").strip()
                if not value:
                    print(f"{field_name} is required!")
                    continue

                if validator(value):
                    return transform(value) if transform else value
                else:
                    print(f"{error_message}")

            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return None

    def _generate_customer_id(self):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM travelers")
            count = cursor.fetchone()[0]

            return f"CUST{(count + 1):06d}"

    def _get_traveler_by_id(self, customer_id):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM travelers WHERE customer_id = ?", (customer_id,)
                )
                return cursor.fetchone()
        except Exception:
            return None

    def _show_traveler_summary(self, data):
        print("\nTRAVELER SUMMARY:")
        print(f"   Name: {data['first_name']} {data['last_name']}")
        print(f"   Birthday: {data['birthday']}")
        print(f"   Gender: {data['gender']}")
        print(f"   Address: {data['street_name']} {data['house_number']}")
        print(f"   City: {data['city']} {data['zip_code']}")
        print(f"   Email: {data['email']}")
        print(f"   Mobile: {data['mobile_phone']}")
        print(f"   License: {data['driving_license']}")

    def display_traveler_details(self, traveler_data):
        if not traveler_data:
            print("No traveler data to display.")
            return

        try:
            (
                traveler_id,
                customer_id,
                first_name,
                last_name,
                birthday,
                gender,
                street_name,
                house_number,
                zip_code,
                city,
                encrypted_email,
                encrypted_mobile_phone,
                encrypted_driving_license,
                registration_date,
            ) = traveler_data

            print("\n" + "=" * 50)
            print(f"TRAVELER DETAILS - ID: {customer_id}")
            print("=" * 50)

            print(f"Name: {first_name} {last_name}")
            print(f"Birthday: {birthday}")
            print(f"Gender: {gender}")
            print(f"Address: {street_name} {house_number}")
            print(f"Zip Code: {zip_code}")
            print(f"City: {city}")
            print(f"Registration Date: {registration_date}")

            try:
                email = decrypt_field(encrypted_email)
                mobile_phone = decrypt_field(encrypted_mobile_phone)
                driving_license = decrypt_field(encrypted_driving_license)

                print(f"Email: {email}")
                print(f"Mobile Phone: {mobile_phone}")
                print(f"Driving License: {driving_license}")

            except Exception as e:
                print(f"Email: [ENCRYPTED] (Decryption failed)")
                print(f"Mobile Phone: [ENCRYPTED] (Decryption failed)")
                print(f"Driving License: [ENCRYPTED] (Decryption failed)")
                print(f"Decryption error: {str(e)}")

            print("=" * 50)

        except ValueError as e:
            print(
                f"Error displaying traveler details: Invalid data format - {str(e)}")
        except Exception as e:
            print(f"Error displaying traveler details: {str(e)}")

    def _display_traveler_details(self, traveler_data):
        """Alias method for compatibility"""
        return self.display_traveler_details(traveler_data)
