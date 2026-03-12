import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Segurança
    SECRET_KEY = os.getenv('SECRET_KEY', 'vexus-ai-production-secret-2024')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-vexus-2024')

    # Banco de Dados
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/vexus_hub')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }

    # WhatsApp Business API
    WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
    WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv('WHATSAPP_BUSINESS_ACCOUNT_ID')
    WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN', 'vexus2024verify')

    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_ORGANIZATION = os.getenv('OPENAI_ORGANIZATION', None)

    # Google Calendar API
    GOOGLE_CALENDAR_CREDENTIALS = os.getenv('GOOGLE_CALENDAR_CREDENTIALS')
    GOOGLE_CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID')

    # Twilio (SMS alternativo)
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

    # Redis para Celery e Cache
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL

    # Email
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@vexus.ai')

    # Upload de Arquivos
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

    # Configurações da Aplicação
    TIMEZONE = 'America/Sao_Paulo'
    DEFAULT_CLINIC_HOURS = {
        'weekdays': {'start': '08:00', 'end': '18:00'},
        'saturday': {'start': '08:00', 'end': '12:00'},
        'sunday': None
    }

    # Planos e Preços
    PRICING_PLANS = {
        'bronze': {
            'monthly_price': 297.00,
            'setup_fee': 500.00,
            'whatsapp_messages': 1000,
            'features': ['chatbot_whatsapp', 'basic_analytics']
        },
        'silver': {
            'monthly_price': 1497.00,
            'setup_fee': 0.00,
            'whatsapp_messages': 5000,
            'features': ['chatbot_whatsapp', 'social_media_management', 'advanced_analytics', 'email_support']
        },
        'gold': {
            'monthly_price': 3500.00,
            'setup_fee': 0.00,
            'whatsapp_messages': 'unlimited',
            'features': ['all_silver_features', 'google_calendar_sync', 'phone_support', 'custom_development']
        }
    }

    @staticmethod
    def init_app(app):
        # Criar pasta de uploads se não existir
        if not os.path.exists(Config.UPLOAD_FOLDER):
            os.makedirs(Config.UPLOAD_FOLDER)

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL', 'sqlite:///vexus_dev.db')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('TEST_DATABASE_URL', 'sqlite:///:memory:')
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    # Forçar HTTPS em produção
    PREFERRED_URL_SCHEME = 'https'
    # Configurações de segurança adicionais
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}