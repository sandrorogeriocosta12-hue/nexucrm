# Testing Guide - Vexus CRM

## Test Suite Overview

The Vexus CRM test suite includes:
- **API Tests** ([tests/test_crm_api.py](tests/test_crm_api.py)): Async API tests using httpx
- **Interactive Browser Tests** ([tests/test_spa_interactive_fixed.py](tests/test_spa_interactive_fixed.py)): Playwright-based SPA automation

---

## Running Tests

### Full API Test Suite (Recommended)

```bash
# Run all API tests
pytest tests/test_crm_api.py -v

# Quick summary
pytest tests/test_crm_api.py -q
```

**Expected Output**: ✅ 5 passed
- `test_root_and_health` - Basic endpoint health checks
- `test_agents_list_defaults` - Default agent configuration
- `test_auth_flow` - Register → Login → Profile → Token Refresh cycle
- `test_auth_flow` - Verifies HttpOnly cookie authentication works correctly
- `test_leads_and_campaigns` - CRUD operations for leads and campaigns

### Interactive Browser Tests

The Playwright test must be run **separately** because:
1. It requires a persistent running FastAPI server
2. API tests clean/reset the database between runs, interfering with browser session state
3. Browser automation needs clean initial state

**To run interactively:**

```bash
# Terminal 1: Start the server
python app_server.py

# Terminal 2: Run the Playwright test (in separate shell)
pytest tests/test_spa_interactive_fixed.py::test_login_and_settings_flow -v --tb=short
```

**Expected Output**: ✅ 1 passed (8-10 seconds)

This test validates:
- ✅ User can create account via signup form
- ✅ User can login with credentials
- ✅ **Security Check**: No `vexus_token` in `localStorage` (tokens in HttpOnly cookies only)
- ✅ Settings page accessible after authentication
- ✅ Encrypted settings not visible in `localStorage`

---

## Key Security Validations

Both test suites validate the security improvements:

### API Tests
```python
# test_auth_flow verifies:
- Login endpoint returns tokens in HttpOnly cookies
- Token refresh endpoint maintains HttpOnly cookie state
- Settings endpoints encrypt/decrypt sensitive fields (api_key, webhook_url)
- Profile endpoint accessible only with valid authentication
```

### Browser Tests
```javascript
// test_login_and_settings_flow verifies:
- localStorage.getItem('vexus_token') === null  // Tokens not in localStorage
- localStorage.getItem('api_key') === null      // API keys not in localStorage
- localStorage.getItem('webhook_url') === null  // Webhooks not in localStorage
// Only non-sensitive data in localStorage:
- localStorage.getItem('user_email')
- localStorage.getItem('user_name')
```

---

## Test Environment Setup

### Database

Tests automatically manage the SQLite database (`vexus.db`):
- **API Tests**: Use `clean_db` fixture to reset database before each test
- **Browser Tests**: Require existing running server with persistent database

Environment variables needed:
```bash
# Required for server startup
export ENCRYPTION_KEY="<your-fernet-key>"  # See SECURITY_IMPROVEMENTS.md
```

### Dependencies

```bash
# Install test dependencies
pip install pytest playwright httpx pytest-sugar

# Install Playwright browsers
playwright install
```

---

## Continuous Integration

### GitHub Actions / CI Pipeline

Recommended setup:

```yaml
# .github/workflows/test.yml
- name: Run API Tests
  run: pytest tests/test_crm_api.py -q

# Note: Browser tests skipped in CI due to persistence requirements
# Run manually on staging environment
```

---

## Debugging Failed Tests

### API Test Failures

```bash
# Verbose output with full tracebacks
pytest tests/test_crm_api.py -v --tb=long

# Show print statements
pytest tests/test_crm_api.py -v -s

# Run specific test
pytest tests/test_crm_api.py::test_auth_flow -v
```

### Browser Test Failures

```bash
# Enable headless=False to watch browser
# (Edit test file temporarily)
browser = p.chromium.launch(headless=False)  # See the browser!

# Run test
pytest tests/test_spa_interactive_fixed.py::test_login_and_settings_flow -v -s
```

---

## Performance Benchmarks

### API Tests
- Full suite: ~1.3 seconds
- Individual test: 0.1-0.3 seconds

### Browser Tests
- Single test: 8-10 seconds
- Includes Playwright startup time

---

## Known Issues & Quirks

1. **Playwright Cookie Persistence**: HttpOnly cookies set by browser are not persisted across `page.reload()` in test environment. The test avoids this by validating state without reload.

2. **Database Cleanup**: The `clean_db` fixture in `test_crm_api.py` auto-uses `autouse=True`, meaning it runs before every test. Browser tests are skipped to avoid interference.

3. **Email Uniqueness**: Browser test uses `time.time()` in email to avoid duplicate user emails between test runs.

---

## Adding New Tests

### API Tests

```python
@pytest.mark.asyncio
async def test_new_feature():
    """Test description."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/endpoint", json={...})
        assert response.status_code == 200
        assert response.json()["field"] == "expected_value"
```

### Browser Tests

```python
def test_new_browser_feature():
    """Test description."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate and interact
        page.goto("http://localhost:8000/frontend/app.html")
        page.fill("#input-field", "value")
        page.click("#submit-button")
        
        # Assertions
        assert page.is_visible("#success-message")
        
        browser.close()
```

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Python API](https://playwright.dev/python/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/advanced/testing-dependencies/)
- [SECURITY_IMPROVEMENTS.md](SECURITY_IMPROVEMENTS.md) - Security architecture details
