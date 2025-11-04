"""
Configuration management using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Server
    environment: str = "production"
    server_host: str = "0.0.0.0"
    server_port: int = 8000

    # Database
    database_url: str = "postgresql://app_sink:password@localhost/app_sink"

    # Kubernetes
    kubeconfig: str = "/etc/rancher/k3s/k3s.yaml"
    namespace_prefix: str = "app-"

    # Ingress
    ingress_class: str = "traefik"
    tls_issuer: str = "letsencrypt"
    default_domain: str = "apps.example.com"

    # AI
    ai_provider: str = "anthropic"  # anthropic or openai
    ai_api_key: Optional[str] = None
    ai_model: str = "claude-3-5-sonnet-20241022"

    # API
    api_domain: str = "api.example.com"
    admin_email: str = "admin@example.com"

    # Security
    api_key_length: int = 64

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
