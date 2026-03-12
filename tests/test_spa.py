"""
Test suite for SPA (Single Page App) functionality
Validates app.html can be loaded and interacted with via JavaScript routing
"""

import json

import pytest
import requests
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:8000"


class TestSPAApp:
    """Test the Single Page App (app.html) functionality"""

    def test_spa_app_loads(self):
        """Verify app.html is served correctly"""
        response = requests.get(f"{BASE_URL}/frontend/app.html")
        assert response.status_code == 200
        assert "Vexus CRM" in response.text
        assert "Sistema Integrado" in response.text

    def test_spa_contains_sidebar(self):
        """Verify sidebar navigation is present"""
        response = requests.get(f"{BASE_URL}/frontend/app.html")
        soup = BeautifulSoup(response.text, "html.parser")

        # Check sidebar exists
        sidebar = soup.find("nav", {"id": "sidebar"})
        assert sidebar is not None

        # Check navigation buttons for each page
        nav_buttons = sidebar.find_all("button", {"class": "nav-btn"})
        assert len(nav_buttons) >= 6  # dashboard, pipeline, contacts, tasks, inbox, kb

        # Verify data-page attributes
        pages = [btn.get("data-page") for btn in nav_buttons]
        assert "dashboard" in pages
        assert "pipeline" in pages
        assert "proposals" in pages
        assert "campaigns" in pages
        assert "contacts" in pages
        assert "tasks" in pages
        assert "inbox" in pages
        assert "kb" in pages

    def test_spa_contains_all_templates(self):
        """Verify all page templates are embedded in HTML"""
        response = requests.get(f"{BASE_URL}/frontend/app.html")
        soup = BeautifulSoup(response.text, "html.parser")

        # Check for template elements
        templates = soup.find_all("template")
        template_ids = [t.get("id") for t in templates]

        assert "dashboard-template" in template_ids
        assert "pipeline-template" in template_ids
        assert "proposals-template" in template_ids
        assert "campaigns-template" in template_ids
        assert "contacts-template" in template_ids
        assert "tasks-template" in template_ids
        assert "inbox-template" in template_ids
        assert "kb-template" in template_ids
        assert "settings-template" in template_ids

    def test_spa_contains_router_script(self):
        """Verify the JavaScript router code is present"""
        response = requests.get(f"{BASE_URL}/frontend/app.html")

        # Check for router functions
        assert "function navigate(pageName)" in response.text
        assert "function renderPage(pageName)" in response.text
        assert "window.history.pushState" in response.text  # For URL history
        assert "DOMContentLoaded" in response.text  # For event listeners
        # showApp should hide signup and plan screens
        assert "signup-screen" in response.text and "plan-screen" in response.text
        assert "classList.add('hidden')" in response.text

    def test_spa_header_elements(self):
        """Verify header contains search and user elements"""
        response = requests.get(f"{BASE_URL}/frontend/app.html")
        soup = BeautifulSoup(response.text, "html.parser")

        # Check header
        header = soup.find("header")
        assert header is not None

        # Check page title element
        assert soup.find("h1", {"id": "page-title"}) is not None
        assert soup.find("span", {"id": "page-description"}) is not None

        # Check search input
        search = soup.find("input", {"id": "global-search"})
        assert search is not None
        assert "Buscar" in search.get("placeholder", "")

    def test_spa_dashboard_content(self):
        """Verify dashboard template has KPI cards"""
        response = requests.get(f"{BASE_URL}/frontend/app.html")
        soup = BeautifulSoup(response.text, "html.parser")

        dashboard_template = soup.find("template", {"id": "dashboard-template"})
        assert dashboard_template is not None

        template_html = str(dashboard_template)
        assert "Leads Abertos" in template_html
        assert "Conversões" in template_html
        assert "Revenue" in template_html
        assert "Taxa Sucesso" in template_html

    def test_spa_pipeline_content(self):
        """Verify pipeline template has kanban columns"""
        response = requests.get(f"{BASE_URL}/frontend/app.html")
        soup = BeautifulSoup(response.text, "html.parser")

        pipeline_template = soup.find("template", {"id": "pipeline-template"})
        assert pipeline_template is not None

        template_html = str(pipeline_template)
        assert "Prospecção" in template_html
        assert "Qualificação" in template_html
        assert "Proposta" in template_html
        assert "Fechado" in template_html

    def test_spa_proposals_template(self):
        """Ensure proposals template exists with new proposal button"""
        response = requests.get(f"{BASE_URL}/frontend/app.html")
        soup = BeautifulSoup(response.text, "html.parser")
        prop = soup.find("template", {"id": "proposals-template"})
        assert prop is not None
        assert "Nova Proposta" in prop.text or "+ Nova Proposta" in prop.text
        assert "openNewProposalModal" in response.text

    def test_spa_campaigns_template(self):
        """Ensure campaigns template exists with new campaign button"""
        response = requests.get(f"{BASE_URL}/frontend/app.html")
        soup = BeautifulSoup(response.text, "html.parser")
        camp = soup.find("template", {"id": "campaigns-template"})
        assert camp is not None
        assert "Nova Campanha" in camp.text or "+ Nova Campanha" in camp.text
        assert "openNewCampaignModal" in response.text

    def test_spa_contacts_content(self):
        """Verify contacts template has table structure"""
        response = requests.get(f"{BASE_URL}/frontend/app.html")
        soup = BeautifulSoup(response.text, "html.parser")

        contacts_template = soup.find("template", {"id": "contacts-template"})
        assert contacts_template is not None

        template_html = str(contacts_template)
        assert "<table" in template_html
        assert "Nome" in template_html
        assert "Email" in template_html
        assert "Empresa" in template_html

    def test_spa_responsive_design(self):
        """Verify responsive design classes are present"""
        response = requests.get(f"{BASE_URL}/frontend/app.html")

        # Check for Tailwind classes indicating responsive design
        assert "grid-cols-" in response.text  # Grid layouts
        assert (
            "grid-cols-3" in response.text or "grid-cols-4" in response.text
        )  # Multi-column layouts
        assert "flex" in response.text  # Flexbox layouts
        assert "overflow" in response.text  # Responsive overflow behavior
        assert (
            "h-screen" in response.text or "w-full" in response.text
        )  # Full viewport sizing

    def test_spa_logout_functionality(self):
        """Verify logout button is present and functional"""
        response = requests.get(f"{BASE_URL}/frontend/app.html")
        soup = BeautifulSoup(response.text, "html.parser")

        logout_btn = soup.find(id="logoutBtn")
        assert logout_btn is not None

        html_text = str(response.text)
        assert "localStorage.removeItem" in html_text
        assert "vexus_token" in html_text

    def test_spa_keyboard_shortcuts(self):
        """Verify keyboard shortcuts are implemented"""
        response = requests.get(f"{BASE_URL}/frontend/app.html")

        # Check for keyboard event listeners
        assert "keydown" in response.text
        assert "Ctrl" in response.text or "metaKey" in response.text
        assert "shortcut" in response.text.lower()

    def test_spa_integration_with_api(self):
        """Verify that API endpoints are accessible from SPA"""
        # Just verify the API is still responding while SPA is running
        response = requests.get(f"{BASE_URL}/api/knowledge/health")
        assert response.status_code == 200

        # Verify other API endpoints
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "online"

    def test_spa_loading_indicator(self):
        """Verify loading indicator HTML is present"""
        response = requests.get(f"{BASE_URL}/frontend/app.html")

        assert "loading-indicator" in response.text
        assert "animate-spin" in response.text  # Tailwind spinner animation

    def test_spa_structure_valid_html(self):
        """Verify overall HTML structure is valid"""
        response = requests.get(f"{BASE_URL}/frontend/app.html")
        soup = BeautifulSoup(response.text, "html.parser")

        # Check main structure
        assert soup.find("html") is not None
        assert soup.find("head") is not None
        assert soup.find("body") is not None

        # Check app container
        app_container = soup.find("div", {"id": "app-container"})
        assert app_container is not None

        # Check main content area
        page_content = soup.find("main", {"id": "page-content"})
        assert page_content is not None

    def test_spa_signup_and_plan_elements(self):
        """Ensure signup and plan selection screens exist with required fields"""
        response = requests.get(f"{BASE_URL}/frontend/app.html")
        text = response.text
        soup = BeautifulSoup(text, "html.parser")

        # Signup screen elements
        signup = soup.find("div", {"id": "signup-screen"})
        assert signup is not None, "Signup screen missing"
        assert signup.find("input", {"id": "signup-name"}) is not None
        assert signup.find("input", {"id": "signup-email"}) is not None
        assert signup.find("input", {"id": "signup-password"}) is not None
        assert signup.find("input", {"id": "signup-confirm"}) is not None
        assert "handleSignup" in text, "JS handler for signup not found"

        # Plan screen elements
        plan = soup.find("div", {"id": "plan-screen"})
        assert plan is not None, "Plan screen missing"
        # check three plan cards by title
        assert "Starter" in plan.text
        assert "Professional" in plan.text
        assert "Premium" in plan.text
        assert "selectPlan" in text, "JS handler for plan selection not found"

        # Demo path
        assert "skipPlanDemo" in text, "Demo button handler not found"

    def test_spa_settings_fields_editable(self):
        """Verify settings screen contains editable fields for channels and profile"""
        response = requests.get(f"{BASE_URL}/frontend/app.html")
        soup = BeautifulSoup(response.text, "html.parser")

        settings = soup.find("template", {"id": "settings-template"})
        assert settings is not None, "Settings template missing"
        template_html = str(settings)
        # check for channel inputs
        assert 'id="settings-whatsapp"' in template_html
        assert 'id="settings-instagram"' in template_html
        assert 'id="settings-email-smtp"' in template_html
        assert 'id="settings-phone"' in template_html
        # whatsapp/ai keys should be password fields with toggle buttons
        assert 'id="settings-whatsapp-api-key"' in template_html
        assert 'id="settings-ai-api-key"' in template_html
        assert 'type="password"' in template_html
        assert "togglePassword" in response.text, "toggle helper missing"
        assert "saveUserSettings" in response.text
        assert "loadUserSettings" in response.text
        # verify settings save uses authenticated endpoint
        assert "/api/auth/users/settings" in response.text
        # ensure loadUserSettings fetches server data
        assert (
            "fetch('/api/auth/users/settings'" in response.text
            or 'fetch("/api/auth/users/settings"' in response.text
        )

    def test_spa_colors_and_theming(self):
        """Verify dark theme and color styling"""
        response = requests.get(f"{BASE_URL}/frontend/app.html")

        # Check for dark theme colors
        assert "slate-900" in response.text
        assert "slate-800" in response.text

        # Check for accent colors
        assert "purple" in response.text
        assert "pink" in response.text
        assert "gradient" in response.text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
