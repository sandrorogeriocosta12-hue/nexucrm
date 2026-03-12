from pathlib import Path
import json
from typing import Any, Dict, Optional

CONFIG_DIR = Path(__file__).parent / "configs"
CONFIG_DIR.mkdir(exist_ok=True)

AI_CONFIG_FILE = CONFIG_DIR / "ai_config.json"


def read_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        write_json(path, default)
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def write_json(path: Path, data: Dict[str, Any]):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Runtime references (set by main on startup)
orchestrator = None
omnichannel = None


def set_orchestrator(obj: Any):
    global orchestrator
    orchestrator = obj


def set_omnichannel(obj: Any):
    global omnichannel
    omnichannel = obj


def apply_agent_config(agent_name: str, config: Dict[str, Any]):
    """Apply agent config to runtime orchestrator if available."""
    if orchestrator is None:
        return False

    try:
        # Expect orchestrator.agents to be a dict-like mapping
        agents = getattr(orchestrator, "agents", None)
        if not agents:
            return False

        # If agent exists, try to update its config attributes
        agent = agents.get(agent_name) or agents.get(agent_name.upper())
        if agent:
            # best-effort: set a .config attribute or update settings dict
            if hasattr(agent, "config"):
                agent_cfg = getattr(agent, "config")
                if isinstance(agent_cfg, dict):
                    agent_cfg.update(config)
                else:
                    try:
                        for k, v in config.items():
                            setattr(agent_cfg, k, v)
                    except Exception:
                        pass
            else:
                try:
                    for k, v in config.items():
                        setattr(agent, k, v)
                except Exception:
                    pass

        return True
    except Exception:
        return False


def apply_channel_config(channel_name: str, config: Dict[str, Any]):
    """Apply channel config to runtime omnichannel manager if available."""
    if omnichannel is None:
        return False

    try:
        # channels in omnichannel are keyed by ChannelType enum values
        channels = getattr(omnichannel, "channels", None)
        if channels is None:
            return False

        # Alias mapping for human-friendly names
        alias_map = {
            "website": "website_chat",
            "website_chat": "website_chat",
            "websitechat": "website_chat",
            "site": "website_chat"
        }
        
        lower_name = channel_name.lower()
        canonical = alias_map.get(lower_name, lower_name)

        # Find matching ChannelType by value
        for ckey in list(channels.keys()):
            cval = getattr(ckey, "value", str(ckey)).lower()
            if cval == canonical or cval == lower_name:
                cfg = channels[ckey]
                # Update the config
                if isinstance(cfg, dict):
                    cfg.update(config)
                else:
                    # ChannelConfig dataclass - set attributes
                    for k, v in config.items():
                        if k == "enabled":
                            cfg.enabled = v
                        elif k == "settings" and isinstance(v, dict):
                            if hasattr(cfg, "credentials"):
                                cfg.credentials.update(v)
                        elif hasattr(cfg, k):
                            setattr(cfg, k, v)
                        else:
                            # fallback: store in credentials
                            if hasattr(cfg, "credentials") and isinstance(cfg.credentials, dict):
                                cfg.credentials[k] = v
                return True

        return False
    except Exception:
        return False


def read_ai_config(default: Dict[str, Any]) -> Dict[str, Any]:
    return read_json(AI_CONFIG_FILE, default)


def write_ai_config(data: Dict[str, Any]):
    write_json(AI_CONFIG_FILE, data)
