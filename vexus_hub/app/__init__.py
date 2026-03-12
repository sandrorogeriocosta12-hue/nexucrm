import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from flask_socketio import SocketIO
from config import config

# Configurar path para módulos de segurança
sys.path.insert(0, '/home/victor-emanuel/PycharmProjects/Vexus Service')

# Importar segurança
from .security import security_middleware

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cors = CORS()
socketio = SocketIO(cors_allowed_origins="*")

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV') or 'default'

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Inicializar extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    cors.init_app(app)
    socketio.init_app(app)

    # Inicializar segurança
    security_middleware.init_app(app)

    # Configurar login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Import all models to ensure they are registered with SQLAlchemy
    from app import models

    # Registrar blueprints
    from app.routes import register_blueprints
    register_blueprints(app)

    # Inicializar configurações
    config[config_name].init_app(app)

    return app