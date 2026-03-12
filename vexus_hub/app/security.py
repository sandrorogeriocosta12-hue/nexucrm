"""
Flask Security Integration
Integração dos módulos de segurança no sistema Flask
"""
import os
import logging
from functools import wraps
from flask import request, g, current_app, jsonify
from werkzeug.exceptions import BadRequest

# Importar módulos de segurança (root-level package)
import os, sys
# inserir caminho para diretório '/app' do workspace no topo do path
_root_app = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'app'))
if _root_app not in sys.path:
    sys.path.insert(0, _root_app)
from core.security.validation import InputValidator
from core.security.rate_limiting import rate_limiter, ddos_protection, RateLimitConfig
from core.security.logging import log_authentication, log_attack_attempt, SecurityEventType, log_rate_limit_exceeded
from core.security.config import security_config

class FlaskSecurityMiddleware:
    """Middleware de segurança para Flask"""

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Inicializar middleware com app Flask"""

        # Configurar logging de segurança
        security_logger = logging.getLogger('security')
        security_logger.setLevel(logging.INFO)

        # Handler para arquivo
        from logging.handlers import RotatingFileHandler
        handler = RotatingFileHandler(
            os.path.join(app.root_path, '../../logs/security.log'),
            maxBytes=10*1024*1024,
            backupCount=5
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        security_logger.addHandler(handler)

        # Registrar callbacks
        app.before_request(self.before_request)
        app.after_request(self.after_request)

        # Adicionar headers de segurança
        app.after_request(self.add_security_headers)

        # Tratamento de erros
        app.register_error_handler(400, self.handle_bad_request)
        app.register_error_handler(429, self.handle_rate_limit)

    def before_request(self):
        """Executado antes de cada request"""
        client_ip = self._get_client_ip()

        # Verificar DDoS
        if ddos_protection.detect_ddos(client_ip):
            rate_limiter.block_ip(client_ip)
            log_attack_attempt(
                SecurityEventType.SQL_INJECTION_ATTEMPT,
                client_ip,
                "DDoS attack detected",
                request.path,
                getattr(g, 'user_id', None)
            )
            return jsonify({"error": "Too Many Requests - DDoS Protection"}), 429

        # Verificar rate limiting
        config = RateLimitConfig(
            requests_per_minute=security_config.RATE_LIMIT_REQUESTS_PER_MINUTE,
            requests_per_hour=security_config.RATE_LIMIT_REQUESTS_PER_HOUR,
            requests_per_day=security_config.RATE_LIMIT_REQUESTS_PER_DAY
        )

        if not rate_limiter.is_allowed(client_ip, config):
            log_rate_limit_exceeded(client_ip, request.path, 0)
            return jsonify({"error": "Too Many Requests"}), 429

        # Validar inputs para POST/PUT/PATCH
        if request.method in ['POST', 'PUT', 'PATCH']:
            self._validate_request_data()

    def after_request(self, response):
        """Executado após cada request"""
        return response

    def add_security_headers(self, response):
        """Adicionar headers de segurança"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = security_config.X_FRAME_OPTIONS
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = f'max-age={security_config.HSTS_MAX_AGE}'
        response.headers['Content-Security-Policy'] = security_config.CSP_POLICY
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    def handle_bad_request(self, error):
        """Tratamento de BadRequest"""
        return jsonify({"error": "Invalid input data"}), 400

    def handle_rate_limit(self, error):
        """Tratamento de rate limit"""
        return jsonify({"error": "Too Many Requests"}), 429

    def _get_client_ip(self):
        """Obter IP do cliente"""
        x_forwarded_for = request.headers.get('X-Forwarded-For')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.remote_addr or 'unknown'

    def _validate_request_data(self):
        """Validar dados do request"""
        client_ip = self._get_client_ip()

        # Validar query parameters
        for key, value in request.args.items():
            if isinstance(value, str):
                if InputValidator.detect_sql_injection(value):
                    log_attack_attempt(
                        SecurityEventType.SQL_INJECTION_ATTEMPT,
                        client_ip, value, request.path,
                        getattr(g, 'user_id', None)
                    )
                    raise BadRequest("Invalid input detected")

                if InputValidator.detect_xss(value):
                    log_attack_attempt(
                        SecurityEventType.XSS_ATTEMPT,
                        client_ip, value, request.path,
                        getattr(g, 'user_id', None)
                    )
                    raise BadRequest("Invalid input detected")

        # Validar JSON body
        if request.is_json:
            try:
                data = request.get_json()
                self._validate_json_data(data, client_ip)
            except Exception as e:
                current_app.logger.warning(f"JSON validation error: {e}")

        # Validar form data
        elif request.form:
            for key, value in request.form.items():
                if isinstance(value, str):
                    if InputValidator.detect_sql_injection(value):
                        log_attack_attempt(
                            SecurityEventType.SQL_INJECTION_ATTEMPT,
                            client_ip, value, request.path,
                            getattr(g, 'user_id', None)
                        )
                        raise BadRequest("Invalid input detected")

    def _validate_json_data(self, data, client_ip):
        """Validar dados JSON recursivamente"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    if InputValidator.detect_sql_injection(value):
                        log_attack_attempt(
                            SecurityEventType.SQL_INJECTION_ATTEMPT,
                            client_ip, value, request.path,
                            getattr(g, 'user_id', None)
                        )
                        raise BadRequest("Invalid input detected")
                    if InputValidator.detect_xss(value):
                        log_attack_attempt(
                            SecurityEventType.XSS_ATTEMPT,
                            client_ip, value, request.path,
                            getattr(g, 'user_id', None)
                        )
                        raise BadRequest("Invalid input detected")
                elif isinstance(value, (dict, list)):
                    self._validate_json_data(value, client_ip)
        elif isinstance(data, list):
            for item in data:
                self._validate_json_data(item, client_ip)


def secure_login_required(f):
    """Decorator para endpoints que requerem autenticação segura"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar se usuário está logado
        if not hasattr(g, 'user') or g.user is None:
            log_authentication(
                success=False,
                username=getattr(g, 'user_id', 'unknown'),
                source_ip=request.remote_addr or 'unknown'
            )
            return jsonify({"error": "Authentication required"}), 401

        # Log de autenticação bem-sucedida
        log_authentication(
            success=True,
            username=g.user.email if hasattr(g.user, 'email') else str(g.user.id),
            source_ip=request.remote_addr or 'unknown'
        )

        return f(*args, **kwargs)
    return decorated_function


def validate_input(*fields):
    """Decorator para validar inputs específicos"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr or 'unknown'

            for field in fields:
                if field in request.args:
                    value = request.args[field]
                    if InputValidator.detect_sql_injection(value):
                        log_attack_attempt(
                            SecurityEventType.SQL_INJECTION_ATTEMPT,
                            client_ip, value, request.path,
                            getattr(g, 'user_id', None)
                        )
                        raise BadRequest(f"Invalid input in field: {field}")

                if request.is_json and field in request.get_json():
                    value = request.get_json()[field]
                    if isinstance(value, str) and InputValidator.detect_sql_injection(value):
                        log_attack_attempt(
                            SecurityEventType.SQL_INJECTION_ATTEMPT,
                            client_ip, value, request.path,
                            getattr(g, 'user_id', None)
                        )
                        raise BadRequest(f"Invalid input in field: {field}")

            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Instância global do middleware
security_middleware = FlaskSecurityMiddleware()