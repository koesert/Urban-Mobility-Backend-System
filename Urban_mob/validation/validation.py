import re
from datetime import datetime
from typing import Dict, Any


class ValidationError(Exception):
    def __init__(self, field_name: str, message: str):
        self.field_name = field_name
        self.message = message
        super().__init__(f"{field_name}: {message}")


class InputValidator:

    VALID_CITIES = [
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

    def validate_email(self, email: str) -> str:
        if not email or not isinstance(email, str):
            raise ValidationError("email", "Email is required")

        email = email.strip().lower()
        self._check_sql_injection(email, "email")

        pattern = r"^[a-zA-Z0-9._+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email):
            raise ValidationError("email", "Invalid email format")

        if ".." in email or email.startswith(".") or email.endswith("."):
            raise ValidationError("email", "Invalid email format")

        return email

    def validate_dutch_zipcode(self, zipcode: str) -> str:
        if not zipcode or not isinstance(zipcode, str):
            raise ValidationError("zipcode", "Zip code is required")

        zipcode = zipcode.strip().upper()
        self._check_sql_injection(zipcode, "zipcode")

        pattern = r"^\d{4}[A-Z]{2}$"
        if not re.match(pattern, zipcode):
            raise ValidationError("zipcode", "Invalid zip code format. Use: 1234AB")

        return zipcode

    def validate_dutch_mobile(self, phone: str) -> str:
        if not phone or not isinstance(phone, str):
            raise ValidationError("phone", "Mobile phone is required")

        phone = phone.strip()
        self._check_sql_injection(phone, "phone")

        pattern = r"^\d{8}$"
        if not re.match(pattern, phone):
            raise ValidationError(
                "phone", "Invalid phone format. Enter exactly 8 digits"
            )

        return f"+31 6 {phone}"

    def validate_driving_license(self, license_num: str) -> str:
        if not license_num or not isinstance(license_num, str):
            raise ValidationError("driving_license", "Driving license is required")

        license_num = license_num.strip().upper()
        self._check_sql_injection(license_num, "driving_license")

        pattern = r"^[A-Z]{1,2}\d{7}$"
        if not re.match(pattern, license_num):
            raise ValidationError(
                "driving_license", "Invalid format. Use: AB1234567 or A1234567"
            )

        return license_num

    def validate_date(self, date_str: str) -> str:
        if not date_str or not isinstance(date_str, str):
            raise ValidationError("date", "Date is required")

        date_str = date_str.strip()
        self._check_sql_injection(date_str, "date")

        try:
            datetime.strptime(date_str, "%d-%m-%Y")
            return date_str
        except ValueError:
            raise ValidationError("date", "Invalid date format. Use DD-MM-YYYY")

    def validate_first_name(self, name: str) -> str:
        if not name or not isinstance(name, str):
            raise ValidationError("first_name", "First name is required")

        name = name.strip()
        self._check_sql_injection(name, "first_name")

        if len(name) < 1:
            raise ValidationError("first_name", "First name cannot be empty")

        if len(name) > 50:
            raise ValidationError("first_name", "First name too long")

        if not re.match(r"^[a-zA-ZÀ-ÿ\s\-'\.]+$", name):
            raise ValidationError(
                "first_name",
                "First name can only contain letters, spaces, hyphens, and apostrophes",
            )

        if re.search(r"\d", name):
            raise ValidationError("first_name", "First name cannot contain numbers")

        return name

    def validate_last_name(self, name: str) -> str:
        if not name or not isinstance(name, str):
            raise ValidationError("last_name", "Last name is required")

        name = name.strip()
        self._check_sql_injection(name, "last_name")

        if len(name) < 1:
            raise ValidationError("last_name", "Last name cannot be empty")

        if len(name) > 50:
            raise ValidationError("last_name", "Last name too long")

        if not re.match(r"^[a-zA-ZÀ-ÿ\s\-'\.]+$", name):
            raise ValidationError(
                "last_name",
                "Last name can only contain letters, spaces, hyphens, and apostrophes",
            )

        if re.search(r"\d", name):
            raise ValidationError("last_name", "Last name cannot contain numbers")

        return name

    def validate_street_name(self, street: str) -> str:
        if not street or not isinstance(street, str):
            raise ValidationError("street_name", "Street name is required")

        street = street.strip()
        self._check_sql_injection(street, "street_name")

        if len(street) < 1:
            raise ValidationError("street_name", "Street name cannot be empty")

        if len(street) > 100:
            raise ValidationError("street_name", "Street name too long")

        if not re.match(r"^[a-zA-ZÀ-ÿ0-9\s\-'\.]+$", street):
            raise ValidationError(
                "street_name", "Street name contains invalid characters"
            )

        if not re.search(r"[a-zA-ZÀ-ÿ]", street):
            raise ValidationError(
                "street_name", "Street name must contain at least one letter"
            )

        return street

    def validate_house_number(self, house_num: str) -> str:
        if not house_num or not isinstance(house_num, str):
            raise ValidationError("house_number", "House number is required")

        house_num = house_num.strip()
        self._check_sql_injection(house_num, "house_number")

        # Reject if starts with hyphen (negative number)
        if house_num.startswith("-"):
            raise ValidationError("house_number", "House number cannot be negative")

        if not re.search(r"\d", house_num):
            raise ValidationError(
                "house_number", "House number must contain at least one digit"
            )

        if not re.match(r"^[a-zA-Z0-9\-]+$", house_num):
            raise ValidationError(
                "house_number",
                "House number can only contain letters, numbers, and hyphens",
            )

        numbers = re.findall(r"\d+", house_num)
        if not numbers:
            raise ValidationError("house_number", "Invalid house number")

        main_number = int(numbers[0])
        if main_number < 1 or main_number > 9999:
            raise ValidationError(
                "house_number", "House number must be between 1 and 9999"
            )

        return house_num

    def validate_city(self, city: str) -> str:
        if not city or not isinstance(city, str):
            raise ValidationError("city", "City is required")

        city = city.strip()
        self._check_sql_injection(city, "city")

        if city not in self.VALID_CITIES:
            raise ValidationError(
                "city", f"Invalid city. Must be one of: {', '.join(self.VALID_CITIES)}"
            )

        return city

    def validate_gender(self, gender: str) -> str:
        if not gender or not isinstance(gender, str):
            raise ValidationError("gender", "Gender is required")

        gender = gender.strip()
        self._check_sql_injection(gender, "gender")

        if gender not in ["Male", "Female"]:
            raise ValidationError("gender", "Gender must be Male or Female")

        return gender

    def _check_sql_injection(self, value: str, field_name: str):
        dangerous_patterns = [
            r"('|(\\'))",
            r"(;|(\\);)",
            r"(union|UNION)",
            r"(select|SELECT)",
            r"(insert|INSERT)",
            r"(update|UPDATE)",
            r"(delete|DELETE)",
            r"(drop|DROP)",
            r"(--)",
            r"(/\*|\*/)",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, value):
                print(
                    f"SECURITY ALERT: SQL injection attempt detected in {field_name}: {value[:20]}..."
                )
                raise ValidationError(
                    field_name, "Input contains potentially dangerous content"
                )

    def validate_traveler_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        cleaned_data = {}

        cleaned_data["first_name"] = self.validate_first_name(
            data.get("first_name") or ""
        )
        cleaned_data["last_name"] = self.validate_last_name(data.get("last_name") or "")
        cleaned_data["birthday"] = self.validate_date(data.get("birthday") or "")
        cleaned_data["gender"] = self.validate_gender(data.get("gender") or "")
        cleaned_data["street_name"] = self.validate_street_name(
            data.get("street_name") or ""
        )
        cleaned_data["house_number"] = self.validate_house_number(
            data.get("house_number") or ""
        )
        cleaned_data["zip_code"] = self.validate_dutch_zipcode(
            data.get("zip_code") or ""
        )
        cleaned_data["city"] = self.validate_city(data.get("city") or "")
        cleaned_data["email"] = self.validate_email(data.get("email") or "")
        cleaned_data["mobile_phone"] = self.validate_dutch_mobile(
            data.get("mobile_phone") or ""
        )
        cleaned_data["driving_license"] = self.validate_driving_license(
            data.get("driving_license") or ""
        )

        return cleaned_data
