# ============================================================================
# ⚙️ CONFIGURAÇÃO CENTRALIZADA - Nexus CRM
# Gerencia configurações por ambiente (desenvolvimento, staging, produção)
# ============================================================================

from .settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
