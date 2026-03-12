from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.models import db, Partnership, PartnershipTransaction, Clinic, PartnershipAssignment
from app.partnership_system import PartnershipManager

partner_bp = Blueprint('partner', __name__, url_prefix='/partner')

@partner_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard do parceiro"""
    # Verificar se usuário é parceiro
    partner = Partnership.query.filter_by(user_id=current_user.id).first()
    if not partner:
        return render_template('error.html', message="Acesso não autorizado"), 403

    # Gerar dados do dashboard
    dashboard_data = PartnershipManager.generate_partner_portal(partner.id)

    return render_template('partner/dashboard.html',
                          partner=partner,
                          data=dashboard_data)

@partner_bp.route('/services', methods=['POST'])
@login_required
def record_service():
    """Registrar serviço prestado"""
    data = request.get_json()

    partner = Partnership.query.filter_by(user_id=current_user.id).first()
    if not partner:
        return jsonify({'error': 'Parceiro não encontrado'}), 404

    success, message = PartnershipManager.record_partner_service(
        clinic_id=data['clinic_id'],
        partner_id=partner.id,
        service_type=data['service_type'],
        description=data['description'],
        hours=data.get('hours', 0),
        value=data.get('value', 0),
        client_plan=data.get('client_plan')
    )

    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'error': message}), 400

@partner_bp.route('/clients')
@login_required
def get_clients():
    """Listar clientes do parceiro"""
    partner = Partnership.query.filter_by(user_id=current_user.id).first()

    assignments = PartnershipAssignment.query.filter_by(
        partner_id=partner.id,
        status='active'
    ).all()

    clients = []
    for assignment in assignments:
        clinic = Clinic.query.get(assignment.clinic_id)
        if clinic:
            subscription = clinic.subscription
            clients.append({
                'id': clinic.id,
                'name': clinic.name,
                'plan': subscription.plan if subscription else 'N/A',
                'assigned_date': assignment.assigned_at.strftime('%d/%m/%Y'),
                'service_needed': assignment.service_needed,
                'contact_email': clinic.email,
                'contact_phone': clinic.phone
            })

    return jsonify({'clients': clients})

@partner_bp.route('/commissions')
@login_required
def get_commissions():
    """Listar comissões do parceiro"""
    partner = Partnership.query.filter_by(user_id=current_user.id).first()

    transactions = PartnershipTransaction.query.filter_by(
        partner_id=partner.id
    ).order_by(PartnershipTransaction.service_date.desc()).all()

    commissions = []
    for t in transactions:
        clinic = Clinic.query.get(t.clinic_id)
        commissions.append({
            'date': t.service_date.strftime('%d/%m/%Y'),
            'clinic': clinic.name if clinic else 'N/A',
            'service': t.service_type,
            'value': float(t.service_value),
            'commission_rate': float(t.commission_rate),
            'commission_amount': float(t.commission_amount),
            'status': t.status,
            'payment_date': t.paid_at.strftime('%d/%m/%Y') if t.paid_at else None
        })

    return jsonify({'commissions': commissions})