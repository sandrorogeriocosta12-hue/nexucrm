from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Clinic(db.Model):
    """Modelo para dados da clínica"""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    whatsapp_business_id = db.Column(db.String(100), unique=True)
    specialties = db.Column(db.Text)  # JSON string: ["Dermatologia", "Cardiologia"]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    services = db.relationship("Service", backref="clinic", lazy=True)
    appointments = db.relationship("Appointment", backref="clinic", lazy=True)


class Service(db.Model):
    """Serviços/procedimentos oferecidos pela clínica"""

    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey("clinic.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # Ex: "Consulta Dermatológica"
    duration = db.Column(db.Integer, default=30)  # Duração em minutos
    price = db.Column(db.Float)
    active = db.Column(db.Boolean, default=True)


class Patient(db.Model):
    """Pacientes"""

    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    appointments = db.relationship("Appointment", backref="patient", lazy=True)


class Appointment(db.Model):
    """Agendamentos"""

    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey("clinic.id"), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey("service.id"))

    # Dados do agendamento
    scheduled_date = db.Column(db.Date, nullable=False)
    scheduled_time = db.Column(db.Time, nullable=False)
    status = db.Column(
        db.String(20), default="agendado"
    )  # agendado, confirmado, cancelado, realizado
    notes = db.Column(db.Text)

    # Metadados
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relacionamento
    service = db.relationship("Service")


class Conversation(db.Model):
    """Registro de conversas para treinamento da IA"""

    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey("clinic.id"), nullable=False)
    patient_phone = db.Column(db.String(20))
    message = db.Column(db.Text)
    response = db.Column(db.Text)
    intent = db.Column(db.String(50))  # agendamento, cancelamento, duvida, etc.
    confidence = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def init_db(app):
    """Inicializa o banco de dados"""
    db.init_app(app)
    with app.app_context():
        db.create_all()

        # Adiciona dados de exemplo para teste
        if Clinic.query.count() == 0:
            clinic = Clinic(
                name="Clínica Vexus Demo",
                phone="+5511999999999",
                specialties='["Dermatologia", "Cardiologia", "Clínica Geral"]',
            )
            db.session.add(clinic)
            db.session.commit()

            # Serviços de exemplo
            services = [
                Service(
                    clinic_id=clinic.id,
                    name="Consulta de Rotina",
                    duration=30,
                    price=150.00,
                ),
                Service(
                    clinic_id=clinic.id,
                    name="Consulta Dermatológica",
                    duration=45,
                    price=200.00,
                ),
                Service(
                    clinic_id=clinic.id,
                    name="Exame de Sangue",
                    duration=15,
                    price=80.00,
                ),
            ]
            db.session.add_all(services)
            db.session.commit()
