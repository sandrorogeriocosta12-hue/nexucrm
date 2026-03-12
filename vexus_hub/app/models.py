from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import json

from app import db

def generate_uuid():
    return str(uuid.uuid4())

class User(UserMixin, db.Model):
    """Usuários do sistema (clientes e administradores)"""
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='client')  # admin, client, manager
    status = db.Column(db.String(20), default='active')  # active, suspended, cancelled
    email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relacionamentos
    clinics = db.relationship('Clinic', backref='owner', lazy='dynamic', foreign_keys='Clinic.user_id')
    subscriptions = db.relationship('Subscription', backref='user', lazy='dynamic')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Clinic(db.Model):
    """Empresas cadastradas no sistema"""
    __tablename__ = 'clinics'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    business_name = db.Column(db.String(200))
    tax_id = db.Column(db.String(20))  # CNPJ
    phone = db.Column(db.String(20), nullable=False)
    whatsapp_phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    website = db.Column(db.String(200))

    # Endereço
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(10))
    country = db.Column(db.String(50), default='Brasil')

    # Configurações
    timezone = db.Column(db.String(50), default='America/Sao_Paulo')
    working_hours = db.Column(db.Text, default='{}')  # JSON com horários
    specialties = db.Column(db.Text, default='[]')  # JSON com especialidades
    languages = db.Column(db.Text, default='["pt-BR"]')  # JSON com idiomas

    # Integrações
    whatsapp_business_id = db.Column(db.String(100))
    whatsapp_access_token = db.Column(db.Text)
    google_calendar_id = db.Column(db.String(200))
    google_credentials = db.Column(db.Text)

    # Status
    status = db.Column(db.String(20), default='pending')  # pending, active, suspended
    onboarding_step = db.Column(db.Integer, default=1)
    trial_ends_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Parceiros atribuídos
    marketing_partner_id = db.Column(db.String(36), db.ForeignKey('partnerships.id'))
    accounting_partner_id = db.Column(db.String(36), db.ForeignKey('partnerships.id'))

    # Onboarding
    onboarding_started_at = db.Column(db.DateTime)
    onboarding_completed_at = db.Column(db.DateTime)
    onboarding_plan = db.Column(db.String(20))  # bronze, silver, gold
    onboarding_manager_id = db.Column(db.String(36), db.ForeignKey('users.id'))

    # Relacionamentos
    services = db.relationship('Service', backref='clinic', lazy='dynamic', cascade='all, delete-orphan')
    professionals = db.relationship('Professional', backref='clinic', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='clinic', lazy='dynamic')
    conversations = db.relationship('Conversation', backref='clinic', lazy='dynamic')
    subscription = db.relationship('Subscription', backref='clinic', uselist=False)

    def get_working_hours(self):
        import json
        try:
            return json.loads(self.working_hours) if self.working_hours else {}
        except:
            return {}

    def set_working_hours(self, hours_dict):
        import json
        self.working_hours = json.dumps(hours_dict)

    def get_specialties(self):
        import json
        try:
            return json.loads(self.specialties) if self.specialties else []
        except:
            return []

    def set_specialties(self, specialties_list):
        import json
        self.specialties = json.dumps(specialties_list)

class Professional(db.Model):
    """Profissionais da empresa (atendentes, técnicos, etc.)"""
    __tablename__ = 'professionals'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    clinic_id = db.Column(db.String(36), db.ForeignKey('clinics.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    specialty = db.Column(db.String(100))
    registration_number = db.Column(db.String(50))  # CRM, CRO, etc.
    color = db.Column(db.String(7), default='#3B82F6')  # Cor no calendário
    working_hours = db.Column(db.Text, default='{}')  # JSON com horários específicos
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relacionamentos
    appointments = db.relationship('Appointment', backref='professional', lazy='dynamic')

class Service(db.Model):
    """Serviços/procedimentos oferecidos"""
    __tablename__ = 'services'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    clinic_id = db.Column(db.String(36), db.ForeignKey('clinics.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer, default=30)  # minutos
    price = db.Column(db.Numeric(10, 2))
    color = db.Column(db.String(7), default='#10B981')
    active = db.Column(db.Boolean, default=True)
    requires_professional = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relacionamentos
    appointments = db.relationship('Appointment', backref='service', lazy='dynamic')

class Patient(db.Model):
    """Clientes cadastrados"""
    __tablename__ = 'patients'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    clinic_id = db.Column(db.String(36), db.ForeignKey('clinics.id'), nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False, index=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    birth_date = db.Column(db.Date)
    gender = db.Column(db.String(1))  # M, F, O
    notes = db.Column(db.Text)
    allergies = db.Column(db.Text)
    medications = db.Column(db.Text)

    # Dados para marketing
    opt_in_marketing = db.Column(db.Boolean, default=True)
    source = db.Column(db.String(50))  # how they found the clinic

    # Métricas
    first_appointment_date = db.Column(db.DateTime)
    last_appointment_date = db.Column(db.DateTime)
    total_appointments = db.Column(db.Integer, default=0)
    total_spent = db.Column(db.Numeric(10, 2), default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relacionamentos
    appointments = db.relationship('Appointment', backref='patient', lazy='dynamic')
    conversations = db.relationship('Conversation', backref='patient', lazy='dynamic')

    # Índice composto
    __table_args__ = (
        db.UniqueConstraint('clinic_id', 'phone', name='unique_patient_phone_per_clinic'),
    )

class Appointment(db.Model):
    """Agendamentos"""
    __tablename__ = 'appointments'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    clinic_id = db.Column(db.String(36), db.ForeignKey('clinics.id'), nullable=False, index=True)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), nullable=False, index=True)
    professional_id = db.Column(db.String(36), db.ForeignKey('professionals.id'), index=True)
    service_id = db.Column(db.String(36), db.ForeignKey('services.id'), nullable=False)

    # Dados do agendamento
    scheduled_date = db.Column(db.Date, nullable=False, index=True)
    scheduled_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time)
    status = db.Column(db.String(20), default='scheduled',
                       index=True)  # scheduled, confirmed, cancelled, completed, no_show
    appointment_type = db.Column(db.String(20), default='service')  # service, consultation, repair, etc.

    # Notificações
    reminder_sent = db.Column(db.Boolean, default=False)
    reminder_sent_at = db.Column(db.DateTime)
    confirmation_sent = db.Column(db.Boolean, default=False)
    confirmation_sent_at = db.Column(db.DateTime)

    # Pagamento
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, partial, refunded
    payment_method = db.Column(db.String(50))
    amount = db.Column(db.Numeric(10, 2))
    paid_amount = db.Column(db.Numeric(10, 2), default=0)

    # Metadados
    notes = db.Column(db.Text)
    cancellation_reason = db.Column(db.Text)
    source = db.Column(db.String(50), default='whatsapp')  # whatsapp, website, phone, etc.

    # Sistema de versões para auditoria
    version = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    created_by = db.Column(db.String(36))

    # Índices compostos
    __table_args__ = (
        db.Index('idx_clinic_date_status', 'clinic_id', 'scheduled_date', 'status'),
        db.Index('idx_patient_date', 'patient_id', 'scheduled_date'),
    )

    @property
    def scheduled_datetime(self):
        from datetime import datetime
        return datetime.combine(self.scheduled_date, self.scheduled_time)

    @property
    def end_datetime(self):
        from datetime import datetime, timedelta
        if self.end_time:
            return datetime.combine(self.scheduled_date, self.end_time)
        elif self.service and self.service.duration:
            return self.scheduled_datetime + timedelta(minutes=self.service.duration)
        else:
            return self.scheduled_datetime + timedelta(minutes=30)

class Conversation(db.Model):
    """Histórico de conversas"""
    __tablename__ = 'conversations'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    clinic_id = db.Column(db.String(36), db.ForeignKey('clinics.id'), nullable=False, index=True)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), index=True)

    # Dados da mensagem
    platform = db.Column(db.String(20), default='whatsapp')  # whatsapp, facebook, instagram, web
    message_id = db.Column(db.String(100))  # ID da mensagem na plataforma
    direction = db.Column(db.String(10), default='inbound')  # inbound, outbound
    message_type = db.Column(db.String(20), default='text')  # text, image, audio, document, etc.

    # Conteúdo
    content = db.Column(db.Text)
    media_url = db.Column(db.String(500))

    # Processamento de IA
    intent = db.Column(db.String(50))  # booking, cancellation, information, etc.
    confidence = db.Column(db.Float)
    processed_by_ai = db.Column(db.Boolean, default=False)
    ai_response = db.Column(db.Text)

    # Status
    status = db.Column(db.String(20), default='received')  # received, processed, failed
    error_message = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Índice composto
    __table_args__ = (
        db.Index('idx_clinic_patient_date', 'clinic_id', 'patient_id', 'created_at'),
    )

class Subscription(db.Model):
    """Assinaturas dos clientes"""
    __tablename__ = 'subscriptions'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    clinic_id = db.Column(db.String(36), db.ForeignKey('clinics.id'), unique=True, index=True)

    # Detalhes do plano
    plan = db.Column(db.String(20), default='bronze')  # bronze, silver, gold, custom
    status = db.Column(db.String(20), default='active')  # active, past_due, cancelled, expired
    billing_cycle = db.Column(db.String(10), default='monthly')  # monthly, quarterly, yearly

    # Preços
    monthly_price = db.Column(db.Numeric(10, 2), nullable=False)
    setup_fee = db.Column(db.Numeric(10, 2), default=0)
    discount = db.Column(db.Numeric(10, 2), default=0)

    # Período
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    trial_end_date = db.Column(db.Date)
    cancelled_at = db.Column(db.DateTime)

    # Pagamento
    payment_method = db.Column(db.String(50))
    payment_gateway = db.Column(db.String(50))  # stripe, pagarme, etc.
    gateway_subscription_id = db.Column(db.String(100))
    gateway_customer_id = db.Column(db.String(100))

    # Uso
    whatsapp_messages_used = db.Column(db.Integer, default=0)
    whatsapp_messages_limit = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    @property
    def is_active(self):
        from datetime import date
        if self.status == 'cancelled':
            return False
        if self.end_date and self.end_date < date.today():
            return False
        return True

class PasswordResetToken(db.Model):
    """Tokens para reset de senha"""
    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    token = db.Column(db.String(256), unique=True, nullable=False, index=True)
    used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @staticmethod
    def create_reset_token(user_id, expires_in_hours=24):
        """Cria um novo token de reset"""
        import secrets
        from datetime import timedelta
        
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        
        reset_token = PasswordResetToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        db.session.add(reset_token)
        db.session.commit()
        return token

    @staticmethod
    def verify_reset_token(token):
        """Verifica se o token é válido e retorna o user_id"""
        reset_token = PasswordResetToken.query.filter_by(
            token=token,
            used=False
        ).first()
        
        if not reset_token:
            return None
        
        if reset_token.expires_at < datetime.now(timezone.utc):
            return None
        
        return reset_token.user_id

    @staticmethod
    def consume_reset_token(token):
        """Marca o token como usado"""
        reset_token = PasswordResetToken.query.filter_by(token=token).first()
        if reset_token:
            reset_token.used = True
            reset_token.used_at = datetime.now(timezone.utc)
            db.session.commit()

class Notification(db.Model):
    """Sistema de notificações"""
    __tablename__ = 'notifications'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), index=True)
    clinic_id = db.Column(db.String(36), db.ForeignKey('clinics.id'), index=True)

    # Conteúdo
    type = db.Column(db.String(50))  # appointment_reminder, payment_due, new_message, etc.
    title = db.Column(db.String(200))
    message = db.Column(db.Text)
    priority = db.Column(db.String(10), default='medium')  # low, medium, high, urgent

    # Ações
    action_url = db.Column(db.String(500))
    action_text = db.Column(db.String(50))

    # Status
    status = db.Column(db.String(20), default='unread')  # unread, read, dismissed
    sent_via = db.Column(db.String(50))  # email, whatsapp, push, in_app
    sent_at = db.Column(db.DateTime)
    read_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

class AuditLog(db.Model):
    """Log de auditoria para compliance"""
    __tablename__ = 'audit_logs'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)

    # Quem
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), index=True)
    clinic_id = db.Column(db.String(36), db.ForeignKey('clinics.id'), index=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)

    # O quê
    action = db.Column(db.String(50), nullable=False)  # create, update, delete, login, etc.
    resource_type = db.Column(db.String(50))  # appointment, patient, etc.
    resource_id = db.Column(db.String(36))

    # Detalhes
    details = db.Column(db.Text)  # JSON com dados antes/depois
    changes = db.Column(db.Text)  # JSON com alterações

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

# ===== NOVOS MODELOS PARA SISTEMA DE PARCERIAS E VENDAS =====

class Partnership(db.Model):
    """Parceiros do sistema"""
    __tablename__ = 'partnerships'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)

    # Informações básicas
    partner_type = db.Column(db.String(50), nullable=False)  # marketing, accounting, development, sales
    company_name = db.Column(db.String(200), nullable=False)
    tax_id = db.Column(db.String(20))  # CPF/CNPJ

    # Especializações e habilidades
    skills = db.Column(db.Text)  # JSON array
    contact_info = db.Column(db.Text)  # JSON com emails, telefones, etc.
    pricing_model = db.Column(db.Text)  # JSON com modelo de preços

    # Capacidade e carga
    min_clients = db.Column(db.Integer, default=1)
    max_clients = db.Column(db.Integer, default=10)
    current_clients = db.Column(db.Integer, default=0)
    total_clients = db.Column(db.Integer, default=0)

    # Status e aprovação
    status = db.Column(db.String(20), default='pending')  # pending, approved, active, suspended
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.String(36))
    contract_details = db.Column(db.Text)  # JSON com detalhes do contrato

    # Avaliação e métricas
    rating = db.Column(db.Float, default=5.0)
    total_reviews = db.Column(db.Integer, default=0)
    total_commission = db.Column(db.Numeric(10, 2), default=0)
    completed_projects = db.Column(db.Integer, default=0)
    total_projects = db.Column(db.Integer, default=0)

    # Método de pagamento
    payment_method = db.Column(db.Text)  # JSON com dados de pagamento
    accumulated_commissions = db.Column(db.Text, default='{}')  # JSON com comissões acumuladas

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relacionamentos
    transactions = db.relationship('PartnershipTransaction', backref='partner', lazy='dynamic')
    assignments = db.relationship('PartnershipAssignment', backref='partner', lazy='dynamic')

class PartnershipTransaction(db.Model):
    """Transações de comissões para parceiros"""
    __tablename__ = 'partnership_transactions'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    clinic_id = db.Column(db.String(36), db.ForeignKey('clinics.id'), nullable=False, index=True)
    partner_id = db.Column(db.String(36), db.ForeignKey('partnerships.id'), nullable=False, index=True)

    # Detalhes do serviço
    service_type = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    hours = db.Column(db.Numeric(5, 2), default=0)
    service_value = db.Column(db.Numeric(10, 2), nullable=False)

    # Comissão
    commission_rate = db.Column(db.Numeric(5, 4), nullable=False)  # 0.15 = 15%
    commission_amount = db.Column(db.Numeric(10, 2), nullable=False)

    # Status
    status = db.Column(db.String(20), default='pending')  # pending, approved, paid, cancelled
    service_date = db.Column(db.DateTime, nullable=False, index=True)
    paid_at = db.Column(db.DateTime)
    payment_id = db.Column(db.String(100))  # ID do pagamento no gateway

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class PartnershipAssignment(db.Model):
    """Atribuição de parceiro a clínica"""
    __tablename__ = 'partnership_assignments'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    clinic_id = db.Column(db.String(36), db.ForeignKey('clinics.id'), nullable=False, index=True)
    partner_id = db.Column(db.String(36), db.ForeignKey('partnerships.id'), nullable=False, index=True)
    partner_type = db.Column(db.String(50), nullable=False)

    service_needed = db.Column(db.String(200))
    budget = db.Column(db.Numeric(10, 2))
    requirements = db.Column(db.Text)  # JSON com requisitos específicos

    status = db.Column(db.String(20), default='assigned')  # assigned, active, completed, cancelled
    assigned_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    rating = db.Column(db.Float)  # Avaliação da clínica (1-5)
    feedback = db.Column(db.Text)

class Lead(db.Model):
    """Leads de vendas"""
    __tablename__ = 'leads'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)

    # Informações básicas
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False, index=True)
    company = db.Column(db.String(200))

    # Origem e qualificação
    source = db.Column(db.String(50), nullable=False)  # website, linkedin, referral, cold_call, event, partner
    landing_page = db.Column(db.String(500))
    utm_params = db.Column(db.Text)  # JSON com parâmetros UTM

    # Status e qualificação
    status = db.Column(db.String(20), default='new')  # new, contacted, qualified, proposal_sent, negotiation, closed_won, closed_lost, nurturing
    score = db.Column(db.Integer, default=0)  # Pontuação de qualificação (0-100)

    # Atribuição
    assigned_to = db.Column(db.String(36), db.ForeignKey('users.id'), index=True)
    assigned_at = db.Column(db.DateTime)
    qualifier_id = db.Column(db.String(36), db.ForeignKey('users.id'))

    # Qualificação
    qualified_at = db.Column(db.DateTime)
    qualification_data = db.Column(db.Text)  # JSON com dados de qualificação

    # Conversão
    converted_to_client = db.Column(db.Boolean, default=False)
    client_id = db.Column(db.String(36), db.ForeignKey('users.id'))

    # Último contato
    last_contact = db.Column(db.DateTime)
    contact_count = db.Column(db.Integer, default=0)

    # Notas e follow-up
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relacionamentos
    activities = db.relationship('Activity', backref='lead', lazy='dynamic')
    deals = db.relationship('Deal', backref='lead', lazy='dynamic')
    proposals = db.relationship('Proposal', backref='lead', lazy='dynamic')
    demo_events = db.relationship('DemoEvent', backref='lead', lazy='dynamic')

class Deal(db.Model):
    """Negócios/oportunidades"""
    __tablename__ = 'deals'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    lead_id = db.Column(db.String(36), db.ForeignKey('leads.id'), nullable=False, index=True)

    # Responsável e proprietário
    owner_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)

    # Detalhes do negócio
    value = db.Column(db.Numeric(10, 2), nullable=False)
    plan = db.Column(db.String(20))  # bronze, silver, gold
    stage = db.Column(db.String(20), default='discovery')  # discovery, demo, proposal, negotiation, closed_won, closed_lost
    probability = db.Column(db.Numeric(5, 4), default=0.1)  # 0.1 = 10%

    # Datas importantes
    expected_close_date = db.Column(db.Date)
    last_stage_change = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    closed_at = db.Column(db.DateTime)
    closed_value = db.Column(db.Numeric(10, 2))

    # Motivos
    win_reason = db.Column(db.Text)
    lost_reason = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

class Activity(db.Model):
    """Atividades de vendas e follow-up"""
    __tablename__ = 'activities'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    lead_id = db.Column(db.String(36), db.ForeignKey('leads.id'), nullable=False, index=True)

    # Tipo e detalhes
    type = db.Column(db.String(50), nullable=False)  # lead_captured, lead_qualified, demo_scheduled, proposal_created, deal_won, deal_lost, etc.
    description = db.Column(db.Text)
    activity_metadata = db.Column(db.Text)  # JSON com dados adicionais

    # Quem executou
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), index=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

class Proposal(db.Model):
    """Propostas comerciais"""
    __tablename__ = 'proposals'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    lead_id = db.Column(db.String(36), db.ForeignKey('leads.id'), nullable=False, index=True)

    # Detalhes da proposta
    plan = db.Column(db.String(20), nullable=False)
    monthly_price = db.Column(db.Numeric(10, 2), nullable=False)
    setup_fee = db.Column(db.Numeric(10, 2), default=0)
    contract_duration = db.Column(db.Integer, default=12)  # meses

    customizations = db.Column(db.Text)  # JSON com customizações
    special_terms = db.Column(db.Text)

    # PDF e status
    pdf_url = db.Column(db.String(500))
    status = db.Column(db.String(20), default='draft')  # draft, sent, accepted, rejected, expired

    # Datas importantes
    sent_at = db.Column(db.DateTime)
    accepted_at = db.Column(db.DateTime)
    rejected_at = db.Column(db.DateTime)
    valid_until = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class DemoEvent(db.Model):
    """Eventos de demonstração"""
    __tablename__ = 'demo_events'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    lead_id = db.Column(db.String(36), db.ForeignKey('leads.id'), nullable=False, index=True)

    # Agendamento
    scheduled_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    scheduled_date = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, default=60)  # minutos
    platform = db.Column(db.String(50), default='google_meet')
    meeting_link = db.Column(db.String(500))
    agenda = db.Column(db.Text)

    # Status
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled, no_show
    completed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    recording_url = db.Column(db.String(500))

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class OnboardingTask(db.Model):
    """Tarefas de onboarding"""
    __tablename__ = 'onboarding_tasks'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    clinic_id = db.Column(db.String(36), db.ForeignKey('clinics.id'), nullable=False, index=True)

    # Detalhes da tarefa
    type = db.Column(db.String(50), nullable=False)  # form, video, task, integration, approval, training
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.String(10), default='medium')  # low, medium, high

    # Atribuição
    assigned_to = db.Column(db.String(36), db.ForeignKey('users.id'), index=True)

    # Status
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    completed_by = db.Column(db.String(36), db.ForeignKey('users.id'))

    # Datas
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class OnboardingStep(db.Model):
    """Passos do processo de onboarding"""
    __tablename__ = 'onboarding_steps'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    clinic_id = db.Column(db.String(36), db.ForeignKey('clinics.id'), nullable=False, index=True)

    # Ordem e tipo
    order = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # form, video, task, integration, approval, training
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

    # Configuração
    config = db.Column(db.Text)  # JSON com configurações específicas

    # Requisitos
    required = db.Column(db.Boolean, default=True)
    estimated_time = db.Column(db.Integer, default=30)  # minutos

    # Status
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, skipped
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    completed_by = db.Column(db.String(36), db.ForeignKey('users.id'))
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class PartnerPayment(db.Model):
    """Pagamentos para parceiros"""
    __tablename__ = 'partner_payments'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    partner_id = db.Column(db.String(36), db.ForeignKey('partnerships.id'), nullable=False, index=True)

    # Detalhes do pagamento
    payment_method = db.Column(db.String(50), nullable=False)  # pix, bank_transfer, paypal
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)

    # Status
    status = db.Column(db.String(20), default='pending')  # pending, processed, failed, cancelled
    reference_id = db.Column(db.String(100))  # ID no gateway de pagamento
    transaction_ids = db.Column(db.Text)  # JSON com IDs das transações incluídas

    # Datas
    processed_at = db.Column(db.DateTime)
    paid_at = db.Column(db.DateTime)
    failed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class EmailTemplate(db.Model):
    """Templates de email para automação"""
    __tablename__ = 'email_templates'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)

    # Identificação
    name = db.Column(db.String(100), nullable=False)
    sequence_name = db.Column(db.String(50), nullable=False, index=True)
    step_order = db.Column(db.Integer, nullable=False)

    # Agendamento
    delay_days = db.Column(db.Integer, default=0)
    delay_hours = db.Column(db.Integer, default=0)

    # Conteúdo
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    conditions = db.Column(db.Text)  # JSON com condições para envio

    # Status
    active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

class EmailCampaign(db.Model):
    """Campanhas de email automatizadas"""
    __tablename__ = 'email_campaigns'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    lead_id = db.Column(db.String(36), db.ForeignKey('leads.id'), nullable=False, index=True)

    # Configuração
    sequence_name = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, paused, completed, cancelled
    current_step = db.Column(db.Integer, default=0)
    total_steps = db.Column(db.Integer, nullable=False)

    # Progresso
    last_email_sent = db.Column(db.DateTime)
    next_email_scheduled = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

# ===== PHASE 3: MARKETING AUTOMATION & ANALYTICS MODELS =====

class MarketingCampaign(db.Model):
    """Campanhas de marketing automatizadas"""
    __tablename__ = 'marketing_campaigns'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    clinic_id = db.Column(db.String(36), db.ForeignKey('clinics.id'), nullable=False, index=True)

    # Configuração da campanha
    name = db.Column(db.String(100), nullable=False)
    segment = db.Column(db.String(50), nullable=False)  # MarketingSegment enum
    channels = db.Column(db.Text, nullable=False)  # JSON array
    message_templates = db.Column(db.Text, nullable=False)  # JSON object
    schedule = db.Column(db.Text)  # JSON object
    filters = db.Column(db.Text)  # JSON object

    # Status e progresso
    status = db.Column(db.String(20), default='draft')  # draft, scheduled, running, completed, paused
    schedule_type = db.Column(db.String(20), default='one_time')  # one_time, recurring
    cron_expression = db.Column(db.String(100))  # Para campanhas recorrentes
    next_scheduled_run = db.Column(db.DateTime)

    # Métricas
    total_recipients = db.Column(db.Integer, default=0)
    estimated_reach = db.Column(db.Integer, default=0)
    cost = db.Column(db.Numeric(10, 2), default=0)

    # Datas
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    executed_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

class MarketingMessage(db.Model):
    """Mensagens enviadas em campanhas de marketing"""
    __tablename__ = 'marketing_messages'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    clinic_id = db.Column(db.String(36), db.ForeignKey('clinics.id'), nullable=False, index=True)
    campaign_id = db.Column(db.String(36), db.ForeignKey('marketing_campaigns.id'), nullable=False, index=True)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), nullable=False, index=True)

    # Conteúdo
    channel = db.Column(db.String(20), nullable=False)  # whatsapp, email, sms
    content = db.Column(db.Text, nullable=False)

    # Status
    status = db.Column(db.String(20), default='sent')  # sent, delivered, read, failed
    sent_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    delivered_at = db.Column(db.DateTime)
    read_at = db.Column(db.DateTime)
    failed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)

    # Métricas
    cost = db.Column(db.Numeric(5, 2), default=0)

class ContentPost(db.Model):
    """Posts de conteúdo para redes sociais"""
    __tablename__ = 'content_posts'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    clinic_id = db.Column(db.String(36), db.ForeignKey('clinics.id'), nullable=False, index=True)

    # Conteúdo
    platform = db.Column(db.String(20), nullable=False)  # instagram, facebook, linkedin
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    caption = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500))
    hashtags = db.Column(db.Text)

    # Agendamento
    scheduled_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, published, failed

    # Publicação
    published_at = db.Column(db.DateTime)
    platform_post_id = db.Column(db.String(100))  # ID do post na plataforma
    metrics = db.Column(db.Text)  # JSON com métricas

    # Erro
    error_message = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class SocialMediaAccount(db.Model):
    """Contas conectadas de redes sociais"""
    __tablename__ = 'social_media_accounts'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    clinic_id = db.Column(db.String(36), db.ForeignKey('clinics.id'), nullable=False, index=True)

    # Conta
    platform = db.Column(db.String(20), nullable=False)  # instagram, facebook, linkedin
    username = db.Column(db.String(100))
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    credentials = db.Column(db.Text, nullable=False)  # JSON com credenciais

    # Status
    status = db.Column(db.String(20), default='disconnected')  # connected, disconnected, error
    last_sync = db.Column(db.DateTime)
    error_message = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

class SystemMetric(db.Model):
    """Métricas de sistema para monitoramento"""
    __tablename__ = 'system_metrics'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # CPU
    cpu_percent = db.Column(db.Numeric(5, 2))

    # Memória
    memory_total = db.Column(db.BigInteger)
    memory_available = db.Column(db.BigInteger)
    memory_percent = db.Column(db.Numeric(5, 2))
    memory_used = db.Column(db.BigInteger)

    # Disco
    disk_total = db.Column(db.BigInteger)
    disk_used = db.Column(db.BigInteger)
    disk_percent = db.Column(db.Numeric(5, 2))
    disk_free = db.Column(db.BigInteger)

    # Rede
    network_sent = db.Column(db.BigInteger)
    network_recv = db.Column(db.BigInteger)

    # Processo
    process_memory = db.Column(db.Numeric(5, 2))
    process_cpu = db.Column(db.Numeric(5, 2))

class PerformanceLog(db.Model):
    """Logs de performance de endpoints"""
    __tablename__ = 'performance_logs'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    endpoint = db.Column(db.String(200), nullable=False, index=True)
    method = db.Column(db.String(10), nullable=False)
    duration_ms = db.Column(db.Numeric(10, 2), nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

class CacheHit(db.Model):
    """Estatísticas de cache"""
    __tablename__ = 'cache_hits'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    cache_key = db.Column(db.String(200), nullable=False, index=True)
    hits = db.Column(db.Integer, default=0)
    misses = db.Column(db.Integer, default=0)
    hit_rate = db.Column(db.Numeric(5, 2))
    avg_duration_ms = db.Column(db.Numeric(10, 2))
    recorded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)