import csv
import io
from datetime import datetime
from .encryption import encrypt_field, decrypt_field

LOG_FILE_PATH = "secure_audit.log"


class SuspiciousLogAlert:
    def __init__(self):
        self.alerts = []

    def add_alert(self, log_entry):
        self.alerts.append(log_entry)

    def get_unread_alerts(self):
        unread = self.alerts.copy()
        self.alerts.clear()
        return unread


class SecureLogger:
    def __init__(self):
        self.alert_system = SuspiciousLogAlert()
        self._initialize_log_file()

    def _initialize_log_file(self):
        try:
            with open(LOG_FILE_PATH, "rb") as f:
                pass
        except FileNotFoundError:
            header = encrypt_field(
                "Date,Time,Username,Activity,Details,Suspicious\n")
            with open(LOG_FILE_PATH, "wb") as f:
                f.write(header.encode())

    def log_activity(self, username, activity, details="", suspicious=False):
        timestamp = datetime.now()
        log_data = {
            "date": timestamp.strftime("%d-%m-%Y"),
            "time": timestamp.strftime("%H:%M:%S"),
            "username": username,
            "activity": activity,
            "details": details,
            "suspicious": "Yes" if suspicious else "No"
        }

        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=log_data.keys())
        writer.writerow(log_data)
        encrypted_entry = encrypt_field(buffer.getvalue())

        with open(LOG_FILE_PATH, "ab") as log_file:
            log_file.write(encrypted_entry.encode() + b"\n")

        if suspicious:
            self.alert_system.add_alert(log_data)

    def check_suspicious_activity(self):
        return self.alert_system.get_unread_alerts()

    def read_logs(self, requester_role: str) -> list:
        """Read and decrypt logs, only accessible by admins"""
        if requester_role not in ["super_admin", "system_admin"]:
            raise PermissionError("Insufficient privileges to view logs")

        try:
            with open(LOG_FILE_PATH, "rb") as f:
                encrypted_logs = f.readlines()
        except FileNotFoundError:
            return []

        decrypted = []
        reader = csv.reader(
            # Header
            [self._decrypt_entry(encrypted_logs[0]).lstrip('\ufeff')] +
            [self._decrypt_entry(e) for e in encrypted_logs[1:]])

        next(reader)  # Skip header
        for idx, row in enumerate(reader, 1):
            if len(row) == 5:  # Handle missing suspicious flag in old entries
                row.append('No')
            decrypted.append({
                "no": idx,
                "date": row[0],
                "time": row[1],
                "username": row[2],
                "activity": row[3],
                "details": row[4],
                "suspicious": row[5]
            })

        return decrypted

    def _decrypt_entry(self, encrypted_entry: bytes) -> str:
        try:
            return decrypt_field(encrypted_entry.decode().strip())
        except:
            return "Corrupted log entry"
        return {
            "no": None,  # Calculated during display
            "date": date,
            "time": time,
            "username": user,
            "activity": activity,
            "details": details,
            "suspicious": suspicious
        }
