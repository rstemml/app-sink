"""
Configuration management for CLI
"""

import os
import yaml
from pathlib import Path
from typing import Optional


class Config:
    """CLI configuration"""

    def __init__(self):
        self.config_dir = Path.home() / ".app-sink"
        self.config_file = self.config_dir / "config.yaml"
        self._ensure_config_dir()
        self._config = self._load_config()

    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        self.config_dir.mkdir(exist_ok=True)

    def _load_config(self) -> dict:
        """Load configuration from file"""
        if not self.config_file.exists():
            return {
                "endpoint": None,
                "api_key": None,
                "default_domain": None
            }

        with open(self.config_file, 'r') as f:
            return yaml.safe_load(f) or {}

    def _save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            yaml.dump(self._config, f)

    def get(self, key: str, default=None):
        """Get configuration value"""
        return self._config.get(key, default)

    def set(self, key: str, value: str):
        """Set configuration value"""
        self._config[key] = value
        self._save_config()

    @property
    def endpoint(self) -> Optional[str]:
        """Get API endpoint"""
        return self.get("endpoint") or os.getenv("APP_SINK_ENDPOINT")

    @property
    def api_key(self) -> Optional[str]:
        """Get API key"""
        return self.get("api_key") or os.getenv("APP_SINK_API_KEY")

    @property
    def default_domain(self) -> Optional[str]:
        """Get default domain"""
        return self.get("default_domain")

    def is_configured(self) -> bool:
        """Check if CLI is configured"""
        return bool(self.endpoint and self.api_key)


# Global config instance
config = Config()
