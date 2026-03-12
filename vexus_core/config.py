import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Configurações básicas
    SECRET_KEY = os.getenv("SECRET_KEY", "vexus-clinica-secret-key-2024")

    # Banco de dados
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///vexus.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # WhatsApp Business API
    WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
    WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    WHATSAPP_API_URL = (
        f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )

    # OpenAI (para respostas inteligentes)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Horário de funcionamento padrão para clínicas
    CLINIC_HOURS = {
        "monday": {"open": "08:00", "close": "18:00"},
        "tuesday": {"open": "08:00", "close": "18:00"},
        "wednesday": {"open": "08:00", "close": "18:00"},
        "thursday": {"open": "08:00", "close": "18:00"},
        "friday": {"open": "08:00", "close": "18:00"},
        "saturday": {"open": "08:00", "close": "12:00"},
        "sunday": {"open": None, "close": None},
    }
