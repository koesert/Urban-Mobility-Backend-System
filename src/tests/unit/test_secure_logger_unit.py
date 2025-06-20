import os
import tempfile
import pytest
from unittest.mock import patch
from data.secure_logger import SecureLogger


class TestSecureLoggerUnit:
    def setup_method(self):
        # Use a temporary log file for each test
        self.temp_log = tempfile.NamedTemporaryFile(delete=False)
        self.log_path = self.temp_log.name
        self.temp_log.close()
        patcher = patch("data.secure_logger.LOG_FILE_PATH", self.log_path)
        self.addCleanup = patcher.stop
        patcher.start()
        self.logger = SecureLogger()

    def teardown_method(self):
        if os.path.exists(self.log_path):
            os.unlink(self.log_path)
        self.addCleanup()

    def test_log_activity_marks_suspicious_and_alerts(self):
        self.logger.log_activity(
            "admin", "Suspicious Activity", "Details", suspicious=True)
        alerts = self.logger.check_suspicious_activity()
        assert any("Suspicious Activity" in alert.get("activity", "")
                   for alert in alerts)
        # Alerts should be cleared after reading
        assert self.logger.check_suspicious_activity() == []

    def test_read_logs_permission_denied(self):
        self.logger.log_activity("user", "Test", "Details")
        with pytest.raises(PermissionError):
            self.logger.read_logs("service_engineer")
