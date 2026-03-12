import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

from app.utils.email import send_email, send_welcome_email
from app.utils.validators import validate_email, validate_phone, validate_cpf_cnpj
from app.utils.formatters import format_currency, format_date, format_phone
from app.utils.cache import cache_response, clear_cache

class TestEmailUtils:
"""Testes para utilitários de email"""

@pytest.mark.asyncio
async def test_send_email_success(self):
"""Testa envio de email bem-sucedido"""
with patch("app.utils.email.smtplib.SMTP") as mock_smtp:
mock_server = MagicMock()
mock_smtp.return_value.__enter__.return_value = mock_server

result = await send_email(
to_email="test@example.com",
subject="Test Subject",
body="Test Body"
)

assert result is True
mock_server.sendmail.assert_called_once()

@pytest.mark.asyncio
async def test_send_welcome_email(self):
"""Testa envio de email de boas-vindas"""
with patch("app.utils.email.send_email") as mock_send:
mock_send.return_value = True

result = await send_welcome_email(
to_email="newuser@example.com",
username="New User"
)

assert result is True
mock_send.assert_called_once()

# Verifica que o assunto contém "Welcome"
call_args = mock_send.call_args[1]
assert "Welcome" in call_args["subject"]
assert "New User" in call_args["body"]

class TestValidators:
"""Testes para validadores"""

def test_validate_email_valid(self):
"""Testa validação de email válido"""
valid_emails = [
"test@example.com",
"user.name@domain.co.uk",
"user+tag@example.com",
"user@sub.domain.com"
]

for email in valid_emails:
assert validate_email(email) is True

def test_validate_email_invalid(self):
"""Testa validação de email inválido"""
invalid_emails = [
"invalid-email",
"@example.com",
"user@.com",
"user@com.",
"user@domain..com"
]

for email in invalid_emails:
assert validate_email(email) is False

def test_validate_phone_valid(self):
"""Testa validação de telefone válido"""
valid_phones = [
"+5511999999999",
"+552122222222",
"11999999999",
"(11) 99999-9999",
"11 99999 9999"
]

for phone in valid_phones:
assert validate_phone(phone) is True

def test_validate_cpf_valid(self):
"""Testa validação de CPF válido"""
valid_cpfs = [
"123.456.789-09",
"98765432100"
]

for cpf in valid_cpfs:
assert validate_cpf_cnpj(cpf) is True

def test_validate_cnpj_valid(self):
"""Testa validação de CNPJ válido"""
valid_cnpjs = [
"12.345.678/0001-95",
"98765432000189"
]

for cnpj in valid_cnpjs:
assert validate_cpf_cnpj(cnpj, doc_type="cnpj") is True

class TestFormatters:
"""Testes para formatadores"""

def test_format_currency(self):
"""Testa formatação de moeda"""
test_cases = [
(1000, "R$ 1.000,00"),
(1500.50, "R$ 1.500,50"),
(0, "R$ 0,00"),
(-500, "R$ -500,00"),
(1234567.89, "R$ 1.234.567,89")
]

for value, expected in test_cases:
assert format_currency(value) == expected

def test_format_date(self):
"""Testa formatação de data"""
date = datetime(2024, 1, 15)

assert format_date(date) == "15/01/2024"
assert format_date(date, format="short") == "15/01/24"
assert format_date(date, format="iso") == "2024-01-15"
assert format_date(date, format="full") == "15 de janeiro de 2024"

def test_format_phone(self):
"""Testa formatação de telefone"""
test_cases = [
("11999999999", "(11) 99999-9999"),
("1122222222", "(11) 2222-2222"),
("+5511999999999", "+55 11 99999-9999"),
("123456", "123456") # Não formata se muito curto
]

for phone, expected in test_cases:
assert format_phone(phone) == expected

class TestCacheUtils:
"""Testes para utilitários de cache"""

@pytest.mark.asyncio
async def test_cache_response(self):
"""Testa cache de resposta"""
mock_redis = AsyncMock()
mock_redis.get.return_value = None
mock_redis.set.return_value = True

key = "test_key"
data = {"message": "Hello World"}

with patch("app.utils.cache.redis_client", mock_redis):
result = await cache_response(key, data, ttl=300)

assert result == data
mock_redis.set.assert_called_once()

@pytest.mark.asyncio
async def test_cache_response_hit(self):
"""Testa cache hit"""
cached_data = '{"message": "Cached"}'
mock_redis = AsyncMock()
mock_redis.get.return_value = cached_data

with patch("app.utils.cache.redis_client", mock_redis):
result = await cache_response("test_key", {"new": "data"})

assert result == {"message": "Cached"}
mock_redis.set.assert_not_called()

@pytest.mark.asyncio
async def test_clear_cache(self):
"""Testa limpeza de cache"""
mock_redis = AsyncMock()
mock_redis.delete.return_value = 1

with patch("app.utils.cache.redis_client", mock_redis):
result = await clear_cache("test_key")

assert result == 1
mock_redis.delete.assert_called_once_with("test_key")