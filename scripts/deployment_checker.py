#!/usr/bin/env python3
"""
📋 NEXUS CRM - PROFESSIONAL DEPLOYMENT CHECKLIST
This script validates all requirements before production deployment
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Tuple, List

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
CHECK = "✅"
CROSS = "❌"
WARN = "⚠️"


class DeploymentChecker:
    """Validate production deployment requirements"""
    
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def print_header(self, title: str):
        print(f"\n{BLUE}{'=' * 70}{RESET}")
        print(f"{BLUE}📋 {title}{RESET}")
        print(f"{BLUE}{'=' * 70}{RESET}\n")
    
    def check_environment_variables(self) -> bool:
        """Check if required environment variables are set"""
        self.print_header("DATABASE & CREDENTIALS")
        
        required_vars = {
            "DATABASE_URL": "PostgreSQL connection string",
            "SECRET_KEY": "Application secret key",
            "ENVIRONMENT": "Environment (production/staging/development)",
        }
        
        optional_vars = {
            "SENTRY_DSN": "Error tracking",
            "SMTP_USER": "Email service user",
            "REDIS_URL": "Cache & session storage",
            "OPENAI_API_KEY": "AI/LLM features",
        }
        
        all_good = True
        
        for var, description in required_vars.items():
            if os.getenv(var):
                print(f"{CHECK} {GREEN}{var:<25} - {description}{RESET}")
                self.passed.append(var)
            else:
                print(f"{CROSS} {RED}{var:<25} - {description} (MISSING){RESET}")
                self.failed.append(var)
                all_good = False
        
        print("\nOptional services:")
        for var, description in optional_vars.items():
            if os.getenv(var):
                print(f"{CHECK} {GREEN}{var:<25} - {description}{RESET}")
                self.passed.append(var)
            else:
                print(f"{WARN} {YELLOW}{var:<25} - {description} (not configured){RESET}")
                self.warnings.append(var)
        
        return all_good
    
    def check_dependencies(self) -> bool:
        """Check if required Python packages are installed"""
        self.print_header("PYTHON DEPENDENCIES")
        
        required_packages = [
            "fastapi",
            "uvicorn",
            "sqlalchemy",
            "psycopg2",
            "pydantic",
        ]
        
        optional_packages = [
            "sentry-sdk",
            "redis",
            "pytest",
            "black",
            "flake8",
            "prometheus-client",
        ]
        
        all_good = True
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"{CHECK} {GREEN}{package:<25} {RESET}")
                self.passed.append(package)
            except ImportError:
                print(f"{CROSS} {RED}{package:<25} (NOT INSTALLED){RESET}")
                self.failed.append(package)
                all_good = False
        
        print("\nOptional packages:")
        for package in optional_packages:
            try:
                __import__(package.replace("-", "_"))
                print(f"{CHECK} {GREEN}{package:<25} {RESET}")
                self.passed.append(package)
            except ImportError:
                print(f"{WARN} {YELLOW}{package:<25} (not installed){RESET}")
                self.warnings.append(package)
        
        return all_good
    
    def check_file_structure(self) -> bool:
        """Check if required directories and files exist"""
        self.print_header("FILE STRUCTURE")
        
        required_dirs = [
            "vexus_crm",
            "frontend",
            "scripts",
            ".github/workflows",
        ]
        
        required_files = [
            "app_server.py",
            "requirements.txt",
            "Dockerfile",
        ]
        
        all_good = True
        
        for dir_path in required_dirs:
            full_path = Path(dir_path)
            if full_path.exists():
                print(f"{CHECK} {GREEN}Directory: {dir_path}{RESET}")
                self.passed.append(dir_path)
            else:
                print(f"{CROSS} {RED}Directory: {dir_path} (MISSING){RESET}")
                self.failed.append(dir_path)
                all_good = False
        
        print()
        
        for file_path in required_files:
            full_path = Path(file_path)
            if full_path.exists():
                size = full_path.stat().st_size
                print(f"{CHECK} {GREEN}File: {file_path:<30} ({size} bytes){RESET}")
                self.passed.append(file_path)
            else:
                print(f"{CROSS} {RED}File: {file_path} (MISSING){RESET}")
                self.failed.append(file_path)
                all_good = False
        
        return all_good
    
    def check_database(self) -> bool:
        """Check database connectivity"""
        self.print_header("DATABASE CONNECTIVITY")
        
        try:
            from sqlalchemy import create_engine, text
            
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                print(f"{WARN} DATABASE_URL not set - skipping DB check")
                return False
            
            engine = create_engine(db_url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print(f"{CHECK} {GREEN}PostgreSQL connection successful{RESET}")
                print(f"{CHECK} {GREEN}Database is accessible and ready{RESET}")
                self.passed.append("Database connectivity")
                return True
        
        except Exception as e:
            print(f"{CROSS} {RED}Database connection failed: {str(e)}{RESET}")
            self.failed.append("Database connectivity")
            return False
    
    def check_docker(self) -> bool:
        """Check if Docker is available"""
        self.print_header("CONTAINERIZATION")
        
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"{CHECK} {GREEN}{result.stdout.strip()}{RESET}")
                self.passed.append("Docker")
                return True
        except Exception as e:
            print(f"{WARN} {YELLOW}Docker not available: {str(e)}{RESET}")
            self.warnings.append("Docker")
            return False
    
    def check_git(self) -> bool:
        """Check git status and commits"""
        self.print_header("VERSION CONTROL")
        
        try:
            # Check git version
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            print(f"{CHECK} {GREEN}{result.stdout.strip()}{RESET}")
            
            # Check if repo is clean
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5,
                cwd="."
            )
            
            if result.returncode == 0:
                if result.stdout.strip():
                    print(f"{WARN} {YELLOW}Uncommitted changes detected{RESET}")
                    print(result.stdout)
                else:
                    print(f"{CHECK} {GREEN}Git repository is clean{RESET}")
                self.passed.append("Git")
                return True
        except Exception as e:
            print(f"{CROSS} {RED}Git check failed: {str(e)}{RESET}")
            self.failed.append("Git")
            return False
    
    def check_api_health(self) -> bool:
        """Check if API server is running and healthy"""
        self.print_header("API HEALTH CHECK")
        
        try:
            import requests
            
            endpoints = [
                ("http://localhost:8000/health", "Health check"),
                ("http://localhost:8000/api/docs", "Swagger documentation"),
                ("http://localhost:8000/status", "Status endpoint"),
            ]
            
            for url, description in endpoints:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        print(f"{CHECK} {GREEN}{description:<30} {url}{RESET}")
                        self.passed.append(description)
                    else:
                        print(f"{WARN} {YELLOW}{description:<30} Status: {response.status_code}{RESET}")
                except requests.exceptions.ConnectionError:
                    print(f"{WARN} {YELLOW}{description:<30} Server not running at {url}{RESET}")
                    self.warnings.append(f"{description} (server offline)")
        except ImportError:
            print(f"{WARN} {YELLOW}requests library not installed - skipping health check{RESET}")
            self.warnings.append("Health check (requests not installed)")
        
        return True
    
    def check_scripts(self) -> bool:
        """Check if required scripts are executable"""
        self.print_header("AUTOMATION SCRIPTS")
        
        scripts = [
            "scripts/backup-db.sh",
            "scripts/restore-db.sh",
            "deploy.sh",
        ]
        
        all_good = True
        
        for script in scripts:
            script_path = Path(script)
            if script_path.exists():
                if os.access(script_path, os.X_OK):
                    print(f"{CHECK} {GREEN}{script:<30} (executable){RESET}")
                    self.passed.append(script)
                else:
                    print(f"{WARN} {YELLOW}{script:<30} (not executable){RESET}")
                    print(f"      Run: chmod +x {script}")
                    self.warnings.append(script)
            else:
                print(f"{WARN} {YELLOW}{script:<30} (not found){RESET}")
                self.warnings.append(script)
        
        return all_good
    
    def generate_report(self):
        """Generate deployment readiness report"""
        self.print_header("DEPLOYMENT READINESS REPORT")
        
        total_checks = len(self.passed) + len(self.failed) + len(self.warnings)
        
        print(f"{GREEN}✅ PASSED:   {len(self.passed):3d}{RESET}")
        print(f"{RED}❌ FAILED:   {len(self.failed):3d}{RESET}")
        print(f"{YELLOW}⚠️  WARNINGS: {len(self.warnings):3d}{RESET}")
        print(f"{BLUE}📋 TOTAL:    {total_checks:3d}{RESET}")
        
        if self.failed:
            print(f"\n{RED}Failed checks:{RESET}")
            for item in self.failed:
                print(f"  - {item}")
        
        if self.warnings:
            print(f"\n{YELLOW}Warnings:{RESET}")
            for item in self.warnings:
                print(f"  - {item}")
        
        # Calculate readiness percentage
        if total_checks > 0:
            readiness = (len(self.passed) / total_checks) * 100
            print(f"\n{BLUE}Production Readiness: {readiness:.1f}%{RESET}")
            
            if readiness >= 90:
                print(f"{GREEN}🚀 Ready for production deployment!{RESET}")
                return True
            elif readiness >= 70:
                print(f"{YELLOW}⚠️  Mostly ready - address warnings before deploying{RESET}")
                return False
            else:
                print(f"{RED}❌ Not ready for production - fix failed checks{RESET}")
                return False
        
        return False
    
    def run_all_checks(self) -> bool:
        """Run all deployment checks"""
        print(f"{BLUE}\n{'=' * 70}")
        print(f"🚀 NEXUS CRM - PROFESSIONAL DEPLOYMENT VALIDATION")
        print(f"{'=' * 70}{RESET}\n")
        
        checks = [
            self.check_environment_variables,
            self.check_dependencies,
            self.check_file_structure,
            self.check_database,
            self.check_docker,
            self.check_git,
            self.check_scripts,
            self.check_api_health,
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                print(f"{CROSS} {RED}Check failed: {str(e)}{RESET}")
        
        return self.generate_report()


if __name__ == "__main__":
    checker = DeploymentChecker()
    success = checker.run_all_checks()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
