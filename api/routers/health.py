"""
Health check endpoints
"""

from fastapi import APIRouter
from datetime import datetime
from models.schemas import HealthResponse
from core.kubernetes import KubernetesManager
from core.database import SessionLocal

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""

    # Check Kubernetes connection
    k8s_healthy = False
    try:
        k8s = KubernetesManager()
        k8s.core_v1.list_namespace(limit=1)
        k8s_healthy = True
    except Exception:
        pass

    # Check database connection
    db_healthy = False
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_healthy = True
    except Exception:
        pass

    status = "healthy" if (k8s_healthy and db_healthy) else "degraded"

    return HealthResponse(
        status=status,
        version="1.0.0",
        kubernetes=k8s_healthy,
        database=db_healthy,
        timestamp=datetime.utcnow()
    )
