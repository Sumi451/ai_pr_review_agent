"""Tests for configuration management."""

import os
import tempfile
from pathlib import Path
import pytest
import yaml

from ai_pr_agent.config import Settings, get_settings


class TestSettings:
    """Test configuration settings."""
    
    def test_default_settings(self):
        """Test default settings creation."""
        settings = Settings()
        
        assert settings.app.name == "AI PR Review Agent"
        assert settings.app.version == "0.1.0"
        assert settings.github.api_base_url == "https://api.github.com"
        assert settings.analysis.ai_feedback.model == "codellama"
    
    def test_load_from_yaml(self):
        """Test loading settings from YAML file."""
        config_data = {
            "app": {
                "debug": True,
                "log_level": "DEBUG"
            },
            "github": {
                "timeout": 60
            },
            "analysis": {
                "ai_feedback": {
                    "model": "llama2",
                    "max_tokens": 500
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
        
        try:
            # Mock load_dotenv to prevent loading .env file
            # and mock environment variables to not override YAML config
            import os
            from unittest.mock import patch
            
            # Save original env vars
            original_debug = os.environ.get('DEBUG')
            original_log_level = os.environ.get('LOG_LEVEL')
            
            # Remove env vars that would override YAML config
            os.environ.pop('DEBUG', None)
            os.environ.pop('LOG_LEVEL', None)
            
            try:
                # Mock load_dotenv to do nothing
                with patch('ai_pr_agent.config.settings.load_dotenv'):
                    settings = Settings.load_from_file(config_path)
                
                assert settings.app.debug is True
                assert settings.app.log_level == "DEBUG"
                assert settings.github.timeout == 60
                assert settings.analysis.ai_feedback.model == "llama2"
                assert settings.analysis.ai_feedback.max_tokens == 500
            finally:
                # Restore original env vars
                if original_debug is not None:
                    os.environ['DEBUG'] = original_debug
                if original_log_level is not None:
                    os.environ['LOG_LEVEL'] = original_log_level
        finally:
            os.unlink(config_path)
    
    def test_environment_variables(self, monkeypatch):
        """Test environment variable override."""
        monkeypatch.setenv("GITHUB_TOKEN", "test-token-123")
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("LOG_LEVEL", "WARNING")
        
        settings = Settings.load_from_file()
        
        assert settings.github.token == "test-token-123"
        assert settings.app.debug is True
        assert settings.app.log_level == "WARNING"
    
    def test_validation_errors(self):
        """Test configuration validation."""
        settings = Settings()
        settings.github.token = None  # Missing required token
        settings.analysis.ai_feedback.model = "invalid-model"
        
        errors = settings.validate()
        
        assert len(errors) >= 2
        assert any("GitHub token is required" in error for error in errors)
        assert any("AI model must be one of" in error for error in errors)
    
    def test_validation_success(self):
        """Test successful validation."""
        settings = Settings()
        settings.github.token = "valid-token"
        
        errors = settings.validate()
        
        assert len(errors) == 0
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        settings = Settings()
        settings.github.token = "secret-token"
        
        config_dict = settings.to_dict()
        
        assert "app" in config_dict
        assert "github" in config_dict
        assert "analysis" in config_dict
        
        # Token should not be included in dict export
        assert "token" not in config_dict["github"]


def test_get_settings_singleton():
    """Test that get_settings returns the same instance."""
    settings1 = get_settings()
    settings2 = get_settings()
    
    assert settings1 is settings2


def test_reload_settings():
    """Test settings reload functionality."""
    from ai_pr_agent.config.settings import reload_settings
    
    settings1 = get_settings()
    settings2 = reload_settings()
    
    # Should be different instances after reload
    assert settings1 is not settings2