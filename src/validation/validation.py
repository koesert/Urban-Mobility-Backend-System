import re
from datetime import datetime
from typing import Dict, Any, List, Optional
import unicodedata
import html


class ValidationError(Exception):
    def __init__(self, field_name: str, message: str):
        self.field_name = field_name
        self.message = message
        super().__init__(f"{field_name}: {message}")


class SecurityError(ValidationError):
    """Specific error for security violations"""

    def __init__(
        self, field_name: str, message: str, attempted_value: Optional[str] = None
    ):
        super().__init__(field_name, message)
        self.attempted_value = attempted_value


class InputValidator:
    """Enhanced input validator with comprehensive SQL injection prevention"""

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

    # Comprehensive SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(?i)\b(select|insert|update|delete|drop|create|alter|truncate|exec|execute|union|fetch|declare|cast|convert|having|merge)\b",
        r"('|\")",
        r"(--|#|/\*|\*/)",
        r"(;)",  # Semicolon
        r"(\|\||&&)",  # Logical OR/AND
        r"(=|!=|<>|<|>|<=|>=)",  # Comparison operators
        r"(?i)(0x[0-9a-f]+)",  # Hexadecimal attack
        r"(?i)(char\s*\(|concat\s*\(|substring\s*\()",  # String functions
        r"(?i)(into\s+(outfile|dumpfile))",  # File writing
        r"(?i)(load_file\s*\()",  # Local file inclusion
        r"(?i)(benchmark\s*\(|sleep\s*\(|waitfor\s+delay)",  # Delays
        r"(?i)(\$where|\$ne|\$eq|\$gt|\$lt|\$gte|\$lte|\$in|\$nin)",  # MongoDB operators
        r"(?i)(\.find\(|\.findOne\(|\.aggregate\()",  # MongoDB methods
        r"(\(|\)|\&|\||\!|\*)",  # Miscellaneous
        r"(?i)(ancestor::|descendant::|following::|parent::|self::)",  # XPath injection
        r"(;|\||&|`|\$\(|\${)",  # Shell metacharacters
        r"(?i)(cmd|powershell|bash|sh|wget|curl|nc|netcat)",  # Command injection
        r"(\.\.\/|\.\.\\|%2e%2e%2f|%252e%252e%252f)",  # Directory traversal
        r"(%00|\\x00|\\0)",  # Null byte
        r"(%u[0-9a-f]{4}|\\u[0-9a-f]{4})",  # Unicode
        r"(?i)(if\s*\(|case\s+when)",  # Conditional statements
        r"(?i)(and\s+\d+\s*=\s*\d+|or\s+\d+\s*=\s*\d+)",  # Tautology
        r"(?i)(;\s*(select|insert|update|delete|drop))",  # Chained queries
        r"(?i)(stored_procedure|sp_|xp_)",  # Stored procedures
        r"(<!ENTITY|<!DOCTYPE|<!\[CDATA\[)",  # XML injection
    ]

    SUSPICIOUS_PATTERNS = [
        r"\s{2,}",
        r"(?i)(SeLeCt|InSeRt|UpDaTe|DeLeTe)",
        r"(/\*!\d+|\*/)",
        r"(?i)(@@version|@@datadir|@@hostname)",
        r"(?i)(database\(\)|user\(\)|version\(\))",
        r"(%27|%22|%3D|%3B|%2D%2D|%23|%2F%2A|%2A%2F)",
        r"(&#x27;|&#39;|&#x22;|&#34;)",  # HTML entities
        r"(?i)(chr\(|ascii\(|ord\()",  # ASCII functions
        r"(?i)(unhex\(|hex\()",  # Hexadecimal functions
    ]

    FIELD_WHITELISTS = {
        "email": r"^[a-zA-Z0-9._+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "phone": r"^\d{8}$",
        "zipcode": r"^\d{4}[A-Z]{2}$",
        "driving_license": r"^[A-Z]{1,2}\d{7}$",
        "date": r"^\d{2}-\d{2}-\d{4}$",
        "name": r"^[a-zA-ZÀ-ÿ\s\-\'\.]+$",
        "street": r"^[a-zA-ZÀ-ÿ0-9\s\-\'\.]+$",
        "house_number": r"^[a-zA-Z0-9\-]+$",
    }

    def __init__(self, log_security_events: bool = True):
        self.log_security_events = log_security_events
        self.security_log: List[Dict[str, Any]] = []

    def _log_security_event(
        self,
        event_type: str,
        field_name: str,
        value: str,
        pattern_matched: Optional[str] = None,
    ):
        if self.log_security_events:
            event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "field_name": field_name,
                "attempted_value": value[:50] + "..." if len(value) > 50 else value,
                "pattern_matched": pattern_matched,
            }
            self.security_log.append(event)
            print(
                f"🚨 SECURITY ALERT: {event_type} in {field_name}: {event['attempted_value']}"
            )

    def _normalize_input(self, value: str) -> str:
        value = unicodedata.normalize("NFKC", value)
        value = html.unescape(value)
        value = value.replace("\x00", "").replace("\0", "")
        value = " ".join(value.split())
        return value

    def _check_length_limits(
        self, value: str, field_name: str, min_length: int = 1, max_length: int = 255
    ):
        if len(value) < min_length:
            raise ValidationError(
                field_name, f"Input too short (minimum {min_length} characters)"
            )
        if len(value) > max_length:
            raise ValidationError(
                field_name, f"Input too long (maximum {max_length} characters)"
            )

    def _check_sql_injection_advanced(
        self, value: str, field_name: str, strict_mode: bool = True
    ):
        normalized_value = self._normalize_input(value)
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, normalized_value, re.IGNORECASE):
                self._log_security_event("SQL_INJECTION_ATTEMPT", field_name, value, pattern)
                raise SecurityError(
                    field_name,
                    "Security violation: Input contains potentially dangerous content",
                    value,
                )
        if strict_mode:
            for pattern in self.SUSPICIOUS_PATTERNS:
                if re.search(pattern, normalized_value, re.IGNORECASE):
                    self._log_security_event("SUSPICIOUS_PATTERN", field_name, value, pattern)
                    raise SecurityError(
                        field_name,
                        "Security warning: Input contains suspicious patterns",
                        value,
                    )
        self._check_encoded_attacks(normalized_value, field_name)
        self._check_context_specific_attacks(normalized_value, field_name)

    def _check_encoded_attacks(self, value: str, field_name: str):
        if re.search(r"%25[0-9a-fA-F]{2}", value):
            self._log_security_event("DOUBLE_ENCODING_ATTEMPT", field_name, value)
            raise SecurityError(field_name, "Double encoding detected")
        if re.search(r"\\u[0-9a-fA-F]{4}", value) or re.search(r"%u[0-9a-fA-F]{4}", value):
            self._log_security_event("UNICODE_ENCODING_ATTACK", field_name, value)
            raise SecurityError(field_name, "Unicode encoding attack detected")
        try:
            value.encode("utf-8").decode("utf-8")
        except UnicodeDecodeError:
            self._log_security_event("INVALID_UTF8", field_name, value)
            raise SecurityError(field_name, "Invalid UTF-8 sequence detected")

    def _check_context_specific_attacks(self, value: str, field_name: str):
        if "email" in field_name.lower():
            if re.search(r"[<>'\"]", value):
                self._log_security_event("EMAIL_INJECTION", field_name, value)
                raise SecurityError(field_name, "Email contains invalid characters")
        if any(term in field_name.lower() for term in ["path", "file", "directory"]):
            if re.search(r"(\.\.\/|\.\.\\|%2e%2e)", value, re.IGNORECASE):
                self._log_security_event("PATH_TRAVERSAL", field_name, value)
                raise SecurityError(field_name, "Path traversal attempt detected")

    def _whitelist_validation(self, value: str, field_type: str) -> bool:
        pattern = self.FIELD_WHITELISTS.get(field_type)
        if pattern:
            return bool(re.match(pattern, value))
        return True

    def validate_email(self, email: str) -> str:
        if not email or not isinstance(email, str):
            raise ValidationError("email", "Email is required")
        email = email.strip().lower()
        self._check_length_limits(email, "email", min_length=5, max_length=254)
        self._check_sql_injection_advanced(email, "email")
        if not self._whitelist_validation(email, "email"):
            raise ValidationError("email", "Invalid email format")
        if ".." in email or email.startswith(".") or email.endswith("."):
            raise ValidationError("email", "Invalid email format")
        if re.search(r"[\r\n]", email):
            self._log_security_event("EMAIL_HEADER_INJECTION", "email", email)
            raise SecurityError("email", "Email header injection attempt detected")
        return email

    def validate_dutch_zipcode(self, zipcode: str) -> str:
        if not zipcode or not isinstance(zipcode, str):
            raise ValidationError("zipcode", "Zip code is required")
        zipcode = zipcode.strip().upper()
        self._check_length_limits(zipcode, "zipcode", min_length=6, max_length=6)
        self._check_sql_injection_advanced(zipcode, "zipcode")
        if not self._whitelist_validation(zipcode, "zipcode"):
            raise ValidationError("zipcode", "Invalid zip code format. Use: 1234AB")
        return zipcode

    def validate_dutch_mobile(self, phone: str) -> str:
        if not phone or not isinstance(phone, str):
            raise ValidationError("phone", "Mobile phone is required")
        phone = phone.strip()
        if re.match(r"^\+31 6 \d{8}$", phone):
            return phone
        self._check_length_limits(phone, "phone", min_length=8, max_length=8)
        self._check_sql_injection_advanced(phone, "phone")
        if not self._whitelist_validation(phone, "phone"):
            raise ValidationError("phone", "Invalid phone format. Enter exactly 8 digits")
        return f"+31 6 {phone}"

    def validate_driving_license(self, license_num: str) -> str:
        if not license_num or not isinstance(license_num, str):
            raise ValidationError("driving_license", "Driving license is required")
        license_num = license_num.strip().upper()
        self._check_length_limits(license_num, "driving_license", min_length=8, max_length=9)
        self._check_sql_injection_advanced(license_num, "driving_license")
        if not self._whitelist_validation(license_num, "driving_license"):
            raise ValidationError("driving_license", "Invalid format. Use: AB1234567 or A1234567")
        return license_num

    def validate_date(self, date_str: str) -> str:
        if not date_str or not isinstance(date_str, str):
            raise ValidationError("date", "Date is required")
        date_str = date_str.strip()
        self._check_length_limits(date_str, "date", min_length=10, max_length=10)
        self._check_sql_injection_advanced(date_str, "date")
        if not self._whitelist_validation(date_str, "date"):
            raise ValidationError("date", "Invalid date format. Use DD-MM-YYYY")
        try:
            datetime.strptime(date_str, "%d-%m-%Y")
            return date_str
        except ValueError:
            raise ValidationError("date", "Invalid date format. Use DD-MM-YYYY")

    def validate_name(self, name: str, field_type: str = "name") -> str:
        if not name or not isinstance(name, str):
            raise ValidationError(
                field_type, f"{field_type.replace('_', ' ').title()} is required"
            )
        name = name.strip()
        self._check_length_limits(name, field_type, min_length=1, max_length=50)
        self._check_sql_injection_advanced(name, field_type)
        if not self._whitelist_validation(name, "name"):
            raise ValidationError(
                field_type,
                f"{field_type.replace('_', ' ').title()} can only contain letters, spaces, hyphens, and apostrophes",
            )
        if re.search(r"\d", name):
            raise ValidationError(field_type, f"{field_type.replace('_', ' ').title()} cannot contain numbers")
        if re.search(r"<[^>]+>", name):
            self._log_security_event("HTML_INJECTION", field_type, name)
            raise SecurityError(field_type, "HTML/Script injection attempt detected")
        return name

    def validate_first_name(self, name: str) -> str:
        return self.validate_name(name, "first_name")

    def validate_last_name(self, name: str) -> str:
        return self.validate_name(name, "last_name")

    def validate_street_name(self, street: str) -> str:
        if not street or not isinstance(street, str):
            raise ValidationError("street_name", "Street name is required")
        street = street.strip()
        self._check_length_limits(street, "street_name", min_length=1, max_length=100)
        self._check_sql_injection_advanced(street, "street_name", strict_mode=False)
        if not self._whitelist_validation(street, "street"):
            raise ValidationError("street_name", "Street name contains invalid characters")
        if not re.search(r"[a-zA-ZÀ-ÿ]", street):
            raise ValidationError("street_name", "Street name must contain at least one letter")
        return street

    def validate_house_number(self, house_num: str) -> str:
        if not house_num or not isinstance(house_num, str):
            raise ValidationError("house_number", "House number is required")
        house_num = house_num.strip()
        self._check_length_limits(house_num, "house_number", min_length=1, max_length=10)
        self._check_sql_injection_advanced(house_num, "house_number")
        if house_num.startswith("-"):
            raise ValidationError("house_number", "House number cannot be negative")
        if not self._whitelist_validation(house_num, "house_number"):
            raise ValidationError("house_number", "House number can only contain letters, numbers, and hyphens")
        numbers = re.findall(r"\d+", house_num)
        if not numbers:
            raise ValidationError("house_number", "Invalid house number")
        main_number = int(numbers[0])
        if main_number < 1 or main_number > 9999:
            raise ValidationError("house_number", "House number must be between 1 and 9999")
        return house_num

    def validate_city(self, city: str) -> str:
        if not city or not isinstance(city, str):
            raise ValidationError("city", "City is required")
        city = city.strip()
        self._check_sql_injection_advanced(city, "city")
        if city not in self.VALID_CITIES:
            raise ValidationError(
                "city", f"Invalid city. Must be one of: {', '.join(self.VALID_CITIES)}"
            )
        return city

    def validate_gender(self, gender: str) -> str:
        if not gender or not isinstance(gender, str):
            raise ValidationError("gender", "Gender is required")
        gender = gender.strip()
        self._check_sql_injection_advanced(gender, "gender")
        if gender not in ["Male", "Female"]:
            raise ValidationError("gender", "Gender must be Male or Female")
        return gender

    def validate_traveler_data(self, data: Dict[str, Any]) -> Dict[str, str]:
        cleaned_data = {}
        cleaned_data["first_name"] = self.validate_first_name(data.get("first_name", ""))
        cleaned_data["last_name"] = self.validate_last_name(data.get("last_name", ""))
        cleaned_data["birthday"] = self.validate_date(data.get("birthday", ""))
        cleaned_data["gender"] = self.validate_gender(data.get("gender", ""))
        cleaned_data["street_name"] = self.validate_street_name(data.get("street_name", ""))
        cleaned_data["house_number"] = self.validate_house_number(data.get("house_number", ""))
        cleaned_data["zip_code"] = self.validate_dutch_zipcode(data.get("zip_code", ""))
        cleaned_data["city"] = self.validate_city(data.get("city", ""))
        cleaned_data["email"] = self.validate_email(data.get("email", ""))
        cleaned_data["mobile_phone"] = self.validate_dutch_mobile(data.get("mobile_phone", ""))
        cleaned_data["driving_license"] = self.validate_driving_license(data.get("driving_license", ""))
        return cleaned_data

    def get_security_report(self) -> List[Dict[str, Any]]:
        return self.security_log.copy()

    def clear_security_log(self):
        self.security_log.clear()


# Example usage and testing
if __name__ == "__main__":
    validator = InputValidator(log_security_events=True)
    test_inputs = [
        ("email", "admin@test.com'; DROP TABLE users; --"),
        ("first_name", "John'; INSERT INTO admin VALUES('hacker'); --"),
        ("street_name", "Main Street' UNION SELECT * FROM passwords --"),
        ("last_name", "Smith', $ne: null"),
        ("house_number", "123; rm -rf /"),
        ("first_name", "<script>alert('xss')</script>"),
        ("email", "test@еxample.com"),
        ("street_name", "../../etc/passwd"),
        ("email", "test%27@example.com%20OR%201=1"),
        ("email", "valid.user@example.com"),
        ("first_name", "María José"),
        ("mobile_phone", "12345678"),
    ]
    print("🔒 Testing Enhanced SQL Injection Prevention\n")
    for field, value in test_inputs:
        try:
            validate_method = getattr(validator, f"validate_{field}")
            result = validate_method(value)
            print(f"✅ {field}: '{value}' -> VALID: '{result}'")
        except SecurityError as e:
            print(f"🚫 {field}: '{value}' -> BLOCKED (Security): {e.message}")
        except ValidationError as e:
            print(f"❌ {field}: '{value}' -> INVALID: {e.message}")
        print()
    print("\n📊 Security Event Report:")
    for event in validator.get_security_report():
        print(f"  - {event['timestamp']}: {event['event_type']} in {event['field_name']}: {event['attempted_value']}")
