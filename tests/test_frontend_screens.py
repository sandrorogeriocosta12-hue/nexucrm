"""
Frontend screens validation tests
Tests all main pages for proper structure and API integration
"""
import pytest
from httpx import AsyncClient
import re
from bs4 import BeautifulSoup

from app_server import app

# List of main frontend pages to test
# Frontend files are served under /frontend/ path
FRONTEND_PAGES = {
    "/frontend/index.html": "index.html",
    "/frontend/login.html": "login.html",
    "/frontend/dashboard.html": "dashboard.html",
    "/frontend/pipeline.html": "pipeline.html",
    "/frontend/contacts.html": "contacts.html",
    "/frontend/tasks.html": "tasks.html",
    "/frontend/inbox-nexus.html": "inbox-nexus.html",
}


@pytest.mark.asyncio
async def test_api_is_online():
    """Verify API root endpoint is accessible"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert "Vexus CRM API" in data["name"]
        print("✓ API root endpoint is online")


@pytest.mark.asyncio
async def test_frontend_pages_load():
    """Verify all main frontend pages load with 200 status"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        for route, description in FRONTEND_PAGES.items():
            response = await client.get(route)
            assert (
                response.status_code == 200
            ), f"Failed to load {description}: {response.status_code}"
            assert "<!DOCTYPE html>" in response.text, f"Invalid HTML: {description}"
            assert (
                len(response.text) > 100
            ), f"Page too small (likely error): {description}"
            print(f"✓ {description} loaded successfully")


@pytest.mark.asyncio
async def test_login_page_elements():
    """Verify login page has required form elements"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/frontend/login.html")
        assert response.status_code == 200

        soup = BeautifulSoup(response.text, "html.parser")

        # Check for required elements
        assert soup.find("input", {"id": "email"}), "Email input missing"
        assert soup.find("input", {"id": "password"}), "Password input missing"
        assert soup.find("form", {"id": "loginForm"}), "Login form missing"
        assert soup.find("button", {"type": "submit"}), "Submit button missing"
        assert "Nexus Service" in response.text, "Brand name missing"

        print("✓ Login page has all required form elements")


@pytest.mark.asyncio
async def test_dashboard_page_elements():
    """Verify dashboard page has main sections"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/frontend/dashboard.html")
        assert response.status_code == 200

        soup = BeautifulSoup(response.text, "html.parser")

        # Check for main navigation elements
        assert soup.find("nav"), "Navigation sidebar missing"
        assert soup.find("input", {"id": "searchInput"}), "Search input missing"

        print("✓ Dashboard page has all main sections")


@pytest.mark.asyncio
async def test_pipeline_page_structure():
    """Verify pipeline page has Kanban board structure"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/frontend/pipeline.html")
        assert response.status_code == 200

        # Check for pipeline/kanban structure
        assert "pipeline" in response.text.lower(), "Pipeline reference missing"

        soup = BeautifulSoup(response.text, "html.parser")

        # Check for navigation elements
        assert soup.find("nav"), "Navigation missing"
        assert soup.find("button"), "Action buttons missing"

        print("✓ Pipeline page has correct structure")


@pytest.mark.asyncio
async def test_contacts_page_structure():
    """Verify contacts page can display contact list"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/frontend/contacts.html")
        assert response.status_code == 200

        soup = BeautifulSoup(response.text, "html.parser")

        # Check for table or list structure
        has_table = soup.find("table") is not None
        has_list = soup.find("ul") is not None or soup.find("li") is not None
        assert (
            has_table or has_list or response.text.count("contact") > 5
        ), "No suitable contact display structure found"

        # Check for search/filter
        assert (
            soup.find("input") or "search" in response.text.lower()
        ), "No search capability found"

        print("✓ Contacts page has proper structure")


@pytest.mark.asyncio
async def test_html_validity():
    """Verify HTML pages don't have obvious syntax errors"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        for route in FRONTEND_PAGES.keys():
            response = await client.get(route)
            assert response.status_code == 200

            # Check for closing html tag
            assert "</html>" in response.text, f"Missing closing </html> in {route}"

            # Check for opening html tag
            assert "<html" in response.text, f"Missing opening <html> in {route}"

            print(f"✓ HTML validity check passed for {route}")


@pytest.mark.asyncio
async def test_responsive_design():
    """Verify pages include responsive design meta tags"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        for route in [
            "/frontend/index.html",
            "/frontend/login.html",
            "/frontend/dashboard.html",
        ]:
            response = await client.get(route)
            assert response.status_code == 200

            # Check for responsive viewport meta tag
            assert "viewport" in response.text, f"Missing viewport meta in {route}"
            assert (
                "width=device-width" in response.text
            ), f"Missing device-width viewport in {route}"

            print(f"✓ Responsive design validated for {route}")


@pytest.mark.asyncio
async def test_page_performance_indicators():
    """Verify pages load within reasonable size"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        for route, page_name in FRONTEND_PAGES.items():
            response = await client.get(route)
            assert response.status_code == 200

            size_kb = len(response.content) / 1024
            # Pages should be reasonably sized
            assert size_kb < 2048, f"{page_name} is too large: {size_kb:.2f}KB"

            # Pages should be meaningful size (at least 2KB for HTML pages)
            assert size_kb > 2, f"{page_name} is suspiciously small: {size_kb:.2f}KB"

            print(f"✓ {page_name}: {size_kb:.2f}KB")


@pytest.mark.asyncio
async def test_critical_page_content():
    """Verify critical pages have expected content"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        tests = [
            ("/frontend/index.html", ["Vexus", "Dashboard", "inbox", "pipeline"]),
            ("/frontend/login.html", ["Nexus Service", "E-mail", "Senha", "Entrar"]),
            ("/frontend/dashboard.html", ["Vexus", "Dashboard", "search"]),
        ]

        for route, expected_content in tests:
            response = await client.get(route)
            assert response.status_code == 200

            text_lower = response.text.lower()
            found = []

            for content in expected_content:
                if content.lower() in text_lower:
                    found.append(content)

            assert (
                len(found) >= len(expected_content) * 0.75
            ), f"{route}: Not enough content found"

            print(
                f"✓ {route}: Found {len(found)}/{len(expected_content)} expected items"
            )


@pytest.mark.asyncio
async def test_frontend_static_mount():
    """Verify frontend can be accessed via /frontend path"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test that specific files are accessible
        response = await client.get("/frontend/index.html")
        assert response.status_code == 200, "Frontend index.html not accessible"

        print("✓ Frontend static mount working correctly")
