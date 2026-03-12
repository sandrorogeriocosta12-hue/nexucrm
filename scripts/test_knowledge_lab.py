#!/usr/bin/env python3
"""
Script de teste para Knowledge Lab - RAG
Testa upload de PDF e queries
"""

import requests
import json
import time
from pathlib import Path

# Configuração
BASE_URL = "http://localhost:8000"
COMPANY_ID = "demo_company"


# Cores para output
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"


def print_section(title):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}{Colors.END}\n")


def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")


def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")


def print_info(msg):
    print(f"{Colors.CYAN}ℹ {msg}{Colors.END}")


def print_result(title, data):
    print(f"\n{Colors.BOLD}{title}:{Colors.END}")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def health_check():
    """Verifica saúde da API"""
    print_section("1. Health Check")
    try:
        response = requests.get(f"{BASE_URL}/api/knowledge/health")
        if response.status_code == 200:
            print_success("Knowledge Lab API está operacional")
            print_result("Status", response.json())
            return True
        else:
            print_error(f"Health check falhou: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(
            "Não conseguiu conectar à API. Certifique-se que o servidor está rodando:"
        )
        print_info("  python main.py")
        return False


def test_upload():
    """Testa upload de PDF"""
    print_section("2. Teste de Upload")

    # Criar PDF de teste
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        import io

        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)

        # Adicionar conteúdo
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, "Produto Vexus - Manual de Uso")

        c.setFont("Helvetica", 12)
        c.drawString(50, 700, "Capítulo 1: Introdução")
        c.drawString(
            50, 680, "Vexus é uma plataforma de CRM inteligente com IA integrada."
        )
        c.drawString(50, 660, "Principais características:")
        c.drawString(70, 640, "• Chat inteligente com sugestões de IA (Whisper Mode)")
        c.drawString(70, 620, "• Lead scoring automático")
        c.drawString(70, 600, "• Geração de propostas com IA")
        c.drawString(70, 580, "• Análise de padrões de venda")

        c.drawString(50, 550, "Capítulo 2: Como começar")
        c.drawString(50, 530, "1. Acesse o dashboard principal")
        c.drawString(50, 510, "2. Importe seus contatos")
        c.drawString(50, 490, "3. Configure os agentes de IA")
        c.drawString(50, 470, "4. Comece a conversar com os clientes")

        c.drawString(50, 440, "Capítulo 3: Preços")
        c.drawString(50, 420, "Plano Basic: R$ 99/mês")
        c.drawString(50, 400, "Plano Professional: R$ 299/mês")
        c.drawString(50, 380, "Plano Enterprise: Sob demanda")

        c.showPage()
        c.save()

        pdf_buffer.seek(0)

        # Fazer upload
        print_info("Enviando arquivo PDF para upload...")
        files = {"file": ("vexus_manual.pdf", pdf_buffer, "application/pdf")}
        data = {"company_id": COMPANY_ID, "doc_type": "product_manual"}

        response = requests.post(
            f"{BASE_URL}/api/knowledge/upload", files=files, data=data, timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print_success(f"Upload realizado com sucesso!")
            print_result("Resultado do Upload", result)
            return result.get("document_id")
        else:
            print_error(f"Upload falhou: {response.status_code}")
            print_result("Erro", response.json())
            return None

    except ImportError:
        print_error("reportlab não instalado. Instalando...")
        import subprocess

        subprocess.run(["pip", "install", "reportlab"], check=True)
        return test_upload()  # Tentar novamente
    except Exception as e:
        print_error(f"Erro ao criar/enviar PDF: {e}")
        return None


def test_list_documents():
    """Lista documentos indexados"""
    print_section("3. Listar Documentos")

    try:
        print_info(f"Buscando documentos da empresa: {COMPANY_ID}")
        response = requests.get(
            f"{BASE_URL}/api/knowledge/documents", params={"company_id": COMPANY_ID}
        )

        if response.status_code == 200:
            result = response.json()
            if result["total"] > 0:
                print_success(f"Total de documentos: {result['total']}")
                print_result("Documentos", result["documents"])
            else:
                print_info("Nenhum documento indexado ainda")
                print_result("Resultado", result)
            return True
        else:
            print_error(f"Erro ao listar documentos: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Erro: {e}")
        return False


def test_queries():
    """Testa RAG queries"""
    print_section("4. Testes de RAG Queries")

    test_queries_list = [
        "Quais são os principais recursos do Vexus?",
        "Qual é o preço do plano Professional?",
        "Como começar a usar o Vexus?",
        "O que é Whisper Mode?",
        "Existe API disponível?",
    ]

    results = []
    for i, query in enumerate(test_queries_list, 1):
        print_info(f"Query {i}: {query}")

        try:
            response = requests.post(
                f"{BASE_URL}/api/knowledge/query",
                json={
                    "company_id": COMPANY_ID,
                    "query": query,
                    "conversation_id": "test_conv_001",
                    "contact_id": "contact_001",
                    "top_k": 3,
                },
            )

            if response.status_code == 200:
                result = response.json()

                print_success(f"Query respondida")
                print(f"  └─ Confiança: {result['confidence']}")
                if result["source_document"]:
                    print(f"  └─ Documento: {result['source_document']}")
                print(f"  └─ Resposta: {result['response'][:100]}...")

                results.append(
                    {
                        "query": query,
                        "confidence": result["confidence"],
                        "use_kb": result["use_knowledge_base"],
                    }
                )
            else:
                print_error(f"Query falhou: {response.status_code}")

        except Exception as e:
            print_error(f"Erro ao fazer query: {e}")

        time.sleep(0.5)

    return results


def test_query_history():
    """Testa histórico de queries"""
    print_section("5. Histórico de Queries")

    try:
        response = requests.get(
            f"{BASE_URL}/api/knowledge/query-history",
            params={"company_id": COMPANY_ID, "limit": 10},
        )

        if response.status_code == 200:
            result = response.json()
            print_success(f"Total de queries no histórico: {result['total']}")

            if result["total"] > 0:
                print("\nÚltimas queries:")
                for query in result["query_history"][:5]:
                    print(f"  • {query['query']}")
                    print(f"    └─ Timestamp: {query['timestamp']}")
        else:
            print_error(f"Erro ao buscar histórico: {response.status_code}")
    except Exception as e:
        print_error(f"Erro: {e}")


def main():
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║      TESTER - Knowledge Lab (RAG) - Vexus CRM              ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")

    # Checagem de dependências
    try:
        import PyPDF2
    except ImportError:
        print_error("PyPDF2 não instalado")
        print_info("Instalando dependências...")
        import subprocess

        subprocess.run(
            ["pip", "install", "-q", "PyPDF2", "reportlab", "langchain"], check=True
        )

    # Executar testes
    if not health_check():
        print_error("\nNão é possível continuar sem a API rodando.")
        return False

    doc_id = test_upload()

    time.sleep(1)
    test_list_documents()

    time.sleep(1)
    query_results = test_queries()

    time.sleep(1)
    test_query_history()

    # Resumo
    print_section("Resumo dos Testes")
    print_success("✓ Health Check passou")
    if doc_id:
        print_success(f"✓ Upload de PDF passou (ID: {doc_id})")
    print_success(f"✓ {len(query_results)} queries testadas com sucesso")

    print(f"\n{Colors.GREEN}{Colors.BOLD}Testes concluídos!{Colors.END}\n")


if __name__ == "__main__":
    main()
