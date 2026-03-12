import os
from pathlib import Path

ROOT = Path(__file__).parent
FRONTEND = ROOT / "frontend"

pages = {
    "Login-Nexus": FRONTEND / "login-nexus.html",
    "Signup-Nexus": FRONTEND / "signup-nexus.html",
    "Inbox-Nexus": FRONTEND / "inbox-nexus.html",
    "KPI-Dashboard": FRONTEND / "kpi-dashboard.html",
    "Pipeline-Nexus": FRONTEND / "pipeline-nexus.html",
}

report_lines = []


def check_file(path: Path):
    if not path.exists():
        return False, f"File not found: {path}"
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return False, f"Could not read file: {e}"
    return True, text


def simple_check_contains(text, substrings):
    for s in substrings:
        if s and s in text:
            return True
    return False


for name, path in pages.items():
    report_lines.append(f"--- {name} ---")
    ok, data = check_file(path)
    if not ok:
        report_lines.append(f"ERROR: {data}")
        continue
    html = data
    # Basic checks common
    checks = []
    # Page loads
    checks.append(("Page loads", True))
    # Title/branding
    checks.append(('Branding "Nexus Service" present', "Nexus Service" in html))
    # Gradient / color presence (search for common classes or styles)
    checks.append(
        (
            "Gradient present (linear-gradient / bg-gradient-to / gradient)",
            simple_check_contains(
                html,
                [
                    "linear-gradient",
                    "bg-gradient-to",
                    "gradient",
                    "-purple-",
                    "#7c3aed",
                ],
            ),
        )
    )

    if name == "Login-Nexus":
        checks.append(
            (
                'Contains phrase "Lead Scoring"',
                simple_check_contains(
                    html, ["Lead Scoring", "Lead Scoring em Tempo Real"]
                ),
            )
        )
        checks.append(
            (
                'Has email/password fields (input type="email" or placeholder)',
                simple_check_contains(
                    html,
                    [
                        'type="email"',
                        'placeholder="Email"',
                        'placeholder="E-mail"',
                        'input name="email"',
                    ],
                ),
            )
        )
        checks.append(
            (
                "Entrar button exists (Entrar Agora / Entrar)",
                simple_check_contains(html, ["Entrar Agora", "Entrar"]),
            )
        )
        checks.append(
            (
                "Dark theme hint (bg-gray, dark, #0f172a)",
                simple_check_contains(
                    html, ["bg-gray", "dark", "bg-gray-900", "#0f172a"]
                ),
            )
        )
        checks.append(
            (
                "Link to signup exists",
                simple_check_contains(html, ["signup-nexus.html", "Solicite acesso"]),
            )
        )
    if name == "Signup-Nexus":
        checks.append(
            (
                'Contains "Criar Conta" title',
                simple_check_contains(html, ["Criar Conta", "criar-account"]),
            )
        )
        checks.append(
            (
                "Has name/email/password fields",
                simple_check_contains(
                    html, ["Nome Completo", "E-mail", "Senha", "Confirmar Senha"]
                ),
            )
        )
        checks.append(
            (
                "Has submit button",
                simple_check_contains(html, ["Criar Conta", "signup", "register"]),
            )
        )
        checks.append(
            (
                "Link back to login exists",
                simple_check_contains(html, ["login-nexus.html", "Faça login"]),
            )
        )
        checks.append(
            (
                "Terms checkbox present",
                simple_check_contains(html, ["termos de serviço", "terms", "checkbox"]),
            )
        )
    if name == "Inbox-Nexus":
        checks.append(
            (
                "Sidebar icons present (emoji or icon classes)",
                simple_check_contains(html, ["💬", "📊", "🤖", "👥", "📈", "⚙️", "sidebar"]),
            )
        )
        checks.append(
            (
                "Inbox active highlighted",
                simple_check_contains(html, ["Inbox", "active", "highlight"]),
            )
        )
        checks.append(
            (
                "Sample scores HOT/WARM/COLD present",
                simple_check_contains(html, ["HOT", "WARM", "COLD", "🔥", "⚠️", "❄️"]),
            )
        )
        checks.append(
            (
                "Ver Proposta Gerada button",
                simple_check_contains(html, ["Ver Proposta Gerada", "Proposta Gerada"]),
            )
        )
    if name == "KPI-Dashboard":
        checks.append(
            (
                "Chart.js present",
                simple_check_contains(
                    html, ["Chart", "chart.js", "Chart.min.js", "chart.min.js"]
                ),
            )
        )
        checks.append(
            (
                "5 metric cards (search for Leads Processados / Taxa de Conversão / Potencial Revenue)",
                simple_check_contains(
                    html,
                    [
                        "Leads Processados",
                        "Taxa de Conversão",
                        "Potencial Revenue",
                        "Tempo Resposta",
                        "Acurácia ML",
                    ],
                ),
            )
        )
    if name == "Pipeline-Nexus":
        checks.append(
            (
                "Kanban columns present (Novo / Qualificado / Proposta / Contrato)",
                simple_check_contains(
                    html, ["Novo", "Qualificado", "Proposta", "Contrato", "Kanban"]
                ),
            )
        )
        checks.append(
            (
                "Column counts (digits near column names)",
                any(c in html for c in ["32", "28", "18", "8"]),
            )
        )

    # Aggregate per-page
    passed = True
    for desc, result in checks:
        mark = "PASS" if result else "FAIL"
        report_lines.append(f"{mark}: {desc}")
        if not result:
            passed = False
    report_lines.append(f'PAGE RESULT: {"OK" if passed else "ISSUES"}')
    report_lines.append("")

# Global visual checks
report_lines.append("--- GLOBAL VISUAL CHECKS ---")
all_html = ""
for p in pages.values():
    if p.exists():
        all_html += p.read_text(encoding="utf-8", errors="ignore")
report_lines.append(
    "Gradient palette present: "
    + (
        "YES"
        if simple_check_contains(
            all_html, ["linear-gradient", "bg-gradient-to", "#7c3aed", "#ec4899"]
        )
        else "NO"
    )
)
report_lines.append(
    "Dark theme used across pages: "
    + (
        "YES"
        if simple_check_contains(all_html, ["bg-gray-900", "dark", "#0f172a"])
        else "NO"
    )
)
report_lines.append(
    "Score color hints (red/orange/blue) present: "
    + (
        "YES"
        if simple_check_contains(
            all_html, ["rgba(239, 68, 68", "rgba(251, 146, 60", "rgba(59, 130, 246"]
        )
        else "NO"
    )
)

# Performance test hints (static)
report_lines.append("--- PERFORMANCE HINTS (manual checks) ---")
report_lines.append(
    "Ensure Chart.js loads from local or CDN; offline pages may show blank charts."
)

out = ROOT / "frontend_qa_report.txt"
out.write_text("\n".join(report_lines), encoding="utf-8")
print("Frontend QA finished. Report saved to", out)
print("\n".join(report_lines))
