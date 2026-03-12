#!/usr/bin/env python3
"""
OWASP Top 10 Security Audit Script
"""
import os
import sys
import json
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


class SecurityAuditor:
    """OWASP Top 10 Security Auditor"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.results = {}
        self.score = 0

    def run_full_audit(self) -> Dict:
        """Run complete OWASP Top 10 audit"""
        print("🔒 INICIANDO AUDITORIA DE SEGURANÇA OWASP TOP 10")
        print("=" * 60)

        checks = [
            ("Configurações de ambiente", self.check_environment_config),
            ("Hardcoded secrets", self.check_hardcoded_secrets),
            ("Dependências vulneráveis", self.check_vulnerable_dependencies),
            ("SQL Injection", self.check_sql_injection),
            ("XSS Vulnerabilities", self.check_xss_vulnerabilities),
            ("Insecure Deserialization", self.check_insecure_deserialization),
            ("Broken Authentication", self.check_broken_authentication),
            ("Security Headers", self.check_security_headers),
            ("File Permissions", self.check_file_permissions),
            ("SSL/TLS Configuration", self.check_ssl_tls_config),
            ("API Security", self.check_api_security),
            ("Code Quality", self.check_code_quality),
            ("Dependency Scanning", self.check_dependency_scanning),
            ("Container Security", self.check_container_security),
        ]

        total_issues = 0
        for check_name, check_func in checks:
            print(f"🔍 Verificando: {check_name}")
            issues = check_func()
            self.results[check_name] = issues
            total_issues += len(issues)
            status = "✅" if len(issues) == 0 else f"⚠️  {len(issues)} issues"
            print(f"   {status}")

        # Calculate security score
        self.score = max(0, 100 - (total_issues * 5))  # Deduct 5 points per issue

        self.results["summary"] = {
            "total_issues": total_issues,
            "security_score": self.score,
            "audit_date": datetime.now().isoformat(),
            "owasp_compliance": self.score >= 80,
        }

        self.save_report()
        self.print_summary()
        return self.results

    def check_environment_config(self) -> List[str]:
        """Check environment configuration security"""
        issues = []

        # Check for debug mode in production
        if os.getenv("DEBUG", "").lower() == "true":
            issues.append("DEBUG mode enabled in production")

        # Check for weak secret keys
        secret_key = os.getenv("SECRET_KEY", "")
        if len(secret_key) < 32:
            issues.append("SECRET_KEY is too short (should be at least 32 characters)")

        # Check for default secrets
        if secret_key in ["", "your-secret-key", "default-secret-key"]:
            issues.append("Using default or empty SECRET_KEY")

        return issues

    def check_hardcoded_secrets(self) -> List[str]:
        """Check for hardcoded secrets in code"""
        issues = []
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
        ]

        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    for pattern in secret_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            issues.append(f"Potential hardcoded secret in {py_file}")
                            break
            except:
                pass

        return issues

    def check_vulnerable_dependencies(self) -> List[str]:
        """Check for vulnerable dependencies"""
        issues = []

        try:
            # Check requirements.txt
            req_file = self.project_root / "requirements.txt"
            if req_file.exists():
                with open(req_file, "r") as f:
                    deps = f.read().splitlines()

                # Check for known vulnerable versions (simplified)
                vulnerable_deps = {
                    "django": ["1.11", "2.2", "3.0", "3.1"],
                    "flask": ["0.12", "1.0", "1.1"],
                    "requests": ["2.20.0", "2.21.0"],
                }

                for dep in deps:
                    for vuln_dep, vuln_versions in vulnerable_deps.items():
                        if vuln_dep in dep.lower():
                            for vuln_ver in vuln_versions:
                                if vuln_ver in dep:
                                    issues.append(
                                        f"Vulnerable {vuln_dep} version {vuln_ver} in requirements.txt"
                                    )
        except:
            pass

        return issues

    def check_sql_injection(self) -> List[str]:
        """Check for SQL injection vulnerabilities"""
        issues = []

        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Look for dangerous SQL patterns
                dangerous_patterns = [
                    r"execute\s*\(.+\+\s*.*\)",
                    r"execute\s*\(.+format\s*\(",
                    r"execute\s*\(.+%\s*.*\)",
                    r"cursor\.execute\s*\(.+\$.+\)",
                ]

                for pattern in dangerous_patterns:
                    if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                        issues.append(
                            f"Potential SQL injection vulnerability in {py_file}"
                        )
                        break
            except:
                pass

        return issues

    def check_xss_vulnerabilities(self) -> List[str]:
        """Check for XSS vulnerabilities"""
        issues = []

        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Look for unsafe HTML rendering
                unsafe_patterns = [
                    r"render_template_string",
                    r"Markup\(.+\)",
                    r"html\.escape\s*\(\s*False\s*\)",
                ]

                for pattern in unsafe_patterns:
                    if re.search(pattern, content):
                        issues.append(f"Potential XSS vulnerability in {py_file}")
                        break
            except:
                pass

        return issues

    def check_insecure_deserialization(self) -> List[str]:
        """Check for insecure deserialization"""
        issues = []

        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Look for pickle usage
                if "pickle.loads" in content or "pickle.load" in content:
                    issues.append(f"Insecure deserialization (pickle) in {py_file}")
            except:
                pass

        return issues

    def check_broken_authentication(self) -> List[str]:
        """Check for broken authentication issues"""
        issues = []

        # Check for weak password policies
        auth_files = list(self.project_root.rglob("*auth*.py")) + list(
            self.project_root.rglob("*login*.py")
        )

        for auth_file in auth_files:
            try:
                with open(auth_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check for bcrypt usage
                if "bcrypt" not in content and "pbkdf2" not in content:
                    issues.append(f"Weak password hashing in {auth_file}")
            except:
                pass

        return issues

    def check_security_headers(self) -> List[str]:
        """Check for security headers configuration"""
        issues = []

        # Check nginx config
        nginx_conf = self.project_root / "nginx" / "nginx.conf"
        if nginx_conf.exists():
            try:
                with open(nginx_conf, "r") as f:
                    content = f.read()

                required_headers = [
                    "X-Frame-Options",
                    "X-Content-Type-Options",
                    "X-XSS-Protection",
                    "Strict-Transport-Security",
                ]

                for header in required_headers:
                    if header not in content:
                        issues.append(f"Missing security header {header} in nginx.conf")
            except:
                pass

        return issues

    def check_file_permissions(self) -> List[str]:
        """Check file permissions"""
        issues = []

        sensitive_files = ["config.py", ".env", "secrets.json", "key.pem", "cert.pem"]

        for sensitive_file in sensitive_files:
            file_path = self.project_root / sensitive_file
            if file_path.exists():
                # Check if file is world-readable
                if oct(file_path.stat().st_mode)[-1] in ["4", "5", "6", "7"]:
                    issues.append(f"File {sensitive_file} is world-readable")

        return issues

    def check_ssl_tls_config(self) -> List[str]:
        """Check SSL/TLS configuration"""
        issues = []

        # Check for SSL certificates
        cert_files = list(self.project_root.rglob("*.pem")) + list(
            self.project_root.rglob("*.crt")
        )
        if not cert_files:
            issues.append("No SSL certificates found")

        # Check docker-compose for SSL config
        docker_compose = self.project_root / "docker-compose.yml"
        if docker_compose.exists():
            try:
                with open(docker_compose, "r") as f:
                    content = f.read()
                    if "443" not in content and "ssl" not in content.lower():
                        issues.append("No SSL configuration in docker-compose.yml")
            except:
                pass

        return issues

    def check_api_security(self) -> List[str]:
        """Check API security"""
        issues = []

        # Check for API rate limiting
        api_files = list(self.project_root.rglob("*api*.py")) + list(
            self.project_root.rglob("*routes*.py")
        )

        for api_file in api_files:
            try:
                with open(api_file, "r", encoding="utf-8") as f:
                    content = f.read()

                if (
                    "rate_limit" not in content.lower()
                    and "limiter" not in content.lower()
                ):
                    issues.append(f"No rate limiting in API file {api_file}")
            except:
                pass

        return issues

    def check_code_quality(self) -> List[str]:
        """Check code quality and security issues"""
        issues = []

        total_lines = 0
        complex_functions = 0

        for py_file in self.project_root.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    total_lines += len(lines)

                    # Check function complexity (simplified)
                    in_function = False
                    brace_count = 0
                    for line in lines:
                        if re.match(r"\s*def\s+", line):
                            in_function = True
                            brace_count = 0
                        if in_function:
                            brace_count += line.count("{") - line.count("}")
                            if brace_count > 10:  # Arbitrary complexity threshold
                                complex_functions += 1
                                in_function = False
            except:
                pass

        if complex_functions > 5:
            issues.append(
                f"Too many complex functions ({complex_functions}) - potential security risk"
            )

        if total_lines > 10000:  # Large codebase
            issues.append("Large codebase - consider security code review")

        return issues

    def check_dependency_scanning(self) -> List[str]:
        """Check dependency scanning setup"""
        issues = []

        # Check for security scanning tools
        security_tools = ["safety", "bandit", "snyk", "owasp-dependency-check"]

        found_tools = False
        if (self.project_root / "requirements-dev.txt").exists():
            try:
                with open(self.project_root / "requirements-dev.txt", "r") as f:
                    content = f.read()
                    for tool in security_tools:
                        if tool in content:
                            found_tools = True
                            break
            except:
                pass

        if not found_tools:
            issues.append("No security dependency scanning tools configured")

        return issues

    def check_container_security(self) -> List[str]:
        """Check container security"""
        issues = []

        # Check Dockerfile
        dockerfile = self.project_root / "Dockerfile"
        if dockerfile.exists():
            try:
                with open(dockerfile, "r") as f:
                    content = f.read()

                # Check for root user
                if "USER root" in content or "user root" in content.lower():
                    issues.append("Container running as root user")

                # Check for latest tag
                if ":latest" in content:
                    issues.append(
                        "Using 'latest' tag in Dockerfile - not recommended for production"
                    )
            except:
                pass

        # Check docker-compose
        docker_compose_files = list(self.project_root.glob("docker-compose*.yml"))
        for dc_file in docker_compose_files:
            try:
                with open(dc_file, "r") as f:
                    content = f.read()
                    if "root" in content and "user:" in content:
                        issues.append(f"Container running as root in {dc_file}")
            except:
                pass

        return issues

    def save_report(self):
        """Save audit report to file"""
        reports_dir = self.project_root / "security-reports"
        reports_dir.mkdir(exist_ok=True)

        report_file = (
            reports_dir
            / f"security_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n📄 Relatório salvo em: {report_file}")

    def print_summary(self):
        """Print audit summary"""
        print("\n" + "=" * 60)
        print("📊 RESULTADO DA AUDITORIA DE SEGURANÇA")
        print("=" * 60)

        total_issues = self.results["summary"]["total_issues"]
        score = self.results["summary"]["security_score"]

        print(f"🔍 Total de problemas encontrados: {total_issues}")
        print(f"📊 SCORE DE SEGURANÇA: {score}/100")

        if score >= 90:
            print("🎉 Excelente! Segurança muito boa")
        elif score >= 80:
            print("✅ Boa segurança - algumas melhorias recomendadas")
        elif score >= 70:
            print("⚠️ Segurança adequada - melhorias necessárias")
        else:
            print("🚨 Segurança crítica - ação imediata necessária")

        print(f"📄 Relatórios gerados: security-reports/")


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="OWASP Top 10 Security Audit")
    parser.add_argument("--quick", action="store_true", help="Run quick audit")
    parser.add_argument("--path", default=".", help="Project root path")

    args = parser.parse_args()

    auditor = SecurityAuditor(args.path)

    if args.quick:
        # Quick audit - only critical checks
        print("🔍 Executando auditoria rápida...")
        results = auditor.run_full_audit()
    else:
        results = auditor.run_full_audit()


if __name__ == "__main__":
    main()
