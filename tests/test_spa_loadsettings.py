import pathlib


def test_load_user_settings_present():
    """Verifica que o frontend contém a função loadUserSettings e campos esperados."""
    p = pathlib.Path("frontend/app.html")
    assert p.exists(), "frontend/app.html não encontrado"
    text = p.read_text(encoding="utf-8")

    # função de carregamento assíncrona
    assert "async function loadUserSettings" in text

    # campos de configuração adicionados recentemente
    assert "settings-whatsapp" in text
    assert "settings-ai-provider" in text
    assert "settings-whatsapp-test-btn" in text
