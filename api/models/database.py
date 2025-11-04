"""
SQLAlchemy database models
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base


class APIKey(Base):
    """API Key model for authentication"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    key_hash = Column(String(255), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)

    # Relationships
    deployments = relationship("Deployment", back_populates="api_key")


class Deployment(Base):
    """Deployment model - represents an app deployment"""
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    namespace = Column(String(255), nullable=False)
    image = Column(String(512), nullable=False)
    port = Column(Integer, nullable=False)
    domain = Column(String(255), nullable=True)
    replicas = Column(Integer, default=1, nullable=False)
    env_vars = Column(JSON, default={}, nullable=True)
    resources = Column(JSON, default={}, nullable=True)
    healthcheck = Column(JSON, default={}, nullable=True)
    status = Column(String(50), default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Foreign keys
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)

    # Relationships
    api_key = relationship("APIKey", back_populates="deployments")
    history = relationship("DeploymentHistory", back_populates="deployment", cascade="all, delete-orphan")


class DeploymentHistory(Base):
    """Deployment history - tracks changes over time"""
    __tablename__ = "deployment_history"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id"), nullable=False)
    action = Column(String(50), nullable=False)  # create, update, scale, rollback, delete
    image = Column(String(512), nullable=True)
    replicas = Column(Integer, nullable=True)
    changes = Column(JSON, default={}, nullable=True)
    performed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    deployment = relationship("Deployment", back_populates="history")
