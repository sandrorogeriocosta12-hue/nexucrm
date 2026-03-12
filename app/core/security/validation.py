"""
Robust input validation module
"""
import re
import json
from typing import Any, Dict, List, Optional, Union
from email_validator import validate_email, EmailNotValidError
import phonenumbers
from pydantic import BaseModel, field_validator, ValidationError
from urllib.parse import urlparse


class InputValidator:
    """Input validation utilities"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address"""
        try:
            validate_email(email)
            return True
        except EmailNotValidError:
            return False

    @staticmethod
    def validate_phone(phone: str, country: str = "BR") -> bool:
        """Validate phone number"""
        try:
            parsed = phonenumbers.parse(phone, country)
            return phonenumbers.is_valid_number(parsed)
        except:
            return False

    @staticmethod
    def validate_cpf(cpf: str) -> bool:
        """Validate Brazilian CPF"""
        cpf = re.sub(r"\D", "", cpf)
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False

        def calc_digit(cpf_slice: str, factor: int) -> int:
            total = sum(
                int(digit) * factor
                for digit, factor in zip(cpf_slice, range(factor, 1, -1))
            )
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder

        digit1 = calc_digit(cpf[:9], 10)
        digit2 = calc_digit(cpf[:10], 11)
        return cpf[-2:] == f"{digit1}{digit2}"

    @staticmethod
    def validate_cnpj(cnpj: str) -> bool:
        """Validate Brazilian CNPJ"""
        cnpj = re.sub(r"\D", "", cnpj)
        if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
            return False

        def calc_digit(cnpj_slice: str, factor: int) -> int:
            total = sum(
                int(digit) * factor
                for digit, factor in zip(cnpj_slice, range(factor, 1, -1))
            )
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder

        digit1 = calc_digit(cnpj[:12], 5)
        digit2 = calc_digit(cnpj[:13], 6)
        return cnpj[-2:] == f"{digit1}{digit2}"

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL with SSRF protection"""
        try:
            parsed = urlparse(url)
            # Prevent SSRF by checking for localhost/private IPs
            if (
                parsed.hostname in ["localhost", "127.0.0.1", "0.0.0.0"]
                or parsed.hostname.startswith("192.168.")
                or parsed.hostname.startswith("10.")
            ):
                return False
            return parsed.scheme in ["http", "https"]
        except:
            return False

    @staticmethod
    def detect_sql_injection(input_str: str) -> bool:
        """Detect potential SQL injection"""
        sql_patterns = [
            r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b",
            r"(\bOR\b|\bAND\b).*(\=|\<|\>)",
            r"(\'\"\").*(\;|\#|\-\-)",
            r"(\bUNION\b|\bJOIN\b).*(\bSELECT\b)",
        ]
        for pattern in sql_patterns:
            if re.search(pattern, input_str, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def detect_xss(input_str: str) -> bool:
        """Detect potential XSS"""
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>.*?</iframe>",
            r"<object[^>]*>.*?</object>",
        ]
        for pattern in xss_patterns:
            if re.search(pattern, input_str, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def detect_command_injection(input_str: str) -> bool:
        """Detect potential command injection"""
        cmd_patterns = [
            r"[;&|`$()]",
            r"\b(rm|del|format|shutdown|reboot)\b",
            r"\.\./",
            r"\b(cat|more|less|tail|head)\b.*\b/etc/passwd\b",
        ]
        for pattern in cmd_patterns:
            if re.search(pattern, input_str, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def detect_path_traversal(input_str: str) -> bool:
        """Detect path traversal attempts"""
        if "../" in input_str or "..\\" in input_str:
            return True
        return False

    @staticmethod
    def validate_json(input_str: str) -> bool:
        """Validate JSON format"""
        try:
            json.loads(input_str)
            return True
        except:
            return False


class SecureBaseModel(BaseModel):
    """Base model with automatic validation"""

    @field_validator("*", mode="before")
    @classmethod
    def validate_input(cls, v):
        """Validate each field input"""
        if isinstance(v, str):
            if InputValidator.detect_sql_injection(v):
                raise ValueError(f"Potential SQL injection detected")
            if InputValidator.detect_xss(v):
                raise ValueError(f"Potential XSS detected")
            if InputValidator.detect_command_injection(v):
                raise ValueError(f"Potential command injection detected")
            if InputValidator.detect_path_traversal(v):
                raise ValueError(f"Potential path traversal detected")
        return v


# Example models
class UserRegistration(SecureBaseModel):
    email: str
    password: str
    phone: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validate_email_field(cls, v):
        if not InputValidator.validate_email(v):
            raise ValueError("Invalid email format")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone_field(cls, v):
        if v and not InputValidator.validate_phone(v):
            raise ValueError("Invalid phone number")
        return v


class FileUpload(SecureBaseModel):
    filename: str
    content_type: str
    size: int

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v):
        if InputValidator.detect_path_traversal(v):
            raise ValueError("Invalid filename")
        return v
