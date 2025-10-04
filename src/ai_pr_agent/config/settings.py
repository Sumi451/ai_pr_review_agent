"""
Configuration management for AI PR Review Agent.
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import yaml
from dotenv import load_dotenv


@dataclass
class AppConfig:
    """Application-level configuration."""
    name: str = "AI PR Review Agent"
    version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"


@dataclass
class GitHubConfig:
    """GitHub-specific configuration."""
    api_base_url: str = "https://api.github.com"
    token: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    rate_limit_buffer: int = 100
    repositories: List[str] = field(default_factory=list)


@dataclass
class StaticAnalysisConfig:
    """Static analysis configuration."""
    enabled: bool = True
    tools: List[str] = field(default_factory=lambda: ["flake8", "bandit", "mypy"])
    flake8: Dict[str, Any] = field(default_factory=lambda: {
        "max_line_length": 88,
        "ignore_errors": ["E203", "W503"]
    })
    bandit: Dict[str, Any] = field(default_factory=lambda: {
        "skip_tests": ["B101"]
    })
    mypy: Dict[str, Any] = field(default_factory=lambda: {
        "strict": False,
        "ignore_missing_imports": True
    })


@dataclass
class AIFeedbackConfig:
    """AI feedback configuration."""
    enabled: bool = True
    model: str = "codellama"
    max_tokens: int = 1000
    temperature: float = 0.1
    chunk_size: int = 2000


@dataclass
class AnalysisConfig:
    """Analysis configuration."""
    static_analysis: StaticAnalysisConfig = field(default_factory=StaticAnalysisConfig)
    ai_feedback: AIFeedbackConfig = field(default_factory=AIFeedbackConfig)


@dataclass
class FileFilterConfig:
    """File filtering configuration."""
    included_extensions: List[str] = field(default_factory=lambda: [
        ".py", ".js", ".ts", ".java", ".cpp", ".h", ".go", ".rs"
    ])
    ignored_directories: List[str] = field(default_factory=lambda: [
        "__pycache__", ".git", "node_modules", ".venv", "venv", 
        "build", "dist", ".pytest_cache"
    ])
    ignored_files: List[str] = field(default_factory=lambda: [
        "*.pyc", "*.log", "*.tmp"
    ])


@dataclass
class FeedbackConfig:
    """Feedback formatting configuration."""
    format: str = "markdown"
    include_line_numbers: bool = True
    max_suggestions_per_file: int = 5
    severity_levels: List[str] = field(default_factory=lambda: [
        "error", "warning", "info", "suggestion"
    ])


@dataclass
class CacheConfig:
    """Caching configuration."""
    enabled: bool = True
    ttl_hours: int = 24
    max_size_mb: int = 100


@dataclass
class LoggingConfig:
    """Logging configuration."""
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "logs/ai_pr_review.log"
    max_size_mb: int = 10
    backup_count: int = 5


@dataclass
class Settings:
    """Main configuration class."""
    app: AppConfig = field(default_factory=AppConfig)
    github: GitHubConfig = field(default_factory=GitHubConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    file_filter: FileFilterConfig = field(default_factory=FileFilterConfig)
    feedback: FeedbackConfig = field(default_factory=FeedbackConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def load_from_file(cls, config_path: Optional[str] = None) -> "Settings":
        """Load settings from YAML file and environment variables."""
        # Load environment variables
        load_dotenv()
        
        # Determine config file path
        if config_path is None:
            config_path = os.getenv("CONFIG_FILE", "config/config.yaml")
        
        config_path = Path(config_path)
        
        # Load YAML config if it exists
        config_data = {}
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
        
        # Create settings instance
        settings = cls()
        
        # Update with config file data
        if config_data:
            settings._update_from_dict(config_data)
        
        # Override with environment variables
        settings._update_from_env()
        
        return settings
    
    def _update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update settings from dictionary."""
        if "app" in data:
            self._update_dataclass(self.app, data["app"])
        if "github" in data:
            self._update_dataclass(self.github, data["github"])
        if "analysis" in data:
            if "static_analysis" in data["analysis"]:
                self._update_dataclass(
                    self.analysis.static_analysis, 
                    data["analysis"]["static_analysis"]
                )
            if "ai_feedback" in data["analysis"]:
                self._update_dataclass(
                    self.analysis.ai_feedback, 
                    data["analysis"]["ai_feedback"]
                )
        if "file_filter" in data:
            self._update_dataclass(self.file_filter, data["file_filter"])
        if "feedback" in data:
            self._update_dataclass(self.feedback, data["feedback"])
        if "cache" in data:
            self._update_dataclass(self.cache, data["cache"])
        if "logging" in data:
            self._update_dataclass(self.logging, data["logging"])
    
    def _update_from_env(self) -> None:
        """Update settings from environment variables"""
        # GitHub token from environment
        if os.getenv("GITHUB_TOKEN"):
            self.github.token = os.getenv("GITHUB_TOKEN")
        
        # Debug mode
        if os.getenv("DEBUG"):
            self.app.debug = os.getenv("DEBUG").lower() in ("true", "1", "yes")
        
        # Log level
        if os.getenv("LOG_LEVEL"):
            self.app.log_level = os.getenv("LOG_LEVEL")
    
    @staticmethod
    def _update_dataclass(instance: Any, data: Dict[str, Any]) -> None:
        """Update a dataclass instance with dictionary data."""
        for key, value in data.items():
            if hasattr(instance, key):
                # Handle nested dictionaries
                current_value = getattr(instance, key)
                if isinstance(current_value, dict) and isinstance(value, dict):
                    current_value.update(value)
                else:
                    setattr(instance, key, value)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Validate GitHub token if GitHub features are needed
        if not self.github.token:
            errors.append("GitHub token is required (set GITHUB_TOKEN environment variable)")
        
        # Validate AI model if AI feedback is enabled
        if self.analysis.ai_feedback.enabled:
            valid_models = ["codellama", "llama2", "mistral"]
            if self.analysis.ai_feedback.model not in valid_models:
                errors.append(f"AI model must be one of: {valid_models}")
        
        # Validate file extensions
        if not self.file_filter.included_extensions:
            errors.append("At least one file extension must be included")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for serialization."""
        return {
            "app": self.app.__dict__,
            "github": {k: v for k, v in self.github.__dict__.items() if k != "token"},
            "analysis": {
                "static_analysis": self.analysis.static_analysis.__dict__,
                "ai_feedback": self.analysis.ai_feedback.__dict__,
            },
            "file_filter": self.file_filter.__dict__,
            "feedback": self.feedback.__dict__,
            "cache": self.cache.__dict__,
            "logging": self.logging.__dict__,
        }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings(config_path: Optional[str] = None, reload: bool = False) -> Settings:
    """Get the global settings instance."""
    global _settings
    
    if _settings is None or reload:
        _settings = Settings.load_from_file(config_path)
    
    return _settings


def reload_settings(config_path: Optional[str] = None) -> Settings:
    """Reload settings from file."""
    return get_settings(config_path, reload=True)