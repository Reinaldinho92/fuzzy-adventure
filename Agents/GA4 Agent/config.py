"""
Configuratie voor de GA4 Agent.
Laadt instellingen uit omgevingsvariabelen of een .env bestand.
"""

from __future__ import annotations

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL: str = "claude-sonnet-4-6"
    GA4_PROPERTY_ID: str = os.environ.get("GA4_PROPERTY_ID", "")
    GA4_SERVICE_ACCOUNT_PATH: str = os.environ.get("GA4_SERVICE_ACCOUNT_PATH", "")

    @classmethod
    def validate(cls) -> list[str]:
        """Geeft een lijst van ontbrekende verplichte instellingen."""
        missing = []
        if not cls.ANTHROPIC_API_KEY:
            missing.append("ANTHROPIC_API_KEY")
        return missing
