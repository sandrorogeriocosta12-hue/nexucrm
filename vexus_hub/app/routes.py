from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app.security import secure_login_required
from flask_login import login_required, current_user
from app.models import db, Clinic, Appointment, Patient, Conversation, Service
from app.dashboard_metrics import DashboardMetrics
from app.appointment_scheduler import AppointmentScheduler
from app.whatsapp_integration import WhatsAppWebhookHandler
import json

main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)
auth_bp = Blueprint('auth', __name__)

# Routes principais
@main_bp.route('/')
@login_required
def index():
    """Dashboard principal"""
    clinics = Clinic.query.filter_by(user_id=current_user.id).all()
    if len(clinics) == 1:
        return redirect(url_for('main.dashboard', clinic_id=clinics[0].id))
    return render_template('index.html', clinics=clinics)

@main_bp.route('/dashboard/<clinic_id>')
@login_required
def dashboard(clinic_id):
    """Dashboard da empresa"""
    clinic = Clinic.query.filter_by(id=clinic_id, user_id=current_user.id).first_or_404()
    metrics = DashboardMetrics.get_kpi_dashboard(clinic_id)
    return render_template('dashboard.html', clinic=clinic, metrics=metrics)

@main_bp.route('/clinics')
@login_required
def clinics():
    """Lista de empresas"""
    clinics = Clinic.query.filter_by(user_id=current_user.id).all()
    return render_template('clinics.html', clinics=clinics)

@main_bp.route('/appointments/<clinic_id>')
@login_required
def appointments(clinic_id):
    """Agendamentos da empresa"""
    clinic = Clinic.query.filter_by(id=clinic_id, user_id=current_user.id).first_or_404()
    appointments = Appointment.query.filter_by(clinic_id=clinic_id)\
        .order_by(Appointment.scheduled_date.desc())\
        .limit(100).all()
    return render_template('appointments.html', clinic=clinic, appointments=appointments)

@main_bp.route('/conversations/<clinic_id>')
@login_required
def conversations(clinic_id):
    """Conversas da empresa"""
    clinic = Clinic.query.filter_by(id=clinic_id, user_id=current_user.id).first_or_404()
    conversations = Conversation.query.filter_by(clinic_id=clinic_id)\
        .order_by(Conversation.created_at.desc())\
        .limit(100).all()
    return render_template('conversations.html', clinic=clinic, conversations=conversations)

# API Routes
@api_bp.route('/clinics/<clinic_id>/appointments', methods=['GET'])
@login_required
def get_appointments(clinic_id):
    """API para obter agendamentos"""
    clinic = Clinic.query.filter_by(id=clinic_id, user_id=current_user.id).first_or_404()

    appointments = Appointment.query.filter_by(clinic_id=clinic_id)\
        .join(Service).join(Patient)\
        .order_by(Appointment.scheduled_date.desc())\
        .limit(100).all()

    result = []
    for appt in appointments:
        result.append({
            'id': appt.id,
            'patient_name': appt.patient.name,
            'patient_phone': appt.patient.phone,
            'service': appt.service.name,
            'date': appt.scheduled_date.strftime('%d/%m/%Y'),
            'time': appt.scheduled_time.strftime('%H:%M'),
            'status': appt.status
        })

    return jsonify(result)

@api_bp.route('/clinics/<clinic_id>/availability', methods=['GET'])
@login_required
def get_availability(clinic_id):
    """API para verificar disponibilidade"""
    clinic = Clinic.query.filter_by(id=clinic_id, user_id=current_user.id).first_or_404()

    date_str = request.args.get('date')
    service_id = request.args.get('service_id')

    if not date_str or not service_id:
        return jsonify({'error': 'Date and service_id are required'}), 400

    from datetime import datetime
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    available_slots = AppointmentScheduler.check_availability(
        clinic_id=clinic_id,
        service_id=service_id,
        target_date=target_date
    )

    return jsonify({'available_slots': available_slots})

@api_bp.route('/clinics/<clinic_id>/appointments', methods=['POST'])
@login_required
def create_appointment(clinic_id):
    """API para criar agendamento"""
    clinic = Clinic.query.filter_by(id=clinic_id, user_id=current_user.id).first_or_404()

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    success, appointment, error = AppointmentScheduler.create_appointment(
        clinic_id=clinic_id,
        patient_id=data.get('patient_id'),
        service_id=data.get('service_id'),
        scheduled_date=datetime.fromisoformat(data.get('scheduled_date')).date(),
        scheduled_time=datetime.fromisoformat(data.get('scheduled_time')).time(),
        professional_id=data.get('professional_id'),
        notes=data.get('notes')
    )

    if success:
        return jsonify({
            'success': True,
            'appointment_id': appointment.id,
            'message': 'Appointment created successfully'
        })
    else:
        return jsonify({'error': error}), 400

@api_bp.route('/webhook/whatsapp', methods=['GET', 'POST'])
def whatsapp_webhook():
    """Webhook do WhatsApp"""
    if request.method == 'GET':
        # Verificação
        is_valid, response = WhatsAppWebhookHandler.verify_webhook(
            request.args.get('hub.verify_token'),
            request.args.get('hub.mode'),
            request.args.get('hub.challenge')
        )
        if is_valid:
            return response, 200
        else:
            return response, 403

    elif request.method == 'POST':
        # Processamento
        data = request.get_json()
        success = WhatsAppWebhookHandler.handle_webhook(data)
        return jsonify({'status': 'ok' if success else 'error'}), 200 if success else 500

# Auth routes (básico)
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        # Implementar login
        pass
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout - limpa sessão e cookies JWT"""
    from flask_login import logout_user
    resp = redirect(url_for('auth_bp.login'))
    logout_user()
    # remover cookies de token
    resp.set_cookie('access_token', '', expires=0)
    resp.set_cookie('refresh_token', '', expires=0)
    return resp

# Importar e registrar novos blueprints
from app.partner_dashboard import partner_bp
from app.sales_dashboard import sales_bp
# API blueprints implemented for auth and billing
from app.auth_api import auth_api_bp
from app.billing_api import billing_api_bp

# Blueprint de segurança
security_bp = Blueprint('security', __name__)

@security_bp.route('/health')
def security_health():
    """Endpoint de saúde da segurança"""
    from core.security.rate_limiting import rate_limiter
    from core.security.config import security_config

    return jsonify({
        "status": "healthy",
        "security": {
            "rate_limiting_enabled": True,
            "blocked_ips": len(rate_limiter.blocked_ips),
            "whitelisted_ips": len(rate_limiter.whitelist),
            "secret_manager": security_config.SECRETS_MANAGER_TYPE,
            "environment": security_config.ENVIRONMENT
        }
    })

@security_bp.route('/block-ip', methods=['POST'])
@secure_login_required
def block_ip():
    """Bloquear IP (apenas admin)"""
    from core.security.rate_limiting import rate_limiter

    data = request.get_json()
    ip = data.get('ip')
    reason = data.get('reason', 'Manual block')

    if not ip:
        return jsonify({"error": "IP address required"}), 400

    rate_limiter.block_ip(ip)
    return jsonify({"message": f"IP {ip} blocked", "reason": reason})

@security_bp.route('/unblock-ip', methods=['POST'])
@secure_login_required
def unblock_ip():
    """Desbloquear IP (apenas admin)"""
    from core.security.rate_limiting import rate_limiter

    data = request.get_json()
    ip = data.get('ip')

    if not ip:
        return jsonify({"error": "IP address required"}), 400

    rate_limiter.unblock_ip(ip)
    return jsonify({"message": f"IP {ip} unblocked"})

@security_bp.route('/security-metrics')
@secure_login_required
def security_metrics():
    """Métricas de segurança"""
    from core.security.rate_limiting import rate_limiter, ddos_protection

    return jsonify({
        "rate_limiting": {
            "blocked_ips": list(rate_limiter.blocked_ips),
            "whitelisted_ips": list(rate_limiter.whitelist),
            "active_requests": len(rate_limiter.requests)
        },
        "ddos_protection": {
            "threshold": ddos_protection.threshold,
            "current_counts": dict(ddos_protection.request_counts)
        }
    })

def register_blueprints(app):
    """Registrar todos os blueprints na aplicação"""
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(partner_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(security_bp, url_prefix='/security')
    # Registrar blueprints de API adicionais
    app.register_blueprint(auth_api_bp)
    app.register_blueprint(billing_api_bp)