"""
╔════════════════════════════════════════════════════════════════════════╗
║  ✈️  CHECKLIST DE VIAGEM - CAMPOS SEGUNDA-FEIRA                       ║
║  O que levar + o que deixar pronto                                    ║
╚════════════════════════════════════════════════════════════════════════╝
"""


def main():
    # MOCHILA / BAG
    mochila = {
        "ELETRÔNICOS": [
            ("Laptop (carregado 100%)", "⚡ CHECK"),
            ("Carregador laptop (leve versão)", "🔌 CHECK"),
            ("Smartphone (carregado 100%)", "📱 CHECK"),
            ("Carregador smartphone", "🔌 CHECK"),
            ("Power bank 20000mAh", "🔋 CHECK"),
            ("Cabos USB-C x2", "🔌 CHECK"),
            ("Adaptador HDMI (pra projetor)", "📺 CHECK"),
        ],
        "DOCUMENTOS": [
            ("RG/CPF original", "🆔 CHECK"),
            ("Contrato impresso (5 cópias)", "📄 CHECK"),
            ("Documentação digital (PDF)", "📑 CHECK"),
            ("Propostas impressas (3 cópias)", "📋 CHECK"),
            ("Business cards (100 unidades)", "🎫 CHECK"),
            ("Notas da reunião (template)", "📝 CHECK"),
        ],
        "ROUPAS / PESSOAL": [
            ("Camisa azul (profissional)", "👔 CHECK"),
            ("Calça preta (confortável)", "👖 CHECK"),
            ("Sapato sociais (testado/confortável)", "👞 CHECK"),
            ("Jaqueta leve (se frio)", "🧥 CHECK"),
            ("Meias extras x2", "🧦 CHECK"),
            ("Deodorante + perfume", "🧴 CHECK"),
            ("Gel cabelo (se necessário)", "💇 CHECK"),
        ],
        "DADOS / BACKUP": [
            ("Cópia local: stress_test.py", "💾 CHECK"),
            ("Cópia local: VEXUS_COMPLETE.md", "💾 CHECK"),
            ("Cópia local: Todos docs finais", "💾 CHECK"),
            ("Backup em Google Drive (sincronizado)", "☁️  CHECK"),
            ("Backup em Dropbox (sincronizado)", "☁️  CHECK"),
        ],
        "COMIDA / HIDRATAÇÃO": [
            ("Garrafinha água (500ml)", "💧 CHECK"),
            ("Barras de proteína x3", "🍫 CHECK"),
            ("Café instantâneo + caneca dobrável", "☕ CHECK"),
            ("Pastilha de menta (breath fresh)", "🍬 CHECK"),
        ],
        "SAÚDE / BEM-ESTAR": [
            ("Remédio dor de cabeça (dipirona)", "💊 CHECK"),
            ("Antiácido (se nervosismo)", "💊 CHECK"),
            ("Energético (Red Bull x2)", "⚡ CHECK"),
            ("Sleep aid (melatonina)", "😴 CHECK"),
        ],
    }

    # HOME PREP
    home_prep = {
        "LAPTOP SETUP": [
            ("Laptop limpo (tela + teclado)", "🧹 CHECK"),
            ("Remover stickers óbvios", "🎨 CHECK"),
            ("Desktop organizado (sem clutter)", "📂 CHECK"),
            ("Dark mode ativado (mais profissional)", "🎨 CHECK"),
            ("Volume no mute", "🔇 CHECK"),
            ("Modo Não incomodar ativado", "🚫 CHECK"),
            ("Wifi memorizado (auto-connect)", "📡 CHECK"),
        ],
        "DOCUMENTAÇÃO": [
            ("Todos PDFs salvos em Desktop", "📄 CHECK"),
            ("Screenshots de dashboards prontos", "📸 CHECK"),
            ("Links de demo salvos em navegador", "🔗 CHECK"),
            ("Versão final do contrato pronta", "📋 CHECK"),
            ("Números atualizados na caderneta", "📝 CHECK"),
        ],
        "DEMO": [
            ("Demo rodou perfeito (3x test)", "✅ CHECK"),
            ("Timing revisado (25 minutos exatos)", "⏱️  CHECK"),
            ("Backup offline pronto (se cair internet)", "💾 CHECK"),
            ("Plano B: Mostrar via smartphone", "📱 CHECK"),
        ],
        "CASA": [
            ("Pedir pra alguém regar plantas", "🌱 CHECK"),
            ("Fechar janelas", "🪟 CHECK"),
            ("Desligar fogão/luz desnecessária", "💡 CHECK"),
            ("Avisar pra família onde vai", "👨‍👩‍👧 CHECK"),
        ],
    }

    # VIAGEM
    viagem = {
        "SEGUNDA-FEIRA (CAMPOS)": [
            ("Sair com 1h antecedência", "🕐 CHECK"),
            ("Celular 100% carregado", "📱 CHECK"),
            ("Google Maps: Rota pré-carregada (offline)", "🗺️  CHECK"),
            ("Contato do gerente salvo (ligar se atraso)", "☎️  CHECK"),
            ("Chegar 10 min adiantado", "✋ CHECK"),
            ("Respirar fundo 2x (calmar)", "🧘 CHECK"),
        ],
    }

    # IMPRIMIR TUDO
    print("\n" + "=" * 70)
    print("  ✈️  CHECKLIST DE VIAGEM - CAMPOS 26/02/2026")
    print("=" * 70 + "\n")

    for section, items in mochila.items():
        print(f"\n🎒 {section}")
        print("─" * 70)
        for item, check in items:
            print(f"  [ ] {item:50} {check}")

    print("\n\n" + "=" * 70)
    print("  🏠 PRÉ-VIAGEM (DEIXAR PRONTO EM CASA)")
    print("=" * 70 + "\n")

    for section, items in home_prep.items():
        print(f"\n{section}")
        print("─" * 70)
        for item, check in items:
            print(f"  [ ] {item:50} {check}")

    print("\n\n" + "=" * 70)
    print("  🚗 DURANTE A VIAGEM")
    print("=" * 70 + "\n")

    for section, items in viagem.items():
        print(f"\n{section}")
        print("─" * 70)
        for item, check in items:
            print(f"  [ ] {item:50} {check}")

    print("\n\n" + "=" * 70)
    print("  ⏰ TIMELINE CHEGADA")
    print("=" * 70 + "\n")

    timeline = [
        ("13:30", "Sair de casa"),
        ("14:20", "Chegar no local (10 min antes)"),
        ("14:20-14:30", "Ligar laptop, testar internet"),
        ("14:25-14:30", "Ir ao banheiro (não voltar meio da reunião)"),
        ("14:30", "CEO entra"),
        ("14:30-14:32", "Apresentação + rapport (2 min)"),
        ("14:32-14:58", "Demo ao vivo (25 min)"),
        ("14:58-15:00", "Fechamento + perguntas (2 min)"),
        ("15:00", "Contrato assinado ✅"),
        ("15:02", "Foto com CEO (memória)"),
        ("15:05", "Voltar pra casa com contrato"),
    ]

    print("Horário | Ação")
    print("────────────────────────────────────────────────")
    for hora, acao in timeline:
        print(f"{hora:7} | {acao}")

    print("\n" + "=" * 70)
    print("  🎯 MINDSET PRÉ-REUNIÃO")
    print("=" * 70 + "\n")

    mindset = [
        "✅ Você estudou",
        "✅ Você preparou",
        "✅ Você testou 3x",
        "✅ O sistema é estável",
        "✅ Os números fazem sentido",
        "✅ Você merece isso",
        "",
        "🎯 ENTRE LEVE, CONFIANTE, GENUÍNO",
        "🎯 DEIXE O CEO SE IMPRESSIONAR COM A SOLUÇÃO",
        "🎯 NÃO VENDA, MOSTRE O PROBLEMA RESOLVIDO",
        "🎯 FECHE O CONTRATO ANTES DE SAIR",
    ]

    for item in mindset:
        print(f"  {item}")

    print("\n" + "=" * 70)
    print("  ✨ BOA SORTE - VOCÊ VAI CONSEGUIR")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
