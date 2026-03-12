"""
Security tests for Vexus Service
"""
import pytest
from app.core.security.validation import InputValidator, SecureBaseModel
from app.core.security.rate_limiting import AdvancedRateLimiter, RateLimitConfig
from pydantic import ValidationError


class TestInputValidation:
    """Test input validation functionality"""

    def test_email_validation(self):
        """Test email validation"""
        assert InputValidator.validate_email("test@example.com") == True
        assert InputValidator.validate_email("invalid-email") == False

    def test_phone_validation(self):
        """Test phone validation"""
        assert InputValidator.validate_phone("+55 11 99999-9999", "BR") == True
        assert InputValidator.validate_phone("invalid-phone", "BR") == False

    def test_sql_injection_detection(self):
        """Test SQL injection detection"""
        assert InputValidator.detect_sql_injection("SELECT * FROM users") == True
        assert InputValidator.detect_sql_injection("Hello world") == False

    def test_xss_detection(self):
        """Test XSS detection"""
        assert InputValidator.detect_xss("<script>alert('xss')</script>") == True
        assert InputValidator.detect_xss("Hello world") == False

    def test_secure_base_model(self):
        """Test secure base model validation"""

        class TestModel(SecureBaseModel):
            name: str
            email: str

        # Valid input
        model = TestModel(name="John Doe", email="john@example.com")
        assert model.name == "John Doe"
        assert model.email == "john@example.com"

        # Invalid input with SQL injection
        with pytest.raises(ValidationError):
            TestModel(name="John'; DROP TABLE users;--", email="john@example.com")


class TestRateLimiting:
    """Test rate limiting functionality"""

    def test_rate_limiter(self):
        """Test basic rate limiting"""
        limiter = AdvancedRateLimiter()
        config = RateLimitConfig(requests_per_minute=10)

        # Should allow initial requests
        for i in range(10):
            assert limiter.is_allowed("test_ip", config) == True

        # Should block 11th request
        assert limiter.is_allowed("test_ip", config) == False

    def test_ddos_protection(self):
        """Test DDoS protection"""
        from app.core.security.rate_limiting import DDoSProtection

        ddos = DDoSProtection(threshold=5)

        # Simulate normal traffic
        for i in range(3):
            assert ddos.detect_ddos("192.168.1.1") == False

        # Simulate DDoS
        for i in range(3):
            ddos.detect_ddos("192.168.1.1")

        assert ddos.detect_ddos("192.168.1.1") == True


class TestSecretsManagement:
    """Test secrets management functionality"""

    @pytest.mark.asyncio
    async def test_local_secrets(self):
        """Test local secrets manager"""
        from app.core.security.secrets import LocalSecretsManager

        manager = LocalSecretsManager()

        # Test setting and getting secret
        await manager.set_secret("test_key", "test_value")
        value = await manager.get_secret("test_key")
        assert value == "test_value"

        # Test non-existent secret
        value = await manager.get_secret("non_existent")
        assert value is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
