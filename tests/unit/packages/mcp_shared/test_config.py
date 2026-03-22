"""Unit tests for mcp_shared config — Settings and FeatureFlags."""

import pytest

from mcp_shared.config import Environment, FeatureFlags, Settings, get_settings


class TestEnvironment:
    def test_string_values(self) -> None:
        assert Environment.LOCAL == "local"
        assert Environment.DEV == "dev"
        assert Environment.STAGING == "staging"
        assert Environment.PROD == "prod"

    def test_is_str_subclass(self) -> None:
        # Allows direct comparison with env var strings
        assert isinstance(Environment.LOCAL, str)



class TestSettings:
    def test_defaults_to_local_environment(self) -> None:
        settings = Settings()
        assert settings.app_env == Environment.LOCAL

    def test_is_local_true_for_local(self) -> None:
        settings = Settings(app_env=Environment.LOCAL)
        assert settings.is_local is True

    def test_is_local_false_for_prod(self) -> None:
        settings = Settings(app_env=Environment.PROD)
        assert settings.is_local is False

    def test_is_prod_true_for_prod(self) -> None:
        settings = Settings(app_env=Environment.PROD)
        assert settings.is_prod is True

    def test_is_prod_false_for_local(self) -> None:
        settings = Settings(app_env=Environment.LOCAL)
        assert settings.is_prod is False

    def test_env_var_overrides_app_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APP_ENV", "staging")
        settings = Settings()
        assert settings.app_env == Environment.STAGING

    def test_unknown_env_vars_are_ignored(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("COMPLETELY_UNKNOWN_VAR", "something")
        settings = Settings()  # should not raise
        assert settings.app_env == Environment.LOCAL


class TestGetSettings:
    def test_returns_settings_instance(self) -> None:
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_returns_same_instance_on_repeated_calls(self) -> None:
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
