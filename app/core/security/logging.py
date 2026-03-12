"""
Security logging module with structured logging and compliance
"""

import json
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict
import uuid


class SecurityEventType(Enum):
    AUTHENTICATION_SUCCESS = "auth_success"
    AUTHENTICATION_FAILURE = "auth_failure"
    AUTHORIZATION_FAILURE = "authz_failure"
    INPUT_VALIDATION_ERROR = "input_validation_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    COMMAND_INJECTION_ATTEMPT = "command_injection_attempt"
    PATH_TRAVERSAL_ATTEMPT = "path_traversal_attempt"
    FILE_UPLOAD_VIOLATION = "file_upload_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SECURITY_HEADERS_MISSING = "security_headers_missing"
    SSL_TLS_ISSUE = "ssl_tls_issue"
    SECRET_ACCESS = "secret_access"
    SECRET_ROTATION = "secret_rotation"
    CONFIGURATION_CHANGE = "configuration_change"


class SecurityLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class SecurityEvent:
    """Security event data structure"""

    event_id: str
    event_type: SecurityEventType
    level: SecurityLevel
    timestamp: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    compliance_tags: Optional[list] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging"""
        data = asdict(self)
        data["event_type"] = self.event_type.value
        data["level"] = self.level.value
        if self.compliance_tags:
            data["compliance_tags"] = self.compliance_tags
        return data


class SecurityLogger:
    """Security logger with structured output"""

    def __init__(self, name: str = "security", log_file: str = "logs/security.log"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Create logs directory if it doesn't exist
        import os

        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # JSON formatter
        formatter = logging.Formatter("%(message)s")

        # File handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def log_event(self, event: SecurityEvent):
        """Log a security event"""
        log_entry = event.to_dict()
        message = json.dumps(log_entry, default=str)

        if event.level == SecurityLevel.CRITICAL:
            self.logger.critical(message)
        elif event.level == SecurityLevel.ERROR:
            self.logger.error(message)
        elif event.level == SecurityLevel.WARNING:
            self.logger.warning(message)
        else:
            self.logger.info(message)

    def log_authentication(
        self,
        success: bool,
        username: str,
        source_ip: str,
        user_agent: Optional[str] = None,
        details: Optional[Dict] = None,
    ):
        """Log authentication event"""
        event_type = (
            SecurityEventType.AUTHENTICATION_SUCCESS
            if success
            else SecurityEventType.AUTHENTICATION_FAILURE
        )
        level = SecurityLevel.INFO if success else SecurityLevel.WARNING

        event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            level=level,
            timestamp=datetime.utcnow().isoformat(),
            user_id=username,
            ip_address=source_ip,
            user_agent=user_agent,
            action="login",
            details=details,
            compliance_tags=["GDPR", "LGPD", "PCI-DSS"],
        )
        self.log_event(event)

    def log_authorization_failure(
        self,
        user_id: str,
        resource: str,
        action: str,
        ip_address: str,
        details: Optional[Dict] = None,
    ):
        """Log authorization failure"""
        event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=SecurityEventType.AUTHORIZATION_FAILURE,
            level=SecurityLevel.WARNING,
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id,
            ip_address=ip_address,
            resource=resource,
            action=action,
            details=details,
            compliance_tags=["GDPR", "LGPD"],
        )
        self.log_event(event)

    def log_input_validation_error(
        self,
        field: str,
        value: str,
        error_type: str,
        ip_address: str,
        user_id: Optional[str] = None,
    ):
        """Log input validation error"""
        event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=SecurityEventType.INPUT_VALIDATION_ERROR,
            level=SecurityLevel.WARNING,
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id,
            ip_address=ip_address,
            resource=field,
            action="input_validation",
            details={"error_type": error_type, "value_length": len(value)},
            compliance_tags=["GDPR", "LGPD"],
        )
        self.log_event(event)

    def log_rate_limit_exceeded(
        self, ip_address: str, endpoint: str, request_count: int
    ):
        """Log rate limit exceeded"""
        event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            level=SecurityLevel.WARNING,
            timestamp=datetime.utcnow().isoformat(),
            ip_address=ip_address,
            resource=endpoint,
            action="rate_limit",
            details={"request_count": request_count},
            compliance_tags=["PCI-DSS"],
        )
        self.log_event(event)

    def log_attack_attempt(
        self,
        attack_type: SecurityEventType,
        ip_address: str,
        payload: str,
        endpoint: str,
        user_id: Optional[str] = None,
    ):
        """Log security attack attempt"""
        event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=attack_type,
            level=SecurityLevel.ERROR,
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id,
            ip_address=ip_address,
            resource=endpoint,
            action="attack_attempt",
            details={"payload_length": len(payload)},
            compliance_tags=["GDPR", "LGPD", "PCI-DSS"],
        )
        self.log_event(event)


# Global logger instance
_security_logger: Optional[SecurityLogger] = None


def get_logger(log_file: str = "logs/security.log") -> SecurityLogger:
    """Get or create global security logger"""
    global _security_logger
    if _security_logger is None:
        _security_logger = SecurityLogger(log_file=log_file)
    return _security_logger


def log_event(event: SecurityEvent):
    """Log a security event using global logger"""
    logger = get_logger()
    logger.log_event(event)


def log_authentication(
    success: bool,
    username: str,
    source_ip: str,
    user_agent: Optional[str] = None,
    details: Optional[Dict] = None,
):
    """Convenience wrapper for authentication events"""
    logger = get_logger()
    logger.log_authentication(success, username, source_ip, user_agent, details)


def log_authorization_failure(
    user_id: str,
    resource: str,
    action: str,
    ip_address: str,
    details: Optional[Dict] = None,
):
    logger = get_logger()
    logger.log_authorization_failure(user_id, resource, action, ip_address, details)


def log_input_validation_error(
    field: str,
    value: str,
    error_type: str,
    ip_address: str,
    user_id: Optional[str] = None,
):
    logger = get_logger()
    logger.log_input_validation_error(field, value, error_type, ip_address, user_id)


def log_rate_limit_exceeded(ip_address: str, endpoint: str, request_count: int):
    logger = get_logger()
    logger.log_rate_limit_exceeded(ip_address, endpoint, request_count)


def log_attack_attempt(
    attack_type: SecurityEventType,
    ip_address: str,
    payload: str,
    endpoint: str,
    user_id: Optional[str] = None,
):
    logger = get_logger()
    logger.log_attack_attempt(attack_type, ip_address, payload, endpoint, user_id)
