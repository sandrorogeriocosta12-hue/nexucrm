import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pickle
import os
# fuzzy integration
from c_modules.ctypes_example import FuzzySystem
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

from app.models import db, Clinic, Patient, Appointment, Conversation, Subscription
import logging

logger = logging.getLogger(__name__)

class PredictiveAnalytics:
    """Sistema de análise preditiva para clínicas"""

    def __init__(self, clinic_id: str):
        self.clinic_id = clinic_id
        self.models = {}

    def prepare_patient_data(self) -> pd.DataFrame:
        """
        Prepara dados dos pacientes para análise
        """
        # Buscar todos os pacientes da clínica
        patients = Patient.query.filter_by(clinic_id=self.clinic_id).all()

        data = []

        for patient in patients:
            # Features básicas
            patient_data = {
                'patient_id': patient.id,
                'age': self._calculate_age(patient.birth_date) if patient.birth_date else None,
                'gender': 1 if patient.gender == 'M' else 0 if patient.gender == 'F' else None,
                'total_appointments': patient.total_appointments,
                'total_spent': float(patient.total_spent or 0),
                'days_since_first_appointment': (datetime.utcnow().date() - patient.first_appointment_date).days
                if patient.first_appointment_date else None,
                'days_since_last_appointment': (datetime.utcnow().date() - patient.last_appointment_date).days
                if patient.last_appointment_date else None,
                'appointment_frequency': self._calculate_appointment_frequency(patient),
                'avg_appointment_value': float(patient.total_spent or 0) / max(patient.total_appointments, 1),
                'has_phone': 1 if patient.phone else 0,
                'has_email': 1 if patient.email else 0,
                'source_encoded': self._encode_source(patient.source)
            }

            # Features de comportamento
            behavior_features = self._extract_behavior_features(patient.id)
            patient_data.update(behavior_features)

            # Target: paciente ativo (consultou nos últimos 60 dias)
            patient_data['is_active'] = 1 if patient.last_appointment_date and \
                (datetime.utcnow().date() - patient.last_appointment_date).days <= 60 else 0

            data.append(patient_data)

        df = pd.DataFrame(data)

        # Tratar valores nulos
        df = df.fillna(df.median())

        return df

    def train_churn_prediction_model(self) -> Dict:
        """
        Treina modelo para prever churn de pacientes
        """
        # Preparar dados
        df = self.prepare_patient_data()

        if len(df) < 50:
            return {'error': 'Dados insuficientes para treinamento'}

        # Separar features e target
        features = ['age', 'gender', 'total_appointments', 'total_spent',
                    'days_since_first_appointment', 'days_since_last_appointment',
                    'appointment_frequency', 'avg_appointment_value',
                    'has_phone', 'has_email', 'source_encoded',
                    'avg_days_between_appointments', 'cancellation_rate',
                    'no_show_rate', 'last_minute_cancellations']

        # Filtrar features disponíveis
        available_features = [f for f in features if f in df.columns]

        X = df[available_features]
        y = df['is_active']

        # Dividir dados
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Treinar modelo
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )

        model.fit(X_train, y_train)

        # Avaliar modelo
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        # Calcular importância das features
        feature_importance = dict(zip(available_features, model.feature_importances_))

        # Salvar modelo
        model_path = f'models/churn_model_clinic_{self.clinic_id}.pkl'
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)

        self.models['churn'] = model

        return {
            'model_type': 'churn_prediction',
            'accuracy': accuracy,
            'training_samples': len(X_train),
            'testing_samples': len(X_test),
            'feature_importance': feature_importance,
            'model_path': model_path
        }

    def predict_patient_churn(self, patient_id: str) -> Dict:
        """
        Prediz probabilidade de churn para um paciente específico
        """
        # Carregar modelo se necessário
        if 'churn' not in self.models:
            model_path = f'models/churn_model_clinic_{self.clinic_id}.pkl'
            try:
                with open(model_path, 'rb') as f:
                    self.models['churn'] = pickle.load(f)
            except:
                result = self.train_churn_prediction_model()
                if 'error' in result:
                    return result

        # Preparar dados do paciente
        patient = Patient.query.get(patient_id)
        if not patient:
            return {'error': 'Paciente não encontrado'}

        # Extrair features
        features = self._extract_patient_features_for_prediction(patient)

        # Fazer predição
        model = self.models['churn']

        # Converter para DataFrame
        features_df = pd.DataFrame([features])

        # Garantir que as features estão na mesma ordem do treinamento
        expected_features = model.feature_names_in_ if hasattr(model, 'feature_names_in_') else []
        features_df = features_df.reindex(columns=expected_features, fill_value=0)

        # Predizer
        probability = model.predict_proba(features_df)[0][1]  # Probabilidade de ser ativo
        churn_risk = 1 - probability

        # Recomendações baseadas no risco
        recommendations = self._generate_churn_recommendations(churn_risk, patient)

        return {
            'patient_id': patient_id,
            'patient_name': patient.name,
            'churn_risk': churn_risk,
            'risk_level': self._classify_risk_level(churn_risk),
            'probability_active': probability,
            'last_appointment': patient.last_appointment_date.strftime('%d/%m/%Y') if patient.last_appointment_date else 'Nunca',
            'total_appointments': patient.total_appointments,
            'total_spent': float(patient.total_spent or 0),
            'recommendations': recommendations,
            'next_best_action': self._determine_next_best_action(churn_risk, patient)
        }

    def _fuzzy_lead_score(self, engagement: float, likelihood: float) -> float:
        """Compute lead score using the C fuzzy engine."""
        # path relative to repo root; adjust if running from elsewhere
        cfg = os.path.join(os.getcwd(), 'c_modules', 'fuzzy', 'rules.json')
        fs = FuzzySystem(cfg)
        return fs.evaluate('score', [engagement, likelihood])

    def identify_at_risk_patients(self, threshold: float = 0.7) -> List[Dict]:
        """
        Identifica pacientes com alto risco de churn
        """
        # Buscar todos os pacientes
        patients = Patient.query.filter_by(clinic_id=self.clinic_id).all()

        at_risk = []

        for patient in patients:
            # Só analisar pacientes com pelo menos uma consulta
            if patient.total_appointments == 0:
                continue

            prediction = self.predict_patient_churn(patient.id)

            if 'churn_risk' in prediction and prediction['churn_risk'] >= threshold:
                at_risk.append(prediction)

        # Ordenar por risco
        at_risk.sort(key=lambda x: x['churn_risk'], reverse=True)

        return at_risk

    def calculate_clinic_health_score(self) -> Dict:
        """
        Calcula score de saúde geral da clínica
        """
        # Analisar pacientes ativos
        patients = Patient.query.filter_by(clinic_id=self.clinic_id).all()

        if not patients:
            return {'error': 'Nenhum paciente encontrado'}

        total_patients = len(patients)
        active_patients = sum(1 for p in patients if p.last_appointment_date and
                              (datetime.utcnow().date() - p.last_appointment_date).days <= 60)

        # Calcular métricas
        active_rate = (active_patients / total_patients) * 100

        # Valor médio por paciente
        total_revenue = sum(float(p.total_spent or 0) for p in patients)
        avg_revenue_per_patient = total_revenue / total_patients

        # Frequência média de consultas
        total_appointments = sum(p.total_appointments for p in patients)
        avg_appointments_per_patient = total_appointments / total_patients

        # Identificar pacientes em risco
        at_risk_patients = self.identify_at_risk_patients(threshold=0.5)
        at_risk_rate = (len(at_risk_patients) / total_patients) * 100

        # Calcular score composto (0-100)
        score = (
            (active_rate * 0.4) +
            (min(avg_revenue_per_patient, 1000) / 10 * 0.3) +
            (min(avg_appointments_per_patient, 10) * 10 * 0.2) +
            ((100 - at_risk_rate) * 0.1)
        )

        return {
            'total_patients': total_patients,
            'active_patients': active_patients,
            'active_rate': round(active_rate, 1),
            'total_revenue': round(total_revenue, 2),
            'avg_revenue_per_patient': round(avg_revenue_per_patient, 2),
            'avg_appointments_per_patient': round(avg_appointments_per_patient, 1),
            'at_risk_patients': len(at_risk_patients),
            'at_risk_rate': round(at_risk_rate, 1),
            'health_score': round(score, 1),
            'health_level': self._classify_health_level(score),
            'recommendations': self._generate_clinic_recommendations(score, at_risk_rate)
        }

    def predict_revenue_next_month(self) -> Dict:
        """
        Prediz receita para o próximo mês
        """
        # Buscar histórico de agendamentos
        six_months_ago = datetime.utcnow() - timedelta(days=180)

        appointments = Appointment.query.filter(
            Appointment.clinic_id == self.clinic_id,
            Appointment.scheduled_date >= six_months_ago.date(),
            Appointment.status.in_(['completed', 'scheduled', 'confirmed'])
        ).all()

        if not appointments:
            return {'error': 'Dados insuficientes para previsão'}

        # Agrupar por mês
        monthly_data = {}
        for appt in appointments:
            month_key = appt.scheduled_date.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = {'count': 0, 'revenue': 0}

            monthly_data[month_key]['count'] += 1
            if appt.amount:
                monthly_data[month_key]['revenue'] += float(appt.amount)

        # Converter para série temporal
        months = sorted(monthly_data.keys())[-6:]  # Últimos 6 meses
        revenues = [monthly_data[m]['revenue'] for m in months]

        # Previsão simples (média móvel)
        if len(revenues) >= 3:
            predicted_revenue = sum(revenues[-3:]) / 3  # Média dos últimos 3 meses
        else:
            predicted_revenue = sum(revenues) / len(revenues) if revenues else 0

        # Fator de crescimento sazonal (ajustar baseado no histórico)
        growth_factor = 1.05  # 5% de crescimento

        predicted_revenue *= growth_factor

        return {
            'historical_data': monthly_data,
            'predicted_revenue': round(predicted_revenue, 2),
            'confidence': 0.75,  # Confiança na previsão
            'next_month': (datetime.utcnow() + timedelta(days=30)).strftime('%Y-%m'),
            'growth_factor': growth_factor,
            'recommendations': self._generate_revenue_recommendations(predicted_revenue, monthly_data)
        }

    def _calculate_age(self, birth_date: datetime) -> int:
        """Calcula idade baseada na data de nascimento"""
        if not birth_date:
            return None

        today = datetime.utcnow().date()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    def _calculate_appointment_frequency(self, patient: Patient) -> float:
        """Calcula frequência de consultas em consultas/mês"""
        if not patient.first_appointment_date or patient.total_appointments <= 1:
            return 0

        days_active = (datetime.utcnow().date() - patient.first_appointment_date).days
        if days_active <= 0:
            return 0

        months_active = days_active / 30.44
        return patient.total_appointments / months_active

    def _encode_source(self, source: str) -> int:
        """Codifica fonte do paciente"""
        sources = {
            'whatsapp': 1,
            'website': 2,
            'referral': 3,
            'walk_in': 4,
            'phone': 5,
            None: 0
        }
        return sources.get(source, 0)

    def _extract_behavior_features(self, patient_id: str) -> Dict:
        """Extrai features de comportamento do paciente"""
        # Buscar histórico de agendamentos
        appointments = Appointment.query.filter_by(
            patient_id=patient_id
        ).order_by(Appointment.scheduled_date).all()

        if len(appointments) < 2:
            return {
                'avg_days_between_appointments': 0,
                'cancellation_rate': 0,
                'no_show_rate': 0,
                'last_minute_cancellations': 0
            }

        # Calcular dias entre consultas
        days_between = []
        for i in range(1, len(appointments)):
            days = (appointments[i].scheduled_date - appointments[i-1].scheduled_date).days
            days_between.append(days)

        avg_days_between = sum(days_between) / len(days_between) if days_between else 0

        # Calcular taxas
        total_appointments = len(appointments)
        cancellations = sum(1 for a in appointments if a.status == 'cancelled')
        no_shows = sum(1 for a in appointments if a.status == 'no_show')

        # Cancelamentos de última hora (menos de 24h)
        last_minute = sum(1 for a in appointments if
                          a.status == 'cancelled' and
                          a.cancellation_reason and
                          'última hora' in a.cancellation_reason.lower())

        return {
            'avg_days_between_appointments': avg_days_between,
            'cancellation_rate': cancellations / total_appointments,
            'no_show_rate': no_shows / total_appointments,
            'last_minute_cancellations': last_minute
        }

    def _extract_patient_features_for_prediction(self, patient: Patient) -> Dict:
        """Extrai features de um paciente para predição"""
        behavior = self._extract_behavior_features(patient.id)

        return {
            'age': self._calculate_age(patient.birth_date) or 0,
            'gender': 1 if patient.gender == 'M' else 0,
            'total_appointments': patient.total_appointments,
            'total_spent': float(patient.total_spent or 0),
            'days_since_first_appointment': (datetime.utcnow().date() - patient.first_appointment_date).days
            if patient.first_appointment_date else 0,
            'days_since_last_appointment': (datetime.utcnow().date() - patient.last_appointment_date).days
            if patient.last_appointment_date else 999,
            'appointment_frequency': self._calculate_appointment_frequency(patient),
            'avg_appointment_value': float(patient.total_spent or 0) / max(patient.total_appointments, 1),
            'has_phone': 1 if patient.phone else 0,
            'has_email': 1 if patient.email else 0,
            'source_encoded': self._encode_source(patient.source),
            'avg_days_between_appointments': behavior['avg_days_between_appointments'],
            'cancellation_rate': behavior['cancellation_rate'],
            'no_show_rate': behavior['no_show_rate'],
            'last_minute_cancellations': behavior['last_minute_cancellations']
        }

    def _classify_risk_level(self, risk: float) -> str:
        """Classifica nível de risco"""
        if risk >= 0.7:
            return 'CRÍTICO'
        elif risk >= 0.5:
            return 'ALTO'
        elif risk >= 0.3:
            return 'MODERADO'
        else:
            return 'BAIXO'

    def _generate_churn_recommendations(self, risk: float, patient: Patient) -> List[str]:
        """Gera recomendações baseadas no risco de churn"""
        recommendations = []

        if risk >= 0.7:
            recommendations.extend([
                "⚠️ CONTATO IMEDIATO: Ligar diretamente para o paciente",
                "🎁 OFERTA ESPECIAL: Desconto de 20% na próxima consulta",
                "📞 AGENDAMENTO PESSOAL: Oferecer para agendar no mesmo horário"
            ])
        elif risk >= 0.5:
            recommendations.extend([
                "📱 CONTATO VIA WHATSAPP: Mensagem personalizada",
                "💌 EMAIL DE RETENÇÃO: Conteúdo educativo + oferta",
                "📅 LEMBRETE ESPECIAL: Oferecer horários preferenciais"
            ])
        elif risk >= 0.3:
            recommendations.extend([
                "✉️ NEWSLETTER: Incluir em campanha de conteúdo",
                "📊 SEGMENTAÇÃO: Incluir em grupo de 'retorno programado'",
                "🎯 FOLLOW-UP: Contato em 15 dias se não agendar"
            ])

        # Recomendações baseadas no perfil
        if patient.total_appointments == 1:
            recommendations.append("🌟 PACIENTE NOVO: Programa de fidelização")

        if patient.total_spent > 500:
            recommendations.append("💰 ALTO VALOR: Programa cliente premium")

        return recommendations

    def _determine_next_best_action(self, risk: float, patient: Patient) -> Dict:
        """Determina a próxima melhor ação"""
        if risk >= 0.7:
            return {
                'action': 'CALL',
                'priority': 'HIGH',
                'timing': 'TODAY',
                'message': f"Ligar para {patient.name} e oferecer consulta com desconto",
                'channel': 'PHONE'
            }
        elif risk >= 0.5:
            return {
                'action': 'WHATSAPP',
                'priority': 'MEDIUM',
                'timing': 'TOMORROW',
                'message': f"Enviar oferta especial via WhatsApp",
                'channel': 'WHATSAPP'
            }
        else:
            return {
                'action': 'EMAIL',
                'priority': 'LOW',
                'timing': 'THIS_WEEK',
                'message': f"Incluir em newsletter segmentada",
                'channel': 'EMAIL'
            }

    def _classify_health_level(self, score: float) -> str:
        """Classifica nível de saúde da clínica"""
        if score >= 80:
            return 'EXCELENTE'
        elif score >= 60:
            return 'BOM'
        elif score >= 40:
            return 'REGULAR'
        else:
            return 'CRÍTICO'

    def _generate_clinic_recommendations(self, score: float, at_risk_rate: float) -> List[str]:
        """Gera recomendações para a clínica"""
        recommendations = []

        if score < 40:
            recommendations.extend([
                "🚨 URGENTE: Implementar programa de retenção imediatamente",
                "📊 ANÁLISE: Revisar processos de atendimento ao paciente",
                "🎯 FOCO: Reduzir taxa de pacientes em risco",
                "💬 PESQUISA: Realizar pesquisa de satisfação",
                "👥 TREINAMENTO: Capacitar equipe em retenção"
            ])
        elif score < 60:
            recommendations.extend([
                "📈 OTIMIZAÇÃO: Melhorar experiência do paciente",
                "📱 AUTOMAÇÃO: Implementar follow-up automatizado",
                "🎁 FIDELIZAÇÃO: Criar programa de recompensas",
                "📊 MONITORAMENTO: Acompanhar métricas semanalmente"
            ])

        if at_risk_rate > 30:
            recommendations.append(f"⚠️ ALERTA: {at_risk_rate:.1f}% dos pacientes em risco")

        return recommendations

    def _generate_revenue_recommendations(self, predicted_revenue: float, historical_data: Dict) -> List[str]:
        """Gera recomendações para aumentar receita"""
        recommendations = []

        # Analisar tendência
        if len(historical_data) >= 2:
            last_month = list(historical_data.values())[-1]['revenue']
            if predicted_revenue < last_month:
                recommendations.append("📉 TENDÊNCIA: Receita pode cair. Reforce marketing.")

        if predicted_revenue < 5000:  # Meta mínima
            recommendations.extend([
                "🎯 META: Estabelecer meta de R$ 5.000 para o mês",
                "📱 CAMPANHA: Lançar campanha de agendamento online",
                "👥 INDICAÇÃO: Implementar programa de indicações",
                "💎 UPSELL: Oferecer procedimentos complementares"
            ])

        return recommendations


class AIPoweredInsights:
    """Insights com IA para tomada de decisão"""

    def __init__(self, clinic_id: str):
        self.clinic_id = clinic_id
        self.analytics = PredictiveAnalytics(clinic_id)

    def generate_weekly_insights(self) -> Dict:
        """
        Gera insights semanais automatizados
        """
        insights = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'clinic_id': self.clinic_id,
            'insights': [],
            'alerts': [],
            'opportunities': [],
            'recommendations': []
        }

        # 1. Saúde da clínica
        health = self.analytics.calculate_clinic_health_score()
        insights['health_score'] = health.get('health_score', 0)
        insights['health_level'] = health.get('health_level', 'DESCONHECIDO')

        if health.get('health_score', 0) < 60:
            insights['alerts'].append({
                'type': 'HEALTH_SCORE_LOW',
                'message': f"Score de saúde da clínica está baixo: {health['health_score']}",
                'priority': 'HIGH'
            })

        # 2. Pacientes em risco
        at_risk = self.analytics.identify_at_risk_patients(threshold=0.5)
        if at_risk:
            insights['alerts'].append({
                'type': 'PATIENTS_AT_RISK',
                'message': f"{len(at_risk)} pacientes em risco de churn",
                'priority': 'MEDIUM',
                'patients': at_risk[:5]  # Top 5 mais em risco
            })

            insights['recommendations'].append({
                'action': 'RETENTION_CAMPAIGN',
                'description': 'Executar campanha de retenção para pacientes em risco',
                'estimated_impact': 'Alta',
                'effort': 'Médio'
            })

        # 3. Previsão de receita
        revenue_prediction = self.analytics.predict_revenue_next_month()
        insights['revenue_prediction'] = revenue_prediction.get('predicted_revenue', 0)

        # 4. Insights de performance
        insights['insights'].extend(self._generate_performance_insights())

        # 5. Oportunidades identificadas
        insights['opportunities'].extend(self._identify_opportunities())

        # 6. Próximas ações recomendadas
        insights['next_actions'] = self._generate_next_actions(insights)

        return insights

    def _generate_performance_insights(self) -> List[Dict]:
        """Gera insights de performance"""
        insights = []

        # Buscar dados da semana
        week_ago = datetime.utcnow() - timedelta(days=7)

        # Agendamentos da semana
        appointments = Appointment.query.filter(
            Appointment.clinic_id == self.clinic_id,
            Appointment.created_at >= week_ago
        ).all()

        if appointments:
            completed = sum(1 for a in appointments if a.status == 'completed')
            cancelled = sum(1 for a in appointments if a.status == 'cancelled')
            no_show = sum(1 for a in appointments if a.status == 'no_show')

            completion_rate = (completed / len(appointments)) * 100 if appointments else 0

            if completion_rate < 70:
                insights.append({
                    'type': 'APPOINTMENT_COMPLETION',
                    'message': f'Taxa de conclusão de consultas está em {completion_rate:.1f}%',
                    'suggestion': 'Revisar processos de confirmação e lembretes'
                })

            if cancelled > 0:
                insights.append({
                    'type': 'CANCELLATION_RATE',
                    'message': f'{cancelled} consultas canceladas esta semana',
                    'suggestion': 'Analisar motivos e melhorar políticas'
                })

        # Novos pacientes
        new_patients = Patient.query.filter(
            Patient.clinic_id == self.clinic_id,
            Patient.created_at >= week_ago
        ).count()

        if new_patients > 0:
            insights.append({
                'type': 'NEW_PATIENTS',
                'message': f'{new_patients} novos pacientes esta semana',
                'suggestion': 'Otimizar processo de onboarding'
            })

        return insights

    def _identify_opportunities(self) -> List[Dict]:
        """Identifica oportunidades de crescimento"""
        opportunities = []

        # Buscar serviços menos utilizados
        from app.models import Service, Appointment
        services = Service.query.filter_by(clinic_id=self.clinic_id, active=True).all()

        for service in services:
            appointments_count = Appointment.query.filter_by(
                clinic_id=self.clinic_id,
                service_id=service.id
            ).count()

            if appointments_count < 5:  # Serviço subutilizado
                opportunities.append({
                    'type': 'UNDERUTILIZED_SERVICE',
                    'service': service.name,
                    'appointments': appointments_count,
                    'suggestion': f'Promover {service.name} através de campanha específica'
                })

        # Horários com baixa ocupação
        # (Implementar análise de horários)

        return opportunities

    def _generate_next_actions(self, insights: Dict) -> List[Dict]:
        """Gera próximas ações baseadas nos insights"""
        actions = []

        # Ação 1: Saúde da clínica
        if insights.get('health_score', 0) < 60:
            actions.append({
                'action': 'REVIEW_HEALTH_METRICS',
                'description': 'Revisar métricas de saúde da clínica',
                'due_date': 'HOJE',
                'owner': 'GERENTE',
                'priority': 'HIGH'
            })

        # Ação 2: Pacientes em risco
        if any(alert['type'] == 'PATIENTS_AT_RISK' for alert in insights.get('alerts', [])):
            actions.append({
                'action': 'EXECUTE_RETENTION_CAMPAIGN',
                'description': 'Executar campanha de retenção para pacientes em risco',
                'due_date': 'AMANHÃ',
                'owner': 'MARKETING',
                'priority': 'MEDIUM'
            })

        # Ação 3: Serviços subutilizados
        opportunities = insights.get('opportunities', [])
        underutilized = [o for o in opportunities if o['type'] == 'UNDERUTILIZED_SERVICE']

        if underutilized:
            actions.append({
                'action': 'PROMOTE_UNDERUTILIZED_SERVICES',
                'description': f'Promover {len(underutilized)} serviço(s) subutilizado(s)',
                'due_date': 'ESTA SEMANA',
                'owner': 'MARKETING',
                'priority': 'LOW'
            })

        return actions