"""
Proposal Generator Agent - Gera propostas automáticas a partir de conversas
"""
import logging
import time
import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from .proposal_models import ProposalRequest, ProposalData, LineItem, ProposalStatus

logger = logging.getLogger(__name__)


class ProposalGeneratorAgent:
    """Agent que gera propostas automáticas a partir de análise de conversas"""
    
    def __init__(self):
        """Inicializa agent com DB em memória e catálogo de produtos"""
        self.proposals_db: Dict[str, ProposalData] = {}
        self.stats = {
            "total_generated": 0,
            "total_sent": 0,
            "total_viewed": 0,
            "generation_times": []
        }
        
        # Catálogo de produtos de exemplo
        self.products_catalog = [
            {"id": "prod_001", "name": "Consultoria Estratégica", "price": 5000.00, "description": "3 meses de consultoria"},
            {"id": "prod_002", "name": "Implementação", "price": 15000.00, "description": "Implementação completa"},
            {"id": "prod_003", "name": "Suporte Premium", "price": 2000.00, "description": "Suporte 24/7 por 30 dias"},
            {"id": "prod_004", "name": "Treinamento", "price": 3000.00, "description": "Treinamento da equipe"},
            {"id": "prod_005", "name": "Manutenção Anual", "price": 8000.00, "description": "Manutenção e suporte anual"},
        ]
    
    async def analyze_conversation(
        self,
        messages: List[Dict],
        contact_data: Dict
    ) -> Tuple[bool, Optional[ProposalRequest]]:
        """
        Analisa conversa para detectar solicitação de proposta.
        
        Args:
            messages: Lista de mensagens [{"sender": "...", "content": "..."}]
            contact_data: {"id", "name", "email", "phone", "company"}
        
        Returns:
            (has_proposal_request, ProposalRequest ou None)
        """
        logger.info(f"Analisando conversa para proposta: {contact_data.get('name')}")
        
        # Palavras-chave para detectar solicitação de proposta
        proposal_keywords = [
            "proposta", "orçamento", "quanto custa", "preço", "cotação",
            "qual o valor", "tabela de preços", "quero comprar", 
            "estou interessado", "preciso de", "quantas unidades",
            "unidades do", "produto"
        ]
        
        # Buscar mensagens do cliente (não 'bot')
        client_messages = [m for m in messages if m.get('sender') in ['cliente', 'client', 'user', 'customer']]
        if not client_messages:
            return False, None
        
        # Juntar últimas 2 mensagens do cliente
        last_messages = ' '.join([m['content'] for m in client_messages[-2:]])
        search_text = last_messages.lower()
        
        # Detectar keywords
        has_proposal_request = any(
            keyword in search_text 
            for keyword in proposal_keywords
        )
        
        if not has_proposal_request:
            logger.debug(f"Nenhuma solicitação de proposta detectada")
            return False, None
        
        # Extrair informações
        logger.info(f"✅ Solicitação de proposta detectada")
        
        try:
            # Simulação de extração (em produção, usaria NLU)
            extraction = self._extract_proposal_data(search_text, client_messages)
            
            # Montar itens
            line_items = []
            for product_name in extraction['products']:
                product = self._find_product_by_name(product_name)
                if product:
                    qty = extraction.get('quantities', {}).get(product_name, 1)
                    line_items.append(LineItem(
                        product_id=product['id'],
                        product_name=product['name'],
                        description=product.get('description', ''),
                        quantity=int(qty),
                        unit_price=product['price'],
                        discount_percent=extraction.get('discount', 0)
                    ))
            
            if not line_items:
                # Se não encontrou produtos, usar o primeiro do catálogo
                product = self.products_catalog[0]
                line_items.append(LineItem(
                    product_id=product['id'],
                    product_name=product['name'],
                    description=product.get('description', ''),
                    quantity=1,
                    unit_price=product['price'],
                    discount_percent=0
                ))
            
            # Montar requisição
            proposal_req = ProposalRequest(
                contact_id=contact_data['id'],
                contact_name=contact_data.get('name', 'Cliente'),
                contact_email=contact_data.get('email', ''),
                contact_phone=contact_data.get('phone', ''),
                company_name=contact_data.get('company'),
                line_items=line_items,
                valid_until_days=extraction.get('valid_days', 7),
                payment_terms=extraction.get('payment_terms', '30'),
                message_context=' | '.join([m['content'][:100] for m in client_messages[-3:]])
            )
            
            return True, proposal_req
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados: {e}")
            return True, None
    
    async def generate(
        self,
        proposal_request: ProposalRequest
    ) -> Optional[ProposalData]:
        """
        Gera proposta com PDF.
        
        Returns:
            ProposalData ou None
        """
        start_time = time.time()
        logger.info(f"Gerando proposta para: {proposal_request.contact_name}")
        
        try:
            # 1. Criar objeto proposta
            proposal = ProposalData(
                request=proposal_request,
                subtotal=0,
                tax_amount=0,
                total=0,
                pdf_url="",
                pdf_filename=""
            )
            
            # 2. Calcular totais
            proposal.calculate_totals(tax_percent=0)  # Sem imposto por padrão
            
            # 3. Simular PDF (em produção: gerar PDF real)
            proposal.pdf_filename = f"PROP_{proposal.id[:8]}.pdf"
            proposal.pdf_url = f"https://s3.amazonaws.com/vexus-proposals/{proposal.pdf_filename}"
            proposal.status = ProposalStatus.DRAFT
            
            # 4. Armazenar em DB
            self.proposals_db[proposal.id] = proposal
            self.stats["total_generated"] += 1
            self.stats["generation_times"].append(time.time() - start_time)
            
            logger.info(f"✅ Proposta gerada: {proposal.id} | Total: R${proposal.total:,.2f}")
            return proposal
            
        except Exception as e:
            logger.error(f"Erro ao gerar proposta: {e}")
            return None
    
    async def send_proposal(
        self,
        proposal_id: str,
        channel: str = "whatsapp"
    ) -> bool:
        """
        Envia proposta para cliente via WhatsApp/Email
        
        Args:
            proposal_id: ID da proposta
            channel: "whatsapp" ou "email"
        """
        proposal = self.proposals_db.get(proposal_id)
        if not proposal:
            logger.error(f"Proposta {proposal_id} não encontrada")
            return False
        
        logger.info(f"Enviando proposta via {channel}...")
        
        try:
            # Marcar como enviada
            proposal.status = ProposalStatus.SENT
            proposal.sent_at = datetime.now()
            
            # Formatar mensagem
            message = self._format_proposal_message(proposal)
            
            # Em produção: integrar com Twilio (WhatsApp) ou SendGrid (Email)
            if channel == "whatsapp":
                logger.info(f"📱 WhatsApp → {proposal.request.contact_phone}")
            else:
                logger.info(f"📧 Email → {proposal.request.contact_email}")
            
            self.stats["total_sent"] += 1
            logger.info(f"✅ Proposta enviada com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar proposta: {e}")
            return False
    
    async def track_view(self, proposal_id: str) -> bool:
        """Registra visualização da proposta"""
        proposal = self.proposals_db.get(proposal_id)
        if not proposal:
            return False
        
        proposal.viewed_count += 1
        proposal.status = ProposalStatus.VIEWED
        proposal.viewed_at = datetime.now()
        self.stats["total_viewed"] += 1
        
        logger.info(f"👁️ Proposta {proposal_id} visualizada ({proposal.viewed_count}x)")
        return True
    
    def get_proposal(self, proposal_id: str) -> Optional[ProposalData]:
        """Recupera proposta por ID"""
        return self.proposals_db.get(proposal_id)
    
    def list_proposals(self, contact_id: str = None, status: ProposalStatus = None) -> List[ProposalData]:
        """Lista propostas com filtros opcionais"""
        proposals = list(self.proposals_db.values())
        
        if contact_id:
            proposals = [p for p in proposals if p.request.contact_id == contact_id]
        
        if status:
            proposals = [p for p in proposals if p.status == status]
        
        return sorted(proposals, key=lambda p: p.created_at, reverse=True)
    
    def get_analytics(self) -> Dict:
        """Retorna analytics de propostas"""
        total_gen = self.stats["total_generated"]
        total_sent = self.stats["total_sent"]
        total_viewed = self.stats["total_viewed"]
        
        return {
            "total_generated": total_gen,
            "total_sent": total_sent,
            "total_viewed": total_viewed,
            "send_rate": (total_sent / total_gen * 100) if total_gen > 0 else 0,
            "view_rate": (total_viewed / total_sent * 100) if total_sent > 0 else 0,
            "avg_generation_time_ms": (sum(self.stats["generation_times"]) / len(self.stats["generation_times"]) * 1000) if self.stats["generation_times"] else 0
        }
    
    def _extract_proposal_data(self, search_text: str, messages: List[Dict]) -> Dict:
        """
        Extrai dados de proposta do texto via regex
        
        Returns:
            {"products": [...], "quantities": {...}, "discount": 0, "valid_days": 7, ...}
        """
        import re
        
        extraction = {
            "products": [],
            "quantities": {},
            "discount": 0,
            "valid_days": 7,
            "payment_terms": "30"
        }
        
        # Buscar referências a produtos
        for product in self.products_catalog:
            if product['name'].lower() in search_text:
                extraction["products"].append(product['name'])
        
        # Se não encontrou, procurar por "Produto X" genérico
        if not extraction["products"]:
            if "produto" in search_text:
                # Pegar o primeiro produto como fallback
                extraction["products"].append(self.products_catalog[0]['name'])
        
        # Extrair quantidade (ex: "50 unidades", "quantidade 100")
        qty_pattern = r'(\d+)\s*(?:unidades?|qty|quantidade)'
        qty_match = re.search(qty_pattern, search_text, re.IGNORECASE)
        if qty_match:
            qty = int(qty_match.group(1))
            for product in extraction["products"]:
                extraction["quantities"][product] = qty
        
        # Extrair desconto
        disc_pattern = r'(\d+)\s*%\s*(?:desc|desconto|off)'
        disc_match = re.search(disc_pattern, search_text, re.IGNORECASE)
        if disc_match:
            extraction["discount"] = int(disc_match.group(1))
        
        # Extrair validade (ex: "válido por 30 dias")
        valid_pattern = r'(?:válido|válida)\s*(?:por|ate|até)\s*(\d+)\s*(?:dia|dias)'
        valid_match = re.search(valid_pattern, search_text, re.IGNORECASE)
        if valid_match:
            extraction["valid_days"] = int(valid_match.group(1))
        
        return extraction
    
    def _find_product_by_name(self, product_name: str) -> Optional[Dict]:
        """Encontra produto no catálogo"""
        product_name = product_name.lower()
        for product in self.products_catalog:
            if product_name in product['name'].lower() or product['name'].lower() in product_name:
                return product
        return None
    
    def _format_proposal_message(self, proposal: ProposalData) -> str:
        """Formata mensagem da proposta"""
        msg = f"""
🎯 PROPOSTA #{proposal.id[:8]}

Olá {proposal.request.contact_name}!

Segue sua proposta com os seguintes itens:

"""
        for item in proposal.request.line_items:
            msg += f"✓ {item.product_name} - {item.quantity}x R${item.unit_price:,.2f}\n"
        
        msg += f"""
{'─' * 50}
Total: R${proposal.total:,.2f}
Válida até: {(proposal.created_at + timedelta(days=proposal.request.valid_until_days)).strftime('%d/%m/%Y')}

🔗 Visualizar: {proposal.pdf_url}
"""
        return msg
