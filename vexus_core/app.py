from flask import Flask, request, jsonify, render_template
import json
from config import Config
from database import init_db, db, Clinic, Conversation
from whatsapp_flow import WhatsAppFlowManager

app = Flask(__name__)
app.config.from_object(Config)

# Inicializa banco de dados
init_db(app)

# Dicionário para gerenciar fluxos por clínica
flow_managers = {}


def get_flow_manager(clinic_id):
    """Obtém ou cria um gerenciador de fluxo para uma clínica"""
    if clinic_id not in flow_managers:
        flow_managers[clinic_id] = WhatsAppFlowManager(db.session, clinic_id)
    return flow_managers[clinic_id]


@app.route("/")
def index():
    """Página inicial do painel administrativo"""
    return render_template("index.html")


@app.route("/admin")
def admin():
    """Painel administrativo"""
    clinics = Clinic.query.all()
    return render_template("admin.html", clinics=clinics)


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    """Webhook para receber mensagens do WhatsApp"""
    if request.method == "GET":
        # Verificação do webhook (requerido pelo Meta)
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        # TOKEN deve ser definido nas variáveis de ambiente
        verify_token = app.config.get("WHATSAPP_VERIFY_TOKEN", "vexus2024")

        if mode == "subscribe" and token == verify_token:
            return challenge, 200
        else:
            return "Verificação falhou", 403

    elif request.method == "POST":
        # Processa mensagem recebida
        data = request.get_json()

        try:
            # Log da mensagem recebida
            print(f"Mensagem recebida: {json.dumps(data, indent=2)}")

            # Verifica se é uma mensagem válida do WhatsApp
            if "entry" in data and data["entry"]:
                entry = data["entry"][0]
                if "changes" in entry and entry["changes"]:
                    change = entry["changes"][0]
                    if "value" in change:
                        value = change["value"]

                        # Verifica se há mensagens
                        if "messages" in value and value["messages"]:
                            message = value["messages"][0]

                            # Obtém dados da mensagem
                            from_number = message["from"]
                            message_text = (
                                message["text"]["body"] if "text" in message else ""
                            )

                            # ID da clínica (assumindo que o número do WhatsApp está associado a uma clínica)
                            # Em produção, você precisaria mapear o número para a clínica
                            clinic = (
                                Clinic.query.first()
                            )  # Para MVP, pega a primeira clínica

                            if clinic:
                                flow_manager = get_flow_manager(clinic.id)
                                response = flow_manager.process_message(
                                    from_number, message_text
                                )

                                # Aqui você enviaria a resposta via API do WhatsApp
                                # Por enquanto, apenas loga
                                print(f"Resposta gerada: {response}")

                                # Salva conversa no banco de dados
                                conversation = Conversation(
                                    clinic_id=clinic.id,
                                    patient_phone=from_number,
                                    message=message_text,
                                    response=response,
                                    intent="whatsapp_message",
                                )
                                db.session.add(conversation)
                                db.session.commit()

                                return jsonify({"status": "success"}), 200

        except Exception as e:
            print(f"Erro ao processar webhook: {str(e)}")
            return jsonify({"error": str(e)}), 500

        return jsonify({"status": "ignored"}), 200


@app.route("/api/send_message", methods=["POST"])
def send_message():
    """API para enviar mensagens via WhatsApp (para testes)"""
    data = request.get_json()

    phone = data.get("phone")
    message = data.get("message")
    clinic_id = data.get("clinic_id", 1)

    if not phone or not message:
        return jsonify({"error": "Phone and message are required"}), 400

    flow_manager = get_flow_manager(clinic_id)
    response = flow_manager.process_message(phone, message)

    return jsonify({"response": response, "status": "success"})


@app.route("/api/appointments", methods=["GET"])
def get_appointments():
    """API para obter agendamentos"""
    from database import Appointment, Service, Patient

    appointments = Appointment.query.join(Service).join(Patient).all()

    result = []
    for appt in appointments:
        result.append(
            {
                "id": appt.id,
                "patient_name": appt.patient.name,
                "patient_phone": appt.patient.phone,
                "service": appt.service.name,
                "date": appt.scheduled_date.strftime("%d/%m/%Y"),
                "time": appt.scheduled_time.strftime("%H:%M"),
                "status": appt.status,
            }
        )

    return jsonify(result)


@app.route("/api/conversations", methods=["GET"])
def get_conversations():
    """API para obter histórico de conversas"""
    clinic_id = request.args.get("clinic_id", 1)

    conversations = (
        Conversation.query.filter_by(clinic_id=clinic_id)
        .order_by(Conversation.created_at.desc())
        .limit(50)
        .all()
    )

    result = []
    for conv in conversations:
        result.append(
            {
                "id": conv.id,
                "patient_phone": conv.patient_phone,
                "message": conv.message,
                "response": conv.response,
                "intent": conv.intent,
                "timestamp": conv.created_at.strftime("%d/%m/%Y %H:%M"),
            }
        )

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
