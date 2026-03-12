import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import openai
from flask import current_app

from app import db
from app.models import Clinic, ContentPost, SocialMediaAccount

logger = logging.getLogger(__name__)

class ContentGenerator:
    """Gerador de conteúdo automatizado com IA"""

    def __init__(self, clinic_id: str):
        self.clinic_id = clinic_id
        self.clinic = Clinic.query.get(clinic_id)
        openai.api_key = current_app.config.get('OPENAI_API_KEY')

    def generate_post_ideas(self, count: int = 10, theme: str = None) -> List[Dict]:
        """
        Gera ideias de posts para redes sociais
        """
        prompt = f"""
        Você é um especialista em marketing para clínicas médicas.
        Gere {count} ideias de posts para redes sociais.

        Clínica: {self.clinic.name if self.clinic else 'Clínica Médica'}
        Especialidades: Saúde e bem-estar

        Tópicos a incluir:
        - Dicas de saúde
        - Prevenção de doenças
        - Promoções de serviços
        - Educação médica
        - Bem-estar geral

        Para cada ideia, forneça:
        1. TÍTULO: (Título atrativo)
        2. CONTEÚDO: (Texto do post, 150-200 caracteres)
        3. HASHTAGS: (5-7 hashtags relevantes)
        4. TIPO: (educativo, promocional, engajamento, etc.)
        """

        if theme:
            prompt += f"\nTema específico: {theme}"

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Você é um criador de conteúdo para saúde."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            content = response.choices[0].message.content
            # Parse the response (simplified)
            ideas = []
            for i in range(min(count, 5)):  # Simplified parsing
                ideas.append({
                    "title": f"Ideia {i+1}",
                    "content": content[:200],
                    "hashtags": ["#saude", "#bemestar"],
                    "type": "educativo"
                })

            return ideas

        except Exception as e:
            logger.error(f"Erro ao gerar ideias: {str(e)}")
            return []

    def generate_post_content(self, idea: Dict, platform: str) -> Dict:
        """
        Gera conteúdo completo para um post
        """
        prompt = f"""
        Crie um post completo para {platform} baseado na ideia:

        Título: {idea.get('title', '')}
        Tipo: {idea.get('type', '')}
        Tema: {idea.get('content', '')}

        O post deve ser otimizado para {platform} e incluir emojis apropriados.
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"Você cria posts para {platform}."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=500
            )

            return {
                "content": response.choices[0].message.content,
                "hashtags": idea.get('hashtags', []),
                "platform": platform
            }

        except Exception as e:
            logger.error(f"Erro ao gerar conteúdo: {str(e)}")
            return {"content": "Conteúdo gerado", "hashtags": [], "platform": platform}

class SocialMediaManager:
    """Gerenciador de publicações em redes sociais"""

    def __init__(self):
        self.accounts = {}

    def connect_account(self, clinic_id: str, platform: str, credentials: Dict) -> bool:
        """
        Conecta uma conta de rede social
        """
        try:
            account = SocialMediaAccount(
                clinic_id=clinic_id,
                platform=platform,
                credentials=json.dumps(credentials),
                status="connected"
            )
            db.session.add(account)
            db.session.commit()

            self.accounts[f"{clinic_id}_{platform}"] = account
            return True

        except Exception as e:
            logger.error(f"Erro ao conectar conta: {str(e)}")
            return False

    def schedule_post(self, clinic_id: str, platform: str, content: Dict,
                     scheduled_time: datetime) -> bool:
        """
        Agenda um post para publicação
        """
        try:
            post = ContentPost(
                clinic_id=clinic_id,
                platform=platform,
                title=content.get('title', ''),
                content=content.get('content', ''),
                caption=content.get('content', ''),
                hashtags=json.dumps(content.get('hashtags', [])),
                scheduled_time=scheduled_time
            )
            db.session.add(post)
            db.session.commit()

            return True

        except Exception as e:
            logger.error(f"Erro ao agendar post: {str(e)}")
            return False

    def publish_post(self, post_id: str) -> bool:
        """
        Publica um post agendado
        """
        try:
            post = ContentPost.query.get(post_id)
            if not post:
                return False

            # Aqui seria integrada com APIs das redes sociais
            # (Instagram Graph API, Facebook Graph API, etc.)

            post.status = "published"
            post.published_at = datetime.utcnow()
            db.session.commit()

            return True

        except Exception as e:
            logger.error(f"Erro ao publicar post: {str(e)}")
            return False

    def get_analytics(self, clinic_id: str, platform: str, days: int = 30) -> Dict:
        """
        Retorna analytics das publicações
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            posts = ContentPost.query.filter(
                ContentPost.clinic_id == clinic_id,
                ContentPost.platform == platform,
                ContentPost.scheduled_time >= start_date
            ).all()

            analytics = {
                "total_posts": len(posts),
                "published": sum(1 for p in posts if p.status == "published"),
                "scheduled": sum(1 for p in posts if p.status == "scheduled"),
                "failed": sum(1 for p in posts if p.status == "failed"),
                "platforms": {}
            }

            # Analytics por plataforma
            for post in posts:
                if post.platform not in analytics["platforms"]:
                    analytics["platforms"][post.platform] = {
                        "posts": 0, "engagement": 0
                    }
                analytics["platforms"][post.platform]["posts"] += 1

            return analytics

        except Exception as e:
            logger.error(f"Erro ao buscar analytics: {str(e)}")
            return {"error": "Erro ao buscar analytics"}