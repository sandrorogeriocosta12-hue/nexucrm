    """
    Serviço básico de analytics.
    """

    from typing import Dict, Any
    from datetime import datetime

class AnalyticsService:
    """Serviço básico de analytics."""

def __init__(self):
        self.events = []

async def track_event(self, event_name: str, properties: Dict[str, Any]) -> None:
        """Registra evento de analytics."""
        event = {
            "event_name": event_name,
            "properties": properties,
            "timestamp": datetime.utcnow().isoformat()
        }

        self.events.append(event)
        print(f"📊 Evento rastreado: {event_name} - {properties}")

def get_events(self) -> list:
        """Retorna todos os eventos registrados."""
        return self.events