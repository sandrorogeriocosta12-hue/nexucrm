import requests
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from flask import current_app
from app.models import db, Clinic, Patient, Appointment, Conversation

logger = logging.getLogger(__name__)

class WhatsAppBusinessAPI:
    """Classe para integração com WhatsApp Business API"""

    def __init__(self, clinic: Clinic = None):
        self.clinic = clinic
        self.base_url = "https://graph.facebook.com/v17.0"

        if clinic and clinic.whatsapp_access_token and clinic.whatsapp_business_id:
            self.access_token = clinic.whatsapp_access_token
            self.phone_number_id = clinic.whatsapp_business_id
        else:
            # Usar credenciais padrão da aplicação
            self.access_token = current_app.config.get('WHATSAPP_ACCESS_TOKEN')
            self.phone_number_id = current_app.config.get('WHATSAPP_PHONE_NUMBER_ID')

    def send_message(self, to_number: str, message: str, message_type: str = "text") -> Tuple[bool, str]:
        """
        Envia mensagem via WhatsApp Business API

        Args:
            to_number: Número do destinatário (formato internacional: 5511999999999)
            message: Conteúdo da mensagem
            message_type: Tipo da mensagem (text, template, interactive)

        Returns:
            Tuple (success, message_id/error_message)
        """
        if not self.access_token or not self.phone_number_id:
            return False, "Credenciais do WhatsApp não configuradas"

        url = f"{self.base_url}/{self.phone_number_id}/messages"

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": message_type
        }

        if message_type == "text":
            payload["text"] = {"body": message}
        elif message_type == "template":
            # Para mensagens de template pré-aprovadas
            template_parts = message.split("|")
            template_name = template_parts[0]
            language_code = template_parts[1] if len(template_parts) > 1 else "pt_BR"
            components = []

            if len(template_parts) > 2:
                # Adicionar parâmetros ao template
                params = []
                for param in template_parts[2:]:
                    params.append({"type": "text", "text": param})

                components = [{
                    "type": "body",
                    "parameters": params
                }]

            payload["template"] = {
                "name": template_name,
                "language": {"code": language_code},
                "components": components
            }
        elif message_type == "interactive":
            # Mensagens interativas (botões, listas)
            try:
                interactive_data = json.loads(message)
                payload["interactive"] = interactive_data
            except:
                return False, "Formato inválido para mensagem interativa"

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            result = response.json()
            message_id = result.get('messages', [{}])[0].get('id')

            # Registrar no banco
            self._log_conversation(
                to_number=to_number,
                direction='outbound',
                message_type=message_type,
                content=message,
                message_id=message_id
            )

            return True, message_id

        except requests.exceptions.RequestException as e:
            error_msg = f"Erro ao enviar mensagem: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def send_template_message(self, to_number: str, template_name: str,
                             language_code: str = "pt_BR",
                             parameters: List[str] = None) -> Tuple[bool, str]:
        """
        Envia mensagem de template pré-aprovado
        """
        if parameters:
            message = f"{template_name}|{language_code}|{'|'.join(parameters)}"
        else:
            message = f"{template_name}|{language_code}"

        return self.send_message(to_number, message, message_type="template")

    def send_appointment_confirmation(self, appointment: Appointment) -> bool:
        """
        Envia confirmação de agendamento
        """
        patient = appointment.patient
        service = appointment.service

        message = f"""
✅ *CONFIRMAÇÃO DE AGENDAMENTO*

👤 *Paciente:* {patient.name}
🏥 *Serviço:* {service.name}
📅 *Data:* {appointment.scheduled_date.strftime('%d/%m/%Y')}
⏰ *Horário:* {appointment.scheduled_time.strftime('%H:%M')}
📍 *Local:* {appointment.clinic.name}
{appointment.clinic.address if appointment.clinic.address else ''}

*Instruções:*
• Chegue 15 minutos antes do horário
• Leve documento com foto
• Traga exames anteriores (se houver)

⚠️ *Cancelamentos devem ser feitos com 24h de antecedência.*

Dúvidas? Responda esta mensagem!
""".strip()

        success, _ = self.send_message(patient.phone, message)

        if success:
            appointment.confirmation_sent = True
            appointment.confirmation_sent_at = datetime.utcnow()
            db.session.commit()

        return success

    def send_appointment_reminder(self, appointment: Appointment, hours_before: int = 24) -> bool:
        """
        Envia lembrete de consulta
        """
        patient = appointment.patient

        message = f"""
⏰ *LEMBRETE DE CONSULTA*

Olá {patient.name}!

Você tem uma consulta agendada para *{appointment.scheduled_date.strftime('%d/%m/%Y')}* às *{appointment.scheduled_time.strftime('%H:%M')}*.

*Serviço:* {appointment.service.name}
*Profissional:* {appointment.professional.name if appointment.professional else 'A definir'}

📍 *Local:* {appointment.clinic.name}
{appointment.clinic.address if appointment.clinic.address else ''}

Para confirmar, reagendar ou cancelar, responda esta mensagem!

_Atendimento via WhatsApp: {appointment.clinic.whatsapp_phone or appointment.clinic.phone}_
""".strip()

        success, _ = self.send_message(patient.phone, message)

        if success:
            appointment.reminder_sent = True
            appointment.reminder_sent_at = datetime.utcnow()
            db.session.commit()

        return success

    def send_cancellation_notification(self, appointment: Appointment, reason: str = None) -> bool:
        """
        Envia notificação de cancelamento
        """
        patient = appointment.patient

        reason_text = f"\n*Motivo:* {reason}" if reason else ""

        message = f"""
❌ *AGENDAMENTO CANCELADO*

Seu agendamento para *{appointment.scheduled_date.strftime('%d/%m/%Y')}* às *{appointment.scheduled_time.strftime('%H:%M')}* foi cancelado.{reason_text}

*Serviço:* {appointment.service.name}

Para reagendar ou tirar dúvidas, responda esta mensagem!

_Atendimento via WhatsApp: {appointment.clinic.whatsapp_phone or appointment.clinic.phone}_
""".strip()

        success, _ = self.send_message(patient.phone, message)
        return success

    def process_incoming_message(self, data: Dict) -> bool:
        """
        Processa mensagem recebida do webhook do WhatsApp
        """
        try:
            # Extrair dados da mensagem
            message_data = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {})

            # Verificar se é uma mensagem
            if 'messages' not in message_data:
                return False

            message = message_data['messages'][0]
            from_number = message['from']
            message_type = message['type']
            message_id = message['id']

            # Extrair conteúdo baseado no tipo
            if message_type == 'text':
                content = message['text']['body']
            elif message_type == 'interactive':
                content = json.dumps(message['interactive'])
            else:
                content = f"[{message_type.upper()}]"

            # Encontrar ou criar empresa (baseado no número de telefone)
            # Em produção, você teria um mapeamento de números para empresas
            clinic = Clinic.query.filter(
                (Clinic.whatsapp_phone == from_number) |
                (Clinic.phone == from_number)
            ).first()

            if not clinic:
                # Usar empresa padrão ou criar uma nova
                clinic = Clinic.query.first()
                if not clinic:
                    logger.error("Nenhuma empresa configurada no sistema")
                    return False

            # Encontrar ou criar paciente
            patient = Patient.query.filter_by(
                clinic_id=clinic.id,
                phone=from_number
            ).first()

            if not patient:
                patient = Patient(
                    clinic_id=clinic.id,
                    phone=from_number,
                    source='whatsapp'
                )
                db.session.add(patient)
                db.session.flush()

            # Registrar conversa
            conversation = Conversation(
                clinic_id=clinic.id,
                patient_id=patient.id,
                platform='whatsapp',
                message_id=message_id,
                direction='inbound',
                message_type=message_type,
                content=content,
                status='received'
            )
            db.session.add(conversation)

            # Processar com IA
            self._process_with_ai(conversation, clinic, patient)

            db.session.commit()
            return True

        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}")
            db.session.rollback()
            return False

    def _process_with_ai(self, conversation: Conversation, clinic: Clinic, patient: Patient):
        """
        Processa a mensagem com IA para entender a intenção
        """
        try:
            # Usar OpenAI para classificar a intenção
            import openai

            openai.api_key = current_app.config.get('OPENAI_API_KEY')

            prompt = f"""
Você é um assistente de empresa de prestação de serviços. Analise a mensagem do cliente e classifique a intenção.

Opções de intenção:
1. booking - Quer agendar um serviço
2. cancellation - Quer cancelar um agendamento
3. reschedule - Quer reagendar um agendamento
4. information - Quer informações (horários, endereço, preços, etc.)
5. confirmation - Quer confirmar um agendamento
6. other - Outros assuntos

Mensagem: "{conversation.content}"

Responda no formato JSON:
{{
"intent": "booking",
"confidence": 0.95,
"entities": {{
"service": "corte de cabelo",
"date": "amanhã",
"time": "14:00"
}}
}}
"""

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um classificador de intenções para empresas de prestação de serviços."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )

            result = json.loads(response.choices[0].message.content)

            conversation.intent = result.get('intent')
            conversation.confidence = result.get('confidence')
            conversation.processed_by_ai = True
            conversation.ai_response = json.dumps(result.get('entities', {}))

            # Gerar resposta automática baseada na intenção
            self._generate_auto_response(conversation, clinic, patient)

        except Exception as e:
            logger.error(f"Erro no processamento de IA: {str(e)}")
            conversation.error_message = str(e)

    def _generate_auto_response(self, conversation: Conversation, clinic: Clinic, patient: Patient):
        """
        Gera resposta automática baseada na intenção detectada
        """
        intent = conversation.intent

        if intent == 'booking':
            response = self._get_booking_response(clinic, patient)
        elif intent == 'cancellation':
            response = self._get_cancellation_response(clinic, patient)
        elif intent == 'information':
            response = self._get_information_response(clinic)
        else:
            response = self._get_default_response(clinic)

        # Enviar resposta
        success, message_id = self.send_message(
            to_number=patient.phone,
            message=response,
            message_type='text'
        )

        if success:
            # Registrar resposta no banco
            outbound_conversation = Conversation(
                clinic_id=clinic.id,
                patient_id=patient.id,
                platform='whatsapp',
                message_id=message_id,
                direction='outbound',
                message_type='text',
                content=response,
                status='sent'
            )
            db.session.add(outbound_conversation)

    def _get_booking_response(self, clinic: Clinic, patient: Patient) -> str:
        """Resposta para agendamento"""
        return f"""
👋 Olá!

Para agendar um serviço, por favor informe:

1️⃣ *Qual serviço você precisa?*
(ex: Corte de cabelo, Manicure, etc.)

2️⃣ *Qual a data preferida?*
(ex: amanhã, 25/12, próxima segunda)

3️⃣ *Qual o horário preferido?*
(ex: 14:00, tarde, manhã)

Ou você pode responder com a data e horário diretamente!

🏢 *{clinic.name}*
📞 {clinic.phone}
""".strip()

    def _get_cancellation_response(self, clinic: Clinic, patient: Patient) -> str:
        """Resposta para cancelamento"""
        # Buscar agendamentos futuros do paciente
        from datetime import date
        appointments = Appointment.query.filter(
            Appointment.clinic_id == clinic.id,
            Appointment.patient_id == patient.id,
            Appointment.scheduled_date >= date.today(),
            Appointment.status.in_(['scheduled', 'confirmed'])
        ).order_by(Appointment.scheduled_date).all()

        if appointments:
            response = "📋 *Seus agendamentos futuros:*\n\n"
            for i, appt in enumerate(appointments[:5], 1):
                response += f"{i}️⃣ {appt.scheduled_date.strftime('%d/%m')} às {appt.scheduled_time.strftime('%H:%M')} - {appt.service.name}\n"
            response += "\n*Digite o número do agendamento que deseja cancelar:*"
        else:
            response = "✅ Você não tem agendamentos futuros para cancelar.\nPara agendar um serviço, digite *AGENDAR*"

        return response

    def _get_information_response(self, clinic: Clinic) -> str:
        """Resposta para informações"""
        specialties = clinic.get_specialties()
        specialties_text = "\n".join([f"• {s}" for s in specialties]) if specialties else "• Serviços Gerais"

        return f"""
🏢 *{clinic.name}*

📌 *Endereço:*
{clinic.address if clinic.address else 'A definir'}

⏰ *Horário de Funcionamento:*
Segunda a Sexta: 8h às 18h
Sábado: 8h às 12h
Domingo: Fechado

🎯 *Serviços:*
{specialties_text}

📞 *Contato:*
{clinic.phone}
{clinic.whatsapp_phone if clinic.whatsapp_phone else ''}

💰 *Formas de Pagamento:*
Dinheiro, Cartão, PIX e Convênios

Para agendar, digite *AGENDAR*
Para cancelar, digite *CANCELAR*
""".strip()

    def _get_default_response(self, clinic: Clinic) -> str:
        """Resposta padrão"""
        return f"""
🤖 *Assistente Vexus IA*

Olá! Sou o assistente virtual da {clinic.name}.

Como posso ajudar?

*Digite uma opção:*
� AGENDAR - Marcar serviço
❌ CANCELAR - Cancelar agendamento
📋 INFORMAÇÕES - Horários, endereço, preços
👨‍💼 FALAR COM ATENDENTE

Ou escreva sua dúvida diretamente!
""".strip()

    def _log_conversation(self, to_number: str, direction: str,
                         message_type: str, content: str, message_id: str = None):
        """
        Registra conversa no banco de dados
        """
        try:
            # Encontrar clínica e paciente
            clinic = self.clinic or Clinic.query.first()
            if not clinic:
                return

            patient = Patient.query.filter_by(
                clinic_id=clinic.id,
                phone=to_number
            ).first()

            conversation = Conversation(
                clinic_id=clinic.id,
                patient_id=patient.id if patient else None,
                platform='whatsapp',
                message_id=message_id,
                direction=direction,
                message_type=message_type,
                content=content,
                status='sent'
            )

            db.session.add(conversation)
            db.session.commit()

        except Exception as e:
            logger.error(f"Erro ao registrar conversa: {str(e)}")
            db.session.rollback()

class WhatsAppWebhookHandler:
    """Handler para webhooks do WhatsApp"""

    @staticmethod
    def verify_webhook(token: str, mode: str, challenge: str) -> Tuple[bool, str]:
        """
        Verifica o webhook do WhatsApp

        Args:
            token: Token recebido
            mode: Mode recebido
            challenge: Challenge recebido

        Returns:
            Tuple (is_valid, response)
        """
        verify_token = current_app.config.get('WHATSAPP_WEBHOOK_VERIFY_TOKEN')

        if mode == 'subscribe' and token == verify_token:
            return True, challenge
        else:
            return False, 'Verification failed'

    @staticmethod
    def handle_webhook(data: Dict) -> bool:
        """
        Processa o webhook do WhatsApp
        """
        handler = WhatsAppBusinessAPI()
        return handler.process_incoming_message(data)