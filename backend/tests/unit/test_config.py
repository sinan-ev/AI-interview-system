"""
Unit tests for application configuration.
"""
from app.core.config import Settings, get_settings


def test_settings_defaults():
    settings = get_settings()
    assert settings.APP_NAME == "AI Interview & Assessment Platform"
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7
    assert settings.MAX_FILE_SIZE_BYTES > 0
    assert "pdf" in settings.ALLOWED_FILE_EXTENSIONS
    assert "wav" in settings.ALLOWED_AUDIO_EXTENSIONS


def test_settings_lru_cache():
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
