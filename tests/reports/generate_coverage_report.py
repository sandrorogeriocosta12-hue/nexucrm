#!/usr/bin/env python3
"""
Script para gerar relatórios de cobertura e testes
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

def generate_test_report():
"""Gera relatório consolidado de testes"""
report_dir = Path("test-reports")
report_dir.mkdir(exist_ok=True)

# Lê dados do coverage
coverage_data = {}
coverage_file = report_dir / "coverage.xml"

if coverage_file.exists():
tree = ET.parse(coverage_file)
root = tree.getroot()

# Extrai métricas do coverage
packages = root.findall(".//package")
total_lines = 0
covered_lines = 0

for package in packages:
metrics = package.find("metrics")
total_lines += int(metrics.get("statements", 0))
covered_lines += int(metrics.get("coveredstatements", 0))

coverage_percent = (covered_lines / total_lines * 100) if total_lines > 0 else 0

coverage_data = {
"total_lines": total_lines,
"covered_lines": covered_lines,
"coverage_percent": round(coverage_percent, 2)
}

# Lê dados do JUnit XML
junit_file = report_dir / "junit.xml"
test_results = {}

if junit_file.exists():
tree = ET.parse(junit_file)
root = tree.getroot()

test_suites = root.findall(".//testsuite")

total_tests = 0
total_failures = 0
total_errors = 0
total_time = 0

for suite in test_suites:
total_tests += int(suite.get("tests", 0))
total_failures += int(suite.get("failures", 0))
total_errors += int(suite.get("errors", 0))
total_time += float(suite.get("time", 0))

test_results = {
"total_tests": total_tests,
"passed": total_tests - total_failures - total_errors,
"failures": total_failures,
"errors": total_errors,
"total_time": round(total_time, 2),
"success_rate": round((total_tests - total_failures - total_errors) / total_tests * 100, 2) if total_tests > 0 else 0
}

# Gera relatório consolidado
consolidated_report = {
"generated_at": datetime.utcnow().isoformat(),
"project": "Vexus Service",
"test_results": test_results,
"coverage": coverage_data,
"quality_gates": {
"minimum_coverage": 80.0,
"minimum_success_rate": 95.0,
"maximum_test_time": 300.0 # 5 minutos
},
"passed_quality_gates": (
coverage_data.get("coverage_percent", 0) >= 80.0 and
test_results.get("success_rate", 0) >= 95.0 and
test_results.get("total_time", 0) <= 300.0
)
}

# Salva relatório
report_file = report_dir / "consolidated_report.json"
with open(report_file, "w") as f:
json.dump(consolidated_report, f, indent=2)

# Gera relatório em markdown
markdown_report = report_dir / "TEST_REPORT.md"
with open(markdown_report, "w") as f:
f.write("# Test Report - Vexus Service\n\n")
f.write(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")

f.write("## Test Results\n\n")
f.write(f"- **Total Tests:** {test_results.get('total_tests', 0)}\n")
f.write(f"- **Passed:** {test_results.get('passed', 0)}\n")
f.write(f"- **Failures:** {test_results.get('failures', 0)}\n")
f.write(f"- **Errors:** {test_results.get('errors', 0)}\n")
f.write(f"- **Success Rate:** {test_results.get('success_rate', 0)}%\n")
f.write(f"- **Total Time:** {test_results.get('total_time', 0)}s\n\n")

f.write("## Code Coverage\n\n")
f.write(f"- **Total Lines:** {coverage_data.get('total_lines', 0)}\n")
f.write(f"- **Covered Lines:** {coverage_data.get('covered_lines', 0)}\n")
f.write(f"- **Coverage:** {coverage_data.get('coverage_percent', 0)}%\n\n")

f.write("## Quality Gates\n\n")
f.write(f"- **Minimum Coverage (80%):** {'✅ PASS' if coverage_data.get('coverage_percent', 0) >= 80.0 else '❌ FAIL'}\n")
f.write(f"- **Minimum Success Rate (95%):** {'✅ PASS' if test_results.get('success_rate', 0) >= 95.0 else '❌ FAIL'}\n")
f.write(f"- **Maximum Test Time (300s):** {'✅ PASS' if test_results.get('total_time', 0) <= 300.0 else '❌ FAIL'}\n\n")

f.write(f"**Overall Result:** {'✅ ALL TESTS PASSED' if consolidated_report['passed_quality_gates'] else '❌ TESTS FAILED'}\n")

print(f"✅ Relatórios gerados em {report_dir}/")
print(f" - consolidated_report.json")
print(f" - TEST_REPORT.md")

return consolidated_report

if __name__ == "__main__":
report = generate_test_report()

# Exibe resumo no console
print("\n" + "="*50)
print("TEST REPORT SUMMARY")
print("="*50)
print(f"Tests: {report['test_results'].get('passed', 0)}/{report['test_results'].get('total_tests', 0)} passed")
print(f"Coverage: {report['coverage'].get('coverage_percent', 0)}%")
print(f"Quality Gates: {'PASS' if report['passed_quality_gates'] else 'FAIL'}")
print("="*50)