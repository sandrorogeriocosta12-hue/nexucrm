"""
🚀 NEXUS SERVICE - PROSPECT TRACKING SYSTEM

Usa JSON simples pra rastrear status de leads beta.
Sem banco de dados complicado. Só edita um JSON e roda o script.

MODO DE USAR:
    python prospect_tracker.py --list              # Lista todos
    python prospect_tracker.py --add "Nome"        # Adiciona novo
    python prospect_tracker.py --update "Nome"     # Marca como "contacted"
    python prospect_tracker.py --status "Nome"     # Muda pra "call_scheduled"
    python prospect_tracker.py --convert "Nome"    # Marca como "beta_client"
    python prospect_tracker.py --report            # Relatório visual

ESTRUTURA:
- Status: new → contacted → call_scheduled → call_done → beta_client (ou rejected)
- Rastreia: Email, Celular, Nicho, Data de contato, Notas, Prioridade

OBJETIVO:
Não deixar nenhum prospect cair e saber em TEMPO REAL quem é seu beta #1, #2, #3
"""

import json
import os
from datetime import datetime
from typing import List, Dict
import argparse
from pathlib import Path


class ProspectTracker:
    def __init__(self, filepath: str = "prospects.json"):
        self.filepath = filepath
        self.prospects = self._load_prospects()

    def _load_prospects(self) -> List[Dict]:
        """Carrega JSON de prospects ou cria novo"""
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_prospects(self):
        """Salva prospects em JSON"""
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.prospects, f, indent=2, ensure_ascii=False)

    def add_prospect(
        self,
        name: str,
        email: str = "",
        phone: str = "",
        niche: str = "",
        priority: int = 5,
    ):
        """Adiciona novo prospect"""
        prospect = {
            "name": name,
            "email": email,
            "phone": phone,
            "niche": niche,
            "priority": priority,  # 1-10, onde 10 é maior prioridade
            "status": "new",  # new, contacted, call_scheduled, call_done, beta_client, rejected
            "created_at": datetime.now().isoformat(),
            "last_contact": None,
            "notes": "",
            "call_date": None,
            "call_outcome": None,
        }
        self.prospects.append(prospect)
        self._save_prospects()
        print(f"✅ Adicionado: {name}")
        return prospect

    def update_status(self, name: str, new_status: str, notes: str = ""):
        """Atualiza status de um prospect"""
        valid_statuses = [
            "new",
            "contacted",
            "call_scheduled",
            "call_done",
            "beta_client",
            "rejected",
        ]

        if new_status not in valid_statuses:
            print(f"❌ Status inválido. Use: {', '.join(valid_statuses)}")
            return

        prospect = self._find_prospect(name)
        if prospect:
            prospect["status"] = new_status
            prospect["last_contact"] = datetime.now().isoformat()
            if notes:
                prospect["notes"] = notes
            self._save_prospects()
            print(f"✅ {name} atualizado para: {new_status}")
        else:
            print(f"❌ Prospect não encontrado: {name}")

    def schedule_call(self, name: str, call_date: str):
        """Agenda call com um prospect"""
        prospect = self._find_prospect(name)
        if prospect:
            prospect["call_date"] = call_date
            prospect["status"] = "call_scheduled"
            self._save_prospects()
            print(f"✅ Call agendada para {name} em: {call_date}")
        else:
            print(f"❌ Prospect não encontrado: {name}")

    def mark_call_done(self, name: str, outcome: str, notes: str = ""):
        """Marca call como concluída"""
        prospect = self._find_prospect(name)
        if prospect:
            prospect["status"] = "call_done"
            prospect["call_outcome"] = outcome  # "positive", "neutral", "negative"
            if notes:
                prospect["notes"] = notes
            self._save_prospects()
            print(f"✅ Call done: {name} ({outcome})")
        else:
            print(f"❌ Prospect não encontrado: {name}")

    def convert_to_beta_client(self, name: str):
        """Converte prospect para beta client"""
        prospect = self._find_prospect(name)
        if prospect:
            prospect["status"] = "beta_client"
            prospect["converted_at"] = datetime.now().isoformat()
            self._save_prospects()
            print(f"🎉 {name} convertido para BETA CLIENT!")
            return prospect
        else:
            print(f"❌ Prospect não encontrado: {name}")

    def reject_prospect(self, name: str, reason: str = ""):
        """Rejeita um prospect"""
        prospect = self._find_prospect(name)
        if prospect:
            prospect["status"] = "rejected"
            if reason:
                prospect["notes"] = f"REJECTED: {reason}"
            self._save_prospects()
            print(f"❌ {name} marked as rejected")
        else:
            print(f"❌ Prospect não encontrado: {name}")

    def _find_prospect(self, name: str) -> Dict or None:
        """Encontra prospect por nome (fuzzy match)"""
        name_lower = name.lower()
        for prospect in self.prospects:
            if name_lower in prospect["name"].lower():
                return prospect
        return None

    def list_all(self):
        """Lista todos prospects com status"""
        if not self.prospects:
            print("Sem prospects ainda. Comece com --add")
            return

        print("\n" + "=" * 100)
        print(f"PROSPECTS ({len(self.prospects)} total)")
        print("=" * 100)

        # Agrupa por status
        by_status = {}
        for prospect in self.prospects:
            status = prospect["status"]
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(prospect)

        status_order = [
            "new",
            "contacted",
            "call_scheduled",
            "call_done",
            "beta_client",
            "rejected",
        ]

        for status in status_order:
            if status not in by_status:
                continue

            print(f"\n📌 {status.upper()}")
            print("-" * 100)

            for prospect in by_status[status]:
                priority_star = "⭐" * prospect["priority"]
                last_contact = (
                    prospect["last_contact"][:10]
                    if prospect["last_contact"]
                    else "nunca"
                )
                print(
                    f"  {prospect['name']:<20} | {prospect['email']:<30} | {prospect['niche']:<15} | {priority_star}"
                )
                if prospect["notes"]:
                    print(f"    └─ {prospect['notes']}")

    def show_beta_status(self):
        """Mostra quantos beta clients temos"""
        beta_clients = [p for p in self.prospects if p["status"] == "beta_client"]
        contacted = [
            p
            for p in self.prospects
            if p["status"] in ["contacted", "call_scheduled", "call_done"]
        ]

        print("\n" + "=" * 60)
        print("🎯 BETA CLIENT STATUS")
        print("=" * 60)
        print(f"Beta Clients: {len(beta_clients)}/3 ✅")
        print(f"In Pipeline: {len(contacted)} (contato já feito)")
        print(f"Total Prospects: {len(self.prospects)}")

        if beta_clients:
            print(f"\n✅ BETA CLIENTS:")
            for client in beta_clients:
                print(f"   • {client['name']} ({client['niche']})")

        if len(beta_clients) < 3:
            priority_prospects = sorted(
                [
                    p
                    for p in self.prospects
                    if p["status"] not in ["beta_client", "rejected"]
                ],
                key=lambda x: x["priority"],
                reverse=True,
            )[:5]

            print(f"\n🔥 PRÓXIMOS A CONTATOAR (top 5 por prioridade):")
            for prospect in priority_prospects:
                status_emoji = {
                    "new": "🆕",
                    "contacted": "📞",
                    "call_scheduled": "📅",
                    "call_done": "✔️",
                }
                emoji = status_emoji.get(prospect["status"], "❓")
                print(
                    f"   {emoji} {prospect['name']:<20} ({prospect['niche']:<15}) - {prospect['status']}"
                )

    def generate_call_script(self, name: str):
        """Gera script de call pra um prospect específico"""
        prospect = self._find_prospect(name)
        if not prospect:
            print(f"❌ Prospect não encontrado: {name}")
            return

        print(
            f"""
════════════════════════════════════════════════════════════════
📞 CALL SCRIPT PARA: {prospect['name'].upper()}
════════════════════════════════════════════════════════════════

CONTEXTO:
  Nome: {prospect['name']}
  Email: {prospect['email']}
  Niche: {prospect['niche']}
  Notas: {prospect['notes'] or 'N/A'}

ROTEIRO:
  Minuto 1-3: Aquecimento
    → "Oi [NOME]! Tudo bem? Você recebeu meus emails?"
    → "Rápido: como você tá vendendo agora?"
  
  Minuto 4-8: Diagnóstico
    → "Quanto tempo leva pra fazer uma proposta?"
    → "Você tá perdendo lead por falta de resposta rápida?"
    → "Qual seu maior gargalo em vendas?"
  
  Minuto 9-12: Solução (DEMO)
    → Mostrar dashboard
    → Mostrar 1 lead sendo qualificado
    → Mostrar 1 proposta automática
  
  Minuto 13-18: Proposta
    → "Topa fazer um piloto de 30 dias? Totalmente grátis."
    → "Eu configuro tudo. Você só testa e dá feedback semanal."
  
  Minuto 19-20: Fechamento
    → "Quando você quer começar? Quinta que vem?"

KEY MESSAGES:
  ✓ "Você tá perdendo 10 horas/semana em coisa que máquina faz"
  ✓ "45 segundos pra gerar uma proposta vs 2 horas manual"
  ✓ "R$ 250/mês vs R$ 2.300 da concorrência"

SAÍDAS ESPERADAS:
  Melhor: "Vamo agendar tudo agora"
  Bom: "Manda pra gente essa semana"
  Neutro: "Deixa eu pensar e te ligo"
  Pior: "Por enquanto não"
  
  💡 Sempre fechar com: "Beleza, vou mandar tudo por email."
════════════════════════════════════════════════════════════════
        """
        )


def main():
    parser = argparse.ArgumentParser(description="Prospect Tracker para Nexus Service")
    parser.add_argument("--list", action="store_true", help="Lista todos prospects")
    parser.add_argument("--report", action="store_true", help="Mostra status completo")
    parser.add_argument("--add", type=str, help="Adiciona novo prospect")
    parser.add_argument("--email", type=str, help="Email do prospect (usar com --add)")
    parser.add_argument("--phone", type=str, help="Phone do prospect (usar com --add)")
    parser.add_argument("--niche", type=str, help="Nicho do prospect (usar com --add)")
    parser.add_argument(
        "--priority", type=int, default=5, help="Prioridade 1-10 (usar com --add)"
    )
    parser.add_argument("--update", type=str, help="Nome do prospect a atualizar")
    parser.add_argument("--status", type=str, help="Novo status (usar com --update)")
    parser.add_argument("--notes", type=str, help="Notas (usar com --update)")
    parser.add_argument(
        "--schedule-call", type=str, help="Nome e data pra agendar call"
    )
    parser.add_argument("--call-date", type=str, help="Data da call (YYYY-MM-DD)")
    parser.add_argument(
        "--convert", type=str, help="Converte prospect para beta client"
    )
    parser.add_argument("--reject", type=str, help="Rejeita prospect")
    parser.add_argument("--reason", type=str, help="Razão da rejeição")
    parser.add_argument("--script", type=str, help="Gera call script pra prospect")

    args = parser.parse_args()

    tracker = ProspectTracker()

    if args.add:
        tracker.add_prospect(
            name=args.add,
            email=args.email or "",
            phone=args.phone or "",
            niche=args.niche or "",
            priority=args.priority,
        )

    elif args.list:
        tracker.list_all()

    elif args.report:
        tracker.show_beta_status()

    elif args.update and args.status:
        tracker.update_status(args.update, args.status, args.notes or "")

    elif args.schedule_call and args.call_date:
        tracker.schedule_call(args.schedule_call, args.call_date)

    elif args.convert:
        tracker.convert_to_beta_client(args.convert)

    elif args.reject:
        tracker.reject_prospect(args.reject, args.reason or "")

    elif args.script:
        tracker.generate_call_script(args.script)

    else:
        print("Modo rápido: rodando --report\n")
        tracker.show_beta_status()


if __name__ == "__main__":
    main()

# EXEMPLOS DE USO:
#
# python prospect_tracker.py --add "João Silva" --email "joao@clinica.com" --niche "Clínica Odontológica" --priority 9
# python prospect_tracker.py --update "João Silva" --status "contacted" --notes "Interesse alto, quer call amanhã"
# python prospect_tracker.py --schedule-call "João Silva" --call-date "2026-03-28 15:00"
# python prospect_tracker.py --script "João Silva"
# python prospect_tracker.py --convert "João Silva"
# python prospect_tracker.py --report
# python prospect_tracker.py --list
