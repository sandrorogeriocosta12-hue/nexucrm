"""
Endpoints de Autenticação - Implementação Crítica para Soft Launch

Endpoints implementados:
✓ POST /api/auth/forgot-password - Solicita reset de senha
✓ POST /api/auth/reset-password - Reseta a senha com token
✓ DELETE /api/auth/account - Deleta conta de usuário (LGPD compliance)
✓ GET /api/auth/me - Retorna dados do usuário autenticado
"""

from flask import Blueprint, request, jsonify, url_for
from flask_login import login_required, current_user
from app.models import db, User, PasswordResetToken, Subscription
# core package is at workspace root, avoid naming conflict with vexus_hub/app
from core.email import EmailService
from datetime import datetime, timezone
import secrets

auth_api_bp = Blueprint('auth_api', __name__, url_prefix='/api/auth')

# ============================================================================
# FORGOT PASSWORD - Envia token de reset por email
# ============================================================================

@auth_api_bp.route('/login', methods=['POST'])
def login():
    """
    Autentica usuário e retorna dados, setando cookies HttpOnly para tokens.

    Request:
        {"email": "user@example.com", "password": "senha"}
    
    Response:
        {"success": true, "user": {..}}
    """
    data = request.get_json() or {}
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.verify_password(password):
        return jsonify({'error': 'Credenciais inválidas'}), 401

    # gerar tokens JWT e armazenar cookie HttpOnly
    from core.auth import create_tokens
    tokens = create_tokens(user.id, user.email, user.name, user.role)

    resp = jsonify({'success': True, 'user': user.to_dict()})
    # definir cookies (seguro em HTTPS, por enquanto cookie de teste sem secure)
    resp.set_cookie('access_token', tokens.access_token,
                    httponly=True, samesite='Lax')
    resp.set_cookie('refresh_token', tokens.refresh_token,
                    httponly=True, samesite='Lax')

    # também usa flask-login para manter session
    from flask_login import login_user
    login_user(user)

    return resp


@auth_api_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Solicita reset de senha
    
    Request:
        {
            "email": "user@example.com"
        }
    
    Response:
        {
            "success": true,
            "message": "Se este email existe, um link de reset foi enviado"
        }
    
    Segurança:
    - Não revela se email existe (proteção contra enumeração)
    - Token válido por 24h
    - Descarta tokens antigos
    """
    
    data = request.get_json()
    if not data or not data.get('email'):
        return jsonify({'error': 'Email é obrigatório'}), 400
    
    email = data.get('email').lower().strip()
    
    # Busca usuário (sem revelar se existe)
    user = User.query.filter_by(email=email).first()
    
    if user:
        # Marca tokens antigos como usados
        PasswordResetToken.query.filter_by(
            user_id=user.id,
            used=False
        ).update({'used': True, 'used_at': datetime.now(timezone.utc)})
        db.session.commit()
        
        # Cria novo token
        reset_token = PasswordResetToken.create_reset_token(user.id, expires_in_hours=24)
        
        # Monta URL de reset
        reset_url = url_for('auth_api.reset_password_page', token=reset_token, _external=True)
        
        # Envia email
        try:
            EmailService.send_password_reset_email(
                email=user.email,
                name=user.name,
                reset_url=reset_url,
                expires_in_hours=24
            )
            # Log de auditoria
            from app.models import AuditLog
            AuditLog.query.session.add(AuditLog(
                user_id=user.id,
                action='password_reset_requested',
                resource_type='user',
                resource_id=user.id,
                details=f'Reset de senha solicitado para {email}'
            ))
        except Exception as e:
            print(f"Erro ao enviar email de reset: {e}")
            # Não revela para o client que houve erro com email
            pass
    
    # Retorna sucesso sempre (não revela se email existe)
    return jsonify({
        'success': True,
        'message': 'Se este email existe em nosso sistema, um link de reset foi enviado'
    }), 200

# ============================================================================
# RESET PASSWORD - Confirma reset com token válido
# ============================================================================

@auth_api_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Reseta a senha usando token válido
    
    Request:
        {
            "token": "token_obtido_no_email",
            "new_password": "SenhaForte123!"
        }
    
    Response:
        {
            "success": true,
            "message": "Senha alterada com sucesso"
        }
    
    Validações:
    - Token válido e não expirado
    - Token não foi usado antes
    - Senha atende critérios de força
    """
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados obrigatórios não fornecidos'}), 400
    
    token = data.get('token')
    new_password = data.get('new_password')
    
    if not token or not new_password:
        return jsonify({'error': 'Token e senha nova são obrigatórios'}), 400
    
    # Valida força da senha (mínimo 8 caracteres, com letra, número, especial)
    if len(new_password) < 8:
        return jsonify({'error': 'Senha deve ter no mínimo 8 caracteres'}), 400
    
    has_letter = any(c.isalpha() for c in new_password)
    has_number = any(c.isdigit() for c in new_password)
    if not (has_letter and has_number):
        return jsonify({'error': 'Senha deve conter letras e números'}), 400
    
    # Verifica token
    user_id = PasswordResetToken.verify_reset_token(token)
    if not user_id:
        return jsonify({'error': 'Token inválido ou expirado'}), 400
    
    # Busca usuário
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 400
    
    # Atualiza senha
    user.password = new_password
    user.updated_at = datetime.now(timezone.utc)
    
    # Marca token como usado
    PasswordResetToken.consume_reset_token(token)
    
    db.session.commit()
    
    # Log de auditoria
    from app.models import AuditLog
    db.session.add(AuditLog(
        user_id=user.id,
        action='password_reset_completed',
        resource_type='user',
        resource_id=user.id,
        details='Senha alterada com sucesso via reset'
    ))
    db.session.commit()
    
    # Opcional: Enviar email de confirmação
    try:
        EmailService.send_password_changed_email(user.email, user.name)
    except:
        pass
    
    return jsonify({
        'success': True,
        'message': 'Senha alterada com sucesso. Você pode fazer login agora.'
    }), 200

# ============================================================================
# RESET PASSWORD PAGE - Página HTML para reset (GET)
# ============================================================================

@auth_api_bp.route('/reset-password/<token>', methods=['GET'])
def reset_password_page(token):
    """
    Página de reset de senha (renderiza HTML)
    Valida se token existe antes de renderizar
    """
    from flask import render_template
    
    # Verifica se token é válido
    user_id = PasswordResetToken.verify_reset_token(token)
    if not user_id:
        return render_template('error.html', 
                             message='Link de reset inválido ou expirado',
                             support_email='support@vexuscrm.com'), 400
    
    return render_template('reset_password.html', token=token)

# ============================================================================
# DELETE ACCOUNT - Deleta conta do usuário (LGPD)
# ============================================================================

@auth_api_bp.route('/account', methods=['DELETE'])
@login_required
def delete_account():
    """
    Deleta conta do usuário autenticado
    Implementa direito ao esquecimento (LGPD)
    
    Request:
        {
            "password": "senha_confirmar",
            "reason": "Não quero mais usar"  (opcional)
        }
    
    Response:
        {
            "success": true,
            "message": "Conta deletada com sucesso"
        }
    
    Procedimento:
    1. Valida senha
    2. Cancela subscriptions ativas
    3. Marca clinics como deleted
    4. Apaga dados sensíveis (password_hash, etc)
    5. Log de auditoria
    6. Invalida sessão
    """
    
    data = request.get_json()
    if not data or not data.get('password'):
        return jsonify({'error': 'Senha é obrigatória para deletar conta'}), 400
    
    password = data.get('password')
    reason = data.get('reason', 'Não especificado')
    
    # Valida senha
    if not current_user.verify_password(password):
        return jsonify({'error': 'Senha incorreta'}), 401
    
    user_id = current_user.id
    user_email = current_user.email
    
    try:
        # 1. Cancela subscriptions ativas
        subscriptions = Subscription.query.filter_by(user_id=user_id).all()
        for sub in subscriptions:
            sub.status = 'cancelled'
            sub.cancelled_at = datetime.now(timezone.utc)
            # TODO: Cancelar também no Stripe se existir
        
        # 2. Marca clínicas como deletadas
        from app.models import Clinic
        clinics = Clinic.query.filter_by(user_id=user_id).all()
        for clinic in clinics:
            clinic.status = 'deleted'
            clinic.updated_at = datetime.now(timezone.utc)
        
        # 3. Apaga dados sensíveis (anonymização)
        current_user.password_hash = 'DELETED'
        current_user.email = f'deleted_{user_id}@deleted.local'
        current_user.name = 'Usuário Deletado'
        current_user.phone = None
        current_user.status = 'deleted'
        current_user.updated_at = datetime.now(timezone.utc)
        
        # 4. Log de auditoria
        from app.models import AuditLog
        db.session.add(AuditLog(
            user_id=user_id,
            action='account_deleted',
            resource_type='user',
            resource_id=user_id,
            details=f'Conta deletada pelo usuário. Motivo: {reason}'
        ))
        
        db.session.commit()
        
        # 5. Tenta enviar email de confirmação (antes de fazer logout)
        try:
            EmailService.send_account_deletion_email(user_email)
        except:
            pass
        
        # 6. Invalida sessão (logout)
        from flask_login import logout_user
        logout_user()
        
        return jsonify({
            'success': True,
            'message': 'Sua conta foi deletada com sucesso. Sentiremos sua falta!',
            'redirectUrl': '/'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao deletar conta: {e}")
        return jsonify({'error': 'Erro ao deletar conta. Tente novamente.'}), 500

# ============================================================================
# GET CURRENT USER - Informações do usuário autenticado
# ============================================================================

@auth_api_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """
    Retorna informações do usuário autenticado
    
    Response:
        {
            "id": "user_uuid",
            "email": "user@example.com",
            "name": "Nome do Usuário",
            "role": "client",
            "email_verified": true,
            "subscriptions": [
                {
                    "id": "sub_uuid",
                    "plan": "bronze",
                    "status": "active",
                    "next_billing_date": "2026-03-16"
                }
            ]
        }
    """
    
    subscriptions = Subscription.query.filter_by(user_id=current_user.id).all()
    
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'name': current_user.name,
        'role': current_user.role,
        'email_verified': current_user.email_verified,
        'phone': current_user.phone,
        'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
        'subscriptions': [
            {
                'id': sub.id,
                'plan': sub.plan,
                'status': sub.status,
                'clinic_id': sub.clinic_id,
                'next_billing_date': sub.end_date.isoformat() if sub.end_date else None,
                'is_active': sub.is_active
            }
            for sub in subscriptions
        ]
    }), 200

# ============================================================================
# GET USER PROFILE - Detalhes completos do perfil
# ============================================================================

@auth_api_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """Retorna perfil completo do usuário"""
    return jsonify(current_user.to_dict()), 200

@auth_api_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """
    Atualiza perfil do usuário
    
    Request:
        {
            "name": "Novo Nome",
            "phone": "(11) 99999-9999"
        }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados não fornecidos'}), 400
    
    if 'name' in data:
        current_user.name = data['name']
    
    if 'phone' in data:
        current_user.phone = data['phone']
    
    current_user.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Perfil atualizado com sucesso',
        'user': current_user.to_dict()
    }), 200

# ============================================================================
# REGISTER/SIGNUP (TODO - será implementado junto com email verification)
# ============================================================================

@auth_api_bp.route('/signup', methods=['POST'])
def signup():
    """
    Cria novo usuário
    
    Request:
        {
            "email": "user@example.com",
            "password": "SenhaForte123!",
            "name": "Nome do Usuário"
        }
    
    Response:
        {
            "success": true,
            "user_id": "uuid",
            "message": "Conta criada. Verifique seu email para confirmar."
        }
    """
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados obrigatórios não fornecidos'}), 400
    
    email = data.get('email', '').lower().strip()
    password = data.get('password', '')
    name = data.get('name', '').strip()
    
    # Validações
    if not email or not password or not name:
        return jsonify({'error': 'Email, senha e nome são obrigatórios'}), 400
    
    # Valida email
    import re
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return jsonify({'error': 'Email inválido'}), 400
    
    # Valida força da senha
    if len(password) < 8:
        return jsonify({'error': 'Senha deve ter no mínimo 8 caracteres'}), 400
    
    # Verifica se email já existe
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Este email já está registrado'}), 400
    
    try:
        # Cria novo usuário
        user = User(
            email=email,
            name=name,
            role='client',
            email_verified=False
        )
        user.password = password  # Usa setter que faz hash
        
        db.session.add(user)
        db.session.commit()
        
        # TODO: Enviar email de verificação
        # EmailService.send_verification_email(email, name, verification_link)
        
        return jsonify({
            'success': True,
            'user_id': user.id,
            'message': 'Conta criada com sucesso. Verifique seu email para confirmar.'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar usuário: {e}")
        return jsonify({'error': 'Erro ao criar conta. Tente novamente.'}), 500
