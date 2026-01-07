"""Configuration management for MCP Flashcard Generator."""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # Anthropic API
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # MCP Server
    MCP_PORT: int = int(os.getenv("MCP_PORT", "3000"))
    AUTO_GENERATE: bool = os.getenv("AUTO_GENERATE", "true").lower() == "true"

    # Anki Sync Server
    SYNC_BASE: str = os.getenv("SYNC_BASE", "/syncserver")
    SYNC_USER1: str = os.getenv("SYNC_USER1", "")
    SYNC_USER2: str = os.getenv("SYNC_USER2", "")
    SYNC_USER3: str = os.getenv("SYNC_USER3", "")
    SYNC_USER4: str = os.getenv("SYNC_USER4", "")
    SYNC_USER5: str = os.getenv("SYNC_USER5", "")

    @classmethod
    def get_primary_user(cls) -> tuple[str, str]:
        """Get primary sync user credentials."""
        if not cls.SYNC_USER1:
            raise ValueError("SYNC_USER1 environment variable is required")

        parts = cls.SYNC_USER1.split(":", 1)
        if len(parts) != 2:
            raise ValueError("SYNC_USER1 must be in format 'username:password'")

        return parts[0], parts[1]

    @classmethod
    def get_user_collection_path(cls, username: Optional[str] = None) -> str:
        """Get path to user's Anki collection."""
        if username is None:
            username, _ = cls.get_primary_user()

        return os.path.join(cls.SYNC_BASE, username, "collection.anki2")

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        if not cls.SYNC_USER1:
            raise ValueError("SYNC_USER1 environment variable is required")

        # Validate format
        cls.get_primary_user()


config = Config()
