# mcp_shared/config.py
"""Application settings and feature flags.

Settings are loaded from environment variables and an optional .env file.
Feature flags are nested under the FEATURES__ prefix.

Usage:
    from mcp_shared.config import get_settings

    settings = get_settings()

    if settings.features.my_feature:
        add_my_feature_tool(mcp)

Environment variables:
    APP_ENV                         local | dev | staging | prod  (default: local)
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Deployment environment.

    Inherits from str so values compare equal to raw env var strings.
    """

    LOCAL = "local"
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class FeatureFlags(BaseModel):
    """Individual feature toggles.

    Each flag maps to an env var via the FEATURES__ prefix:
        FEATURES__MY_FEATURE=false  →  features.my_feature = False

    All flags default to True so new environments start fully enabled
    and selectively disable only what they need.
    """


class Settings(BaseSettings):
    """Application settings — single source of truth for runtime configuration.

    Reads from environment variables and a .env file (lower precedence than
    real env vars, so CI/CD values always win).

    Nested objects use __ as the delimiter:
        FEATURES__TOOL_TEMPLATE=false
    """

    app_env: Environment = Environment.LOCAL
    features: FeatureFlags = FeatureFlags()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",  # silently drop unknown env vars — important in shared environments
    )

    @property
    def is_local(self) -> bool:
        """True when running in a local development environment."""
        return self.app_env == Environment.LOCAL

    @property
    def is_prod(self) -> bool:
        """True when running in production."""
        return self.app_env == Environment.PROD


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the cached Settings singleton.

    Reads from env vars and .env on first call; subsequent calls return
    the same instance for performance.  In tests, instantiate Settings()
    directly to avoid cache side-effects.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
