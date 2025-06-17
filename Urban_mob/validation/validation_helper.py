from validation.validation import InputValidator, ValidationError
from typing import Dict


class ValidationHelper:

    def __init__(self):
        self.validator = InputValidator()

    def get_validated_input(
        self,
        field_name: str,
        validation_method: str,
        prompt: str,
        max_attempts: int = 3,
    ) -> str:
        validator_method = getattr(self.validator, validation_method)

        for attempt in range(max_attempts):
            try:
                user_input = input(prompt).strip()
                validated_value = validator_method(user_input)
                print(f"✓ {field_name.replace('_', ' ').title()} validated")
                return validated_value

            except ValidationError as e:
                print(f"✗ {e.message}")

                if attempt < max_attempts - 1:
                    while True:
                        retry = input("Try again? (y/n): ").lower().strip()
                        if retry == "y":
                            break
                        elif retry == "n":
                            raise KeyboardInterrupt("User cancelled input")
                        else:
                            print("Please enter 'y' or 'n'.")
                else:
                    print(f"Maximum attempts ({max_attempts}) exceeded")
                    raise KeyboardInterrupt("Too many failed attempts")

        raise KeyboardInterrupt("Failed to get valid input")

    def validate_traveler_interactive(self) -> Dict[str, str]:
        try:
            print("\n--- Enter your data ---")

            data = {}

            data["first_name"] = self.get_validated_input(
                "first_name", "validate_first_name", "First Name: "
            )
            data["last_name"] = self.get_validated_input(
                "last_name", "validate_last_name", "Last Name: "
            )
            data["birthday"] = self.get_validated_input(
                "birthday", "validate_date", "Birthday (DD-MM-YYYY): "
            )

            data["gender"] = self._get_gender_selection()

            data["street_name"] = self.get_validated_input(
                "street_name", "validate_street_name", "Street Name: "
            )
            data["house_number"] = self.get_validated_input(
                "house_number", "validate_house_number", "House Number: "
            )
            data["zip_code"] = self.get_validated_input(
                "zip_code", "validate_dutch_zipcode", "Zip Code (1234AB): "
            )
            data["city"] = self._get_city_selection()

            data["email"] = self.get_validated_input(
                "email", "validate_email", "Email: "
            )
            data["mobile_phone"] = self.get_validated_input(
                "mobile_phone", "validate_dutch_mobile", "Mobile Phone (8 digits): "
            )
            data["driving_license"] = self.get_validated_input(
                "driving_license", "validate_driving_license", "Driving License: "
            )

            print("\n✓ All data collection completed successfully!")
            return data

        except KeyboardInterrupt:
            print("\nData collection cancelled")
            raise

    def _get_gender_selection(self) -> str:
        while True:
            print("\nGender Selection:")
            print("1. Male")
            print("2. Female")

            choice = input("Select (1 or 2): ").strip()

            if choice == "1":
                return "Male"
            elif choice == "2":
                return "Female"
            else:
                print("✗ Invalid selection. Please choose 1 or 2.")
                while True:
                    retry = input("Try again? (y/n): ").lower().strip()
                    if retry == "y":
                        break
                    elif retry == "n":
                        raise KeyboardInterrupt("User cancelled")
                    else:
                        print("Please enter 'y' for yes or 'n' for no.")

    def _get_city_selection(self) -> str:
        while True:
            print("\nCity Selection:")
            for i, city in enumerate(self.validator.VALID_CITIES, 1):
                print(f"{i:2d}. {city}")

            try:
                choice = int(
                    input(f"Select city (1-{len(self.validator.VALID_CITIES)}): ")
                )
                if 1 <= choice <= len(self.validator.VALID_CITIES):
                    selected_city = self.validator.VALID_CITIES[choice - 1]
                    print(f"✓ City validated: {selected_city}")
                    return selected_city
                else:
                    print("✗ Invalid selection")

            except ValueError:
                print("✗ Please enter a number")

            while True:
                retry = input("Try again? (y/n): ").lower().strip()
                if retry == "y":
                    break
                elif retry == "n":
                    raise KeyboardInterrupt("User cancelled")
                else:
                    print("Please enter 'y' for yes or 'n' for no.")
