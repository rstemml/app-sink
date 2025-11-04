"""
Pydantic models for request/response schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List
from datetime import datetime


class ResourceRequirements(BaseModel):
    """Resource requirements for deployment"""
    cpu: str = Field(default="500m", description="CPU limit (e.g., 500m, 1, 2)")
    memory: str = Field(default="512Mi", description="Memory limit (e.g., 512Mi, 1Gi)")


class HealthCheck(BaseModel):
    """Health check configuration"""
    path: str = Field(default="/health", description="Health check path")
    interval: int = Field(default=30, description="Check interval in seconds")
    timeout: int = Field(default=5, description="Timeout in seconds")
    initial_delay: int = Field(default=10, description="Initial delay in seconds")


class DeploymentCreate(BaseModel):
    """Request model for creating a deployment"""
    name: str = Field(..., description="Application name (lowercase, alphanumeric, hyphens)")
    image: str = Field(..., description="Docker image (e.g., registry.io/app:tag)")
    port: int = Field(..., description="Container port to expose")
    domain: Optional[str] = Field(None, description="Custom domain (e.g., myapp.example.com)")
    replicas: int = Field(default=1, ge=1, le=10, description="Number of replicas")
    env: Optional[Dict[str, str]] = Field(default={}, description="Environment variables")
    resources: Optional[ResourceRequirements] = Field(default_factory=ResourceRequirements)
    healthcheck: Optional[HealthCheck] = Field(default_factory=HealthCheck)

    @validator("name")
    def validate_name(cls, v):
        """Validate app name follows Kubernetes naming conventions"""
        if not v:
            raise ValueError("Name cannot be empty")
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Name must be alphanumeric with hyphens/underscores")
        if len(v) > 63:
            raise ValueError("Name must be 63 characters or less")
        return v.lower()

    @validator("port")
    def validate_port(cls, v):
        """Validate port is in valid range"""
        if not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v


class DeploymentUpdate(BaseModel):
    """Request model for updating a deployment"""
    image: Optional[str] = None
    replicas: Optional[int] = Field(None, ge=1, le=10)
    env: Optional[Dict[str, str]] = None
    resources: Optional[ResourceRequirements] = None
    domain: Optional[str] = None


class DeploymentScale(BaseModel):
    """Request model for scaling a deployment"""
    replicas: int = Field(..., ge=0, le=10, description="Number of replicas")


class DeploymentResponse(BaseModel):
    """Response model for deployment"""
    name: str
    namespace: str
    image: str
    port: int
    domain: Optional[str]
    replicas: int
    env_vars: Dict[str, str]
    resources: Dict
    status: str
    created_at: datetime
    updated_at: datetime
    url: Optional[str] = None

    class Config:
        from_attributes = True


class DeploymentList(BaseModel):
    """Response model for list of deployments"""
    deployments: List[DeploymentResponse]
    total: int


class AnalyzeRequest(BaseModel):
    """Request model for AI-powered repo analysis"""
    git_url: Optional[str] = Field(None, description="Git repository URL")
    repo_path: Optional[str] = Field(None, description="Local repository path")
    branch: str = Field(default="main", description="Git branch to analyze")


class AnalyzeResponse(BaseModel):
    """Response model for AI analysis"""
    detected_language: str
    detected_framework: Optional[str]
    package_manager: Optional[str]
    entry_point: Optional[str]
    detected_port: Optional[int]
    dependencies: List[str]
    recommended_resources: ResourceRequirements
    suggested_env_vars: List[str]
    deployment_config: DeploymentCreate
    confidence: float = Field(ge=0.0, le=1.0, description="Analysis confidence score")


class DeployAnalyzeRequest(BaseModel):
    """Request model for analyze and deploy in one step"""
    git_url: str = Field(..., description="Git repository URL")
    branch: str = Field(default="main", description="Git branch")
    domain: Optional[str] = Field(None, description="Custom domain")
    env: Optional[Dict[str, str]] = Field(default={}, description="Additional environment variables")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    kubernetes: bool
    database: bool
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    status_code: int
    details: Optional[Dict] = None


class LogsResponse(BaseModel):
    """Logs response model"""
    logs: str
    pod_name: str
    container: str


class APIKeyCreate(BaseModel):
    """Request model for creating API key"""
    name: str = Field(..., description="API key name")
    description: Optional[str] = Field(None, description="API key description")


class APIKeyResponse(BaseModel):
    """Response model for API key"""
    name: str
    description: Optional[str]
    api_key: str  # Only returned on creation
    created_at: datetime

    class Config:
        from_attributes = True
