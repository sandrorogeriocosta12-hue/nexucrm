import json
import re
from datetime import datetime, timedelta
from enum import Enum

class ConversationState(Enum):
    """Estados da conversa no fluxo de agendamento"""
    INITIAL = "initial"
    CHOOSING_SERVICE = "choosing_service"
    PROVIDING_NAME = "providing_name"
    CHOOSING_DATE = "choosing_date"
    CHOOSING_TIME = "choosing_time"
    CONFIRMING = "confirming"
    COMPLETED = "completed"

class WhatsAppFlowManager:
    """Gerenciador do fluxo de conversa via WhatsApp"""
    
    def __init__(self, db_session, clinic_id):
        self.db = db_session
        self.clinic_id = clinic_id
        self.conversations = {}  # phone -> state_data
        
    def _extract_phone(self, phone_str):
        """Extrai e formata o número de telefone"""
        # Remove caracteres não numéricos
        digits = re.sub(r'\D', '', phone_str)
        
        # Se começar com 55 (Brasil), mantém
        if digits.startswith('55'):
            return f"+{digits}"
        # Se tiver 9 dígitos (sem DDD), adiciona DDD padrão
        elif len(digits) == 9:
            return f"+5511{digits}"  # DDD 11 como exemplo
        else:
            return f"+55{digits}"
    
    def _get_available_dates(self):
        """Retorna datas disponíveis para agendamento (próximos 15 dias)"""
        today = datetime.now().date()
        available_dates = []
        
        for i in range(1, 16):  # Próximos 15 dias
            date = today + timedelta(days=i)
            # Não permitir agendamentos aos domingos
            if date.weekday() != 6:  # 6 = domingo
                available_dates.append(date.strftime("%d/%m/%Y"))
        
        return available_dates
    
    def _get_available_times(self, date_str):
        """Retorna horários disponíveis para uma data específica"""
        # Horários padrão para clínicas
        times = []
        
        # Converte string para objeto date
        date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()
        
        # Verifica se é sábado (horário reduzido)
        if date_obj.weekday() == 5:  # 5 = sábado
            start_hour = 8
            end_hour = 12
        else:
            start_hour = 8
            end_hour = 18
        
        # Gera horários a cada 30 minutos
        for hour in range(start_hour, end_hour):
            for minute in [0, 30]:
                # Formata o horário
                time_str = f"{hour:02d}:{minute:02d}"
                times.append(time_str)
        
        return times
    
    def _check_time_availability(self, date_str, time_str):
        """Verifica se o horário está disponível"""
        from database import Appointment
        
        # Converte para objetos datetime
        date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()
        time_obj = datetime.strptime(time_str, "%H:%M").time()
        
        # Verifica se já existe agendamento neste horário
        existing = Appointment.query.filter(
            Appointment.clinic_id == self.clinic_id,
            Appointment.scheduled_date == date_obj,
            Appointment.scheduled_time == time_obj,
            Appointment.status.in_(['agendado', 'confirmado'])
        ).first()
        
        return existing is None
    
    def process_message(self, from_number, message_text):
        """Processa uma mensagem recebida"""
        phone = self._extract_phone(from_number)
        
        # Inicializa ou recupera estado da conversa
        if phone not in self.conversations:
            self.conversations[phone] = {
                'state': ConversationState.INITIAL,
                'data': {}
            }
        
        state_data = self.conversations[phone]
        current_state = state_data['state']
        
        # Processa de acordo com o estado atual
        if current_state == ConversationState.INITIAL:
            return self._handle_initial_state(phone, message_text, state_data)
        elif current_state == ConversationState.CHOOSING_SERVICE:
            return self._handle_service_selection(phone, message_text, state_data)
        elif current_state == ConversationState.PROVIDING_NAME:
            return self._handle_name_input(phone, message_text, state_data)
        elif current_state == ConversationState.CHOOSING_DATE:
            return self._handle_date_selection(phone, message_text, state_data)
        elif current_state == ConversationState.CHOOSING_TIME:
            return self._handle_time_selection(phone, message_text, state_data)
        elif current_state == ConversationState.CONFIRMING:
            return self._handle_confirmation(phone, message_text, state_data)
        else:
            return self._handle_general_inquiry(message_text)
    
    def _handle_initial_state(self, phone, message, state_data):
        """Lida com o estado inicial da conversa"""
        message_lower = message.lower()
        
        # Verifica intenção do usuário
        if any(word in message_lower for word in ['agendar', 'marcar', 'consulta', 'horário']):
            state_data['state'] = ConversationState.CHOOSING_SERVICE
            return self._get_services_list()
        elif any(word in message_lower for word in ['cancelar', 'desmarcar']):
            return self._handle_cancellation_request(phone)
        elif any(word in message_lower for word in ['horário', 'funciona', 'aberto']):
            return "⏰ *Horário de Funcionamento:*\nSegunda a Sexta: 8h às 18h\nSábado: 8h às 12h\nDomingo: Fechado"
        elif any(word in message_lower for word in ['valor', 'preço', 'custa']):
            return self._get_prices_list()
        else:
            return self._get_welcome_message()
    
    def _get_welcome_message(self):
        """Mensagem de boas-vindas"""
        return """👋 *Bem-vindo à Clínica Vexus!*

Eu sou o assistente virtual. Como posso ajudar?

*Digite o número da opção desejada:*
1️⃣ *Agendar consulta*
2️⃣ *Cancelar agendamento*
3️⃣ *Horário de funcionamento*
4️⃣ *Valores e procedimentos*
5️⃣ *Falar com atendente*

Ou escreva sua dúvida diretamente!"""
    
    def _get_services_list(self):
        """Retorna lista de serviços disponíveis"""
        from database import Service
        
        services = Service.query.filter_by(
            clinic_id=self.clinic_id,
            active=True
        ).all()
        
        response = "📋 *Selecione o serviço desejado:*\n\n"
        for i, service in enumerate(services, 1):
            duration = f" ({service.duration}min)" if service.duration else ""
            price = f" - R$ {service.price:.2f}" if service.price else ""
            response += f"{i}️⃣ {service.name}{duration}{price}\n"
        
        response += "\n*Digite o número do serviço desejado:*"
        return response
    
    def _handle_service_selection(self, phone, message, state_data):
        """Processa seleção de serviço"""
        try:
            service_index = int(message) - 1
            from database import Service
            
            services = Service.query.filter_by(
                clinic_id=self.clinic_id,
                active=True
            ).all()
            
            if 0 <= service_index < len(services):
                selected_service = services[service_index]
                state_data['data']['service_id'] = selected_service.id
                state_data['data']['service_name'] = selected_service.name
                state_data['state'] = ConversationState.PROVIDING_NAME
                
                return "📝 *Ótima escolha!*\n\nAgora preciso do seu *nome completo* para o agendamento:"
            else:
                return "❌ Opção inválida. Por favor, digite um número da lista:"
                
        except ValueError:
            return "❌ Por favor, digite apenas o *número* do serviço desejado:"
    
    def _handle_name_input(self, phone, message, state_data):
        """Processa entrada do nome"""
        if len(message.strip()) < 3:
            return "❌ Por favor, digite seu *nome completo* (mínimo 3 letras):"
        
        state_data['data']['patient_name'] = message.strip()
        state_data['state'] = ConversationState.CHOOSING_DATE
        
        # Obtém datas disponíveis
        dates = self._get_available_dates()
        
        response = f"👤 Nome registrado: *{message.strip()}*\n\n"
        response += "📅 *Selecione uma data para o agendamento:*\n\n"
        
        for i, date in enumerate(dates[:5], 1):  # Mostra apenas 5 primeiras datas
            response += f"{i}️⃣ {date}\n"
        
        response += "\n*Digite o número da data desejada ou uma data específica (DD/MM/AAAA):*"
        return response
    
    def _handle_date_selection(self, phone, message, state_data):
        """Processa seleção de data"""
        try:
            # Tenta interpretar como número da lista
            date_index = int(message) - 1
            dates = self._get_available_dates()
            
            if 0 <= date_index < len(dates[:5]):  # Apenas as 5 mostradas
                selected_date = dates[date_index]
            else:
                return "❌ Data inválida. Escolha um número da lista:"
                
        except ValueError:
            # Tenta interpretar como data no formato DD/MM/AAAA
            try:
                # Valida formato da data
                datetime.strptime(message, "%d/%m/%Y")
                selected_date = message
                
                # Verifica se está dentro do período permitido
                dates = self._get_available_dates()
                if selected_date not in dates:
                    return "❌ Data não disponível para agendamento. Escolha uma data futura (exceto domingos):"
                    
            except ValueError:
                return "❌ Formato inválido. Use DD/MM/AAAA (ex: 25/12/2023) ou escolha um número da lista:"
        
        state_data['data']['selected_date'] = selected_date
        state_data['state'] = ConversationState.CHOOSING_TIME
        
        # Obtém horários disponíveis
        times = self._get_available_times(selected_date)
        
        response = f"📅 Data selecionada: *{selected_date}*\n\n"
        response += "⏰ *Selecione um horário disponível:*\n\n"
        
        # Agrupa horários em colunas
        for i in range(0, len(times), 3):
            row_times = times[i:i+3]
            time_options = []
            for j, time in enumerate(row_times, i+1):
                time_options.append(f"{j}️⃣ {time}")
            response += " | ".join(time_options) + "\n"
        
        response += "\n*Digite o número do horário desejado:*"
        return response
    
    def _handle_time_selection(self, phone, message, state_data):
        """Processa seleção de horário"""
        try:
            time_index = int(message) - 1
            times = self._get_available_times(state_data['data']['selected_date'])
            
            if 0 <= time_index < len(times):
                selected_time = times[time_index]
                
                # Verifica disponibilidade
                if not self._check_time_availability(state_data['data']['selected_date'], selected_time):
                    return "❌ Este horário já está ocupado. Por favor, selecione outro horário:"
                
                state_data['data']['selected_time'] = selected_time
                state_data['state'] = ConversationState.CONFIRMING
                
                return self._get_confirmation_message(state_data['data'])
            else:
                return "❌ Horário inválido. Escolha um número da lista:"
                
        except ValueError:
            return "❌ Por favor, digite apenas o *número* do horário desejado:"
    
    def _get_confirmation_message(self, data):
        """Gera mensagem de confirmação"""
        return f"""✅ *CONFIRMAÇÃO DE AGENDAMENTO*

👤 *Paciente:* {data['patient_name']}
🏥 *Serviço:* {data['service_name']}
📅 *Data:* {data['selected_date']}
⏰ *Horário:* {data['selected_time']}

*Para confirmar, digite:* CONFIRMAR
*Para cancelar, digite:* CANCELAR

_⚠️ Lembre-se: Cancelamentos devem ser feitos com 24h de antecedência._"""
    
    def _handle_confirmation(self, phone, message, state_data):
        """Processa confirmação do agendamento"""
        message_lower = message.lower()
        
        if message_lower == 'confirmar':
            # Salva o agendamento no banco de dados
            success = self._save_appointment(phone, state_data['data'])
            
            if success:
                # Limpa estado da conversa
                self.conversations[phone]['state'] = ConversationState.COMPLETED
                
                return """🎉 *AGENDAMENTO CONFIRMADO!*

Obrigado por escolher a Clínica Vexus.

📋 *Lembretes importantes:*
• Chegue 15 minutos antes do horário
• Leve documento com foto
• Cancelamentos com 24h de antecedência

📞 Dúvidas? Entre em contato: (11) 99999-9999

_Em breve enviaremos um lembrete por WhatsApp._"""
            else:
                return "❌ Erro ao salvar agendamento. Por favor, tente novamente ou entre em contato conosco."
        
        elif message_lower == 'cancelar':
            self.conversations[phone]['state'] = ConversationState.INITIAL
            return "❌ Agendamento cancelado. Posso ajudar com algo mais?"
        
        else:
            return "❌ Por favor, digite *CONFIRMAR* para confirmar ou *CANCELAR* para cancelar:"
    
    def _save_appointment(self, phone, data):
        """Salva o agendamento no banco de dados"""
        try:
            from database import Patient, Appointment, Conversation, db
            
            # Encontra ou cria paciente
            patient = Patient.query.filter_by(phone=phone).first()
            if not patient:
                patient = Patient(
                    phone=phone,
                    name=data['patient_name']
                )
                db.session.add(patient)
                db.session.flush()  # Para obter o ID
            
            # Cria agendamento
            appointment = Appointment(
                clinic_id=self.clinic_id,
                patient_id=patient.id,
                service_id=data['service_id'],
                scheduled_date=datetime.strptime(data['selected_date'], "%d/%m/%Y").date(),
                scheduled_time=datetime.strptime(data['selected_time'], "%H:%M").time(),
                status='agendado',
                notes=f"Agendado via WhatsApp Bot - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )
            
            db.session.add(appointment)
            db.session.commit()
            
            # Registra conversa
            conversation = Conversation(
                clinic_id=self.clinic_id,
                patient_phone=phone,
                intent="agendamento",
                confidence=1.0
            )
            db.session.add(conversation)
            db.session.commit()
            
            return True
            
        except Exception as e:
            print(f"Erro ao salvar agendamento: {str(e)}")
            db.session.rollback()
            return False
    
    def _handle_cancellation_request(self, phone):
        """Processa solicitação de cancelamento"""
        from database import Appointment, Patient
        
        # Busca paciente pelo telefone
        patient = Patient.query.filter_by(phone=phone).first()
        
        if not patient:
            return "❌ Não encontramos agendamentos para este número. Verifique o telefone ou entre em contato com a recepção."
        
        # Busca agendamentos futuros
        today = datetime.now().date()
        appointments = Appointment.query.filter(
            Appointment.patient_id == patient.id,
            Appointment.scheduled_date >= today,
            Appointment.status.in_(['agendado', 'confirmado'])
        ).order_by(Appointment.scheduled_date).all()
        
        if not appointments:
            return "✅ Não há agendamentos futuros para cancelar."
        
        # Lista agendamentos
        response = "📋 *Seus Agendamentos Futuros:*\n\n"
        for i, appt in enumerate(appointments, 1):
            response += f"{i}️⃣ {appt.scheduled_date.strftime('%d/%m/%Y')} às {appt.scheduled_time.strftime('%H:%M')} - {appt.service.name}\n"
        
        response += "\n*Digite o número do agendamento que deseja cancelar:*"
        
        # Armazena a lista de agendamentos no estado da conversa
        if phone not in self.conversations:
            self.conversations[phone] = {}
        
        self.conversations[phone]['pending_cancellations'] = [
            {'id': appt.id, 'date': appt.scheduled_date, 'time': appt.scheduled_time}
            for appt in appointments
        ]
        
        return response
    
    def _get_prices_list(self):
        """Retorna lista de preços"""
        from database import Service
        
        services = Service.query.filter_by(
            clinic_id=self.clinic_id,
            active=True
        ).order_by(Service.price).all()
        
        response = "💰 *Tabela de Preços:*\n\n"
        
        for service in services:
            price = f"R$ {service.price:.2f}" if service.price else "Sob consulta"
            response += f"• {service.name}: *{price}*\n"
        
        response += "\n_Valores sujeitos a alteração sem aviso prévio._\n"
        response += "_Consultar disponibilidade de convênios._"
        
        return response
    
    def _handle_general_inquiry(self, message):
        """Lida com consultas gerais usando IA básica"""
        # Respostas padrão para perguntas frequentes
        faq_responses = {
            'convênio': "📋 *Convênios Aceitos:*\n\n• Amil\n• Bradesco Saúde\n• SulAmérica\n• Unimed\n\n_Consulte a recepção para verificar cobertura completa._",
            'endereço': "📍 *Endereço da Clínica:*\n\nRua das Flores, 123 - Centro\nSão Paulo - SP\nCEP: 01234-567",
            'estacionamento': "🚗 Temos estacionamento privativo para clientes. Valet disponível por R$ 20,00.",
            'documentos': "📄 *Documentos necessários:*\n\n• Documento com foto (RG ou CNH)\n• Cartão do convênio (se houver)\n• Exames anteriores (se aplicável)",
            'pagamento': "💳 *Formas de Pagamento:*\n\n• Dinheiro\n• Cartão de crédito/débito\n• PIX\n• Convênios\n\n_Parcelamento em até 3x no cartão._"
        }
        
        # Procura palavras-chave na mensagem
        message_lower = message.lower()
        
        for keyword, response in faq_responses.items():
            if keyword in message_lower:
                return response
        
        # Se não encontrar, resposta padrão
        return "🤖 Não entendi completamente sua pergunta.\n\nVocê pode:\n• Digitar um número das opções iniciais\n• Perguntar sobre: convênios, endereço, estacionamento, documentos ou pagamento\n• Falar com atendente (digite ATENDENTE)"