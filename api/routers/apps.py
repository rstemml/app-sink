"""
Application management endpoints
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from models.schemas import (
    DeploymentCreate,
    DeploymentUpdate,
    DeploymentResponse,
    DeploymentList,
    DeploymentScale,
    LogsResponse
)
from models.database import Deployment, DeploymentHistory, APIKey
from core.kubernetes import KubernetesManager
from core.database import get_db
from core.auth import verify_api_key

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/apps", response_model=DeploymentResponse, status_code=201)
async def create_app(
    deployment: DeploymentCreate,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key)
):
    """Create a new application deployment"""

    # Check if app already exists
    existing = db.query(Deployment).filter(Deployment.name == deployment.name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"App '{deployment.name}' already exists")

    # Initialize Kubernetes manager
    k8s = KubernetesManager()

    try:
        # Create namespace
        namespace = k8s.create_namespace(deployment.name)

        # Create Kubernetes resources
        k8s.create_deployment(deployment.name, deployment)
        k8s.create_service(deployment.name, deployment.port)
        ingress_result = k8s.create_ingress(deployment.name, deployment.domain)

        # Save to database
        db_deployment = Deployment(
            name=deployment.name,
            namespace=namespace,
            image=deployment.image,
            port=deployment.port,
            domain=ingress_result.get("domain"),
            replicas=deployment.replicas,
            env_vars=deployment.env or {},
            resources=deployment.resources.dict() if deployment.resources else {},
            healthcheck=deployment.healthcheck.dict() if deployment.healthcheck else {},
            status="running",
            api_key_id=api_key.id
        )

        db.add(db_deployment)

        # Add history entry
        history = DeploymentHistory(
            deployment_id=db_deployment.id,
            action="create",
            image=deployment.image,
            replicas=deployment.replicas
        )
        db.add(history)

        db.commit()
        db.refresh(db_deployment)

        logger.info(f"Created app: {deployment.name}")

        # Build response
        response = DeploymentResponse.from_orm(db_deployment)
        response.url = f"https://{db_deployment.domain}" if db_deployment.domain else None

        return response

    except Exception as e:
        logger.error(f"Failed to create app: {e}")
        # Cleanup on failure
        try:
            k8s.delete_deployment(deployment.name)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Failed to create app: {str(e)}")


@router.get("/apps", response_model=DeploymentList)
async def list_apps(
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """List all applications"""

    # Get deployments from database
    deployments = db.query(Deployment).offset(skip).limit(limit).all()
    total = db.query(Deployment).count()

    # Build response
    deployment_list = []
    for dep in deployments:
        response = DeploymentResponse.from_orm(dep)
        response.url = f"https://{dep.domain}" if dep.domain else None
        deployment_list.append(response)

    return DeploymentList(
        deployments=deployment_list,
        total=total
    )


@router.get("/apps/{app_name}", response_model=DeploymentResponse)
async def get_app(
    app_name: str,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key)
):
    """Get application details"""

    deployment = db.query(Deployment).filter(Deployment.name == app_name).first()
    if not deployment:
        raise HTTPException(status_code=404, detail=f"App '{app_name}' not found")

    # Get live status from Kubernetes
    k8s = KubernetesManager()
    try:
        status = k8s.get_deployment_status(app_name)
        deployment.status = status.get("status", "unknown")
    except:
        pass

    response = DeploymentResponse.from_orm(deployment)
    response.url = f"https://{deployment.domain}" if deployment.domain else None

    return response


@router.put("/apps/{app_name}", response_model=DeploymentResponse)
async def update_app(
    app_name: str,
    update: DeploymentUpdate,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key)
):
    """Update application deployment"""

    deployment = db.query(Deployment).filter(Deployment.name == app_name).first()
    if not deployment:
        raise HTTPException(status_code=404, detail=f"App '{app_name}' not found")

    k8s = KubernetesManager()

    try:
        # Update Kubernetes deployment
        k8s.update_deployment(app_name, update)

        # Update database
        changes = {}
        if update.image:
            changes["image"] = {"old": deployment.image, "new": update.image}
            deployment.image = update.image

        if update.replicas is not None:
            changes["replicas"] = {"old": deployment.replicas, "new": update.replicas}
            deployment.replicas = update.replicas

        if update.env:
            deployment.env_vars = update.env

        if update.resources:
            deployment.resources = update.resources.dict()

        if update.domain:
            deployment.domain = update.domain

        # Add history entry
        history = DeploymentHistory(
            deployment_id=deployment.id,
            action="update",
            image=update.image,
            replicas=update.replicas,
            changes=changes
        )
        db.add(history)

        db.commit()
        db.refresh(deployment)

        logger.info(f"Updated app: {app_name}")

        response = DeploymentResponse.from_orm(deployment)
        response.url = f"https://{deployment.domain}" if deployment.domain else None

        return response

    except Exception as e:
        logger.error(f"Failed to update app: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update app: {str(e)}")


@router.put("/apps/{app_name}/scale", response_model=DeploymentResponse)
async def scale_app(
    app_name: str,
    scale: DeploymentScale,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key)
):
    """Scale application replicas"""

    deployment = db.query(Deployment).filter(Deployment.name == app_name).first()
    if not deployment:
        raise HTTPException(status_code=404, detail=f"App '{app_name}' not found")

    k8s = KubernetesManager()

    try:
        # Scale in Kubernetes
        k8s.scale_deployment(app_name, scale.replicas)

        # Update database
        old_replicas = deployment.replicas
        deployment.replicas = scale.replicas

        # Add history entry
        history = DeploymentHistory(
            deployment_id=deployment.id,
            action="scale",
            replicas=scale.replicas,
            changes={"replicas": {"old": old_replicas, "new": scale.replicas}}
        )
        db.add(history)

        db.commit()
        db.refresh(deployment)

        logger.info(f"Scaled app {app_name} to {scale.replicas} replicas")

        response = DeploymentResponse.from_orm(deployment)
        response.url = f"https://{deployment.domain}" if deployment.domain else None

        return response

    except Exception as e:
        logger.error(f"Failed to scale app: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to scale app: {str(e)}")


@router.delete("/apps/{app_name}")
async def delete_app(
    app_name: str,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key)
):
    """Delete application"""

    deployment = db.query(Deployment).filter(Deployment.name == app_name).first()
    if not deployment:
        raise HTTPException(status_code=404, detail=f"App '{app_name}' not found")

    k8s = KubernetesManager()

    try:
        # Delete from Kubernetes
        k8s.delete_deployment(app_name)

        # Add history entry before deletion
        history = DeploymentHistory(
            deployment_id=deployment.id,
            action="delete",
            image=deployment.image
        )
        db.add(history)

        # Delete from database
        db.delete(deployment)
        db.commit()

        logger.info(f"Deleted app: {app_name}")

        return {"status": "deleted", "name": app_name}

    except Exception as e:
        logger.error(f"Failed to delete app: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete app: {str(e)}")


@router.get("/apps/{app_name}/logs", response_model=LogsResponse)
async def get_app_logs(
    app_name: str,
    tail: int = Query(100, ge=1, le=1000),
    api_key: APIKey = Depends(verify_api_key)
):
    """Get application logs"""

    k8s = KubernetesManager()

    try:
        logs = k8s.get_logs(app_name, tail_lines=tail)

        return LogsResponse(
            logs=logs,
            pod_name=app_name,
            container=app_name
        )

    except Exception as e:
        logger.error(f"Failed to get logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")


@router.post("/apps/{app_name}/rollback", response_model=DeploymentResponse)
async def rollback_app(
    app_name: str,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key)
):
    """Rollback to previous deployment"""

    deployment = db.query(Deployment).filter(Deployment.name == app_name).first()
    if not deployment:
        raise HTTPException(status_code=404, detail=f"App '{app_name}' not found")

    # Get previous deployment from history
    previous = db.query(DeploymentHistory).filter(
        DeploymentHistory.deployment_id == deployment.id,
        DeploymentHistory.action.in_(["create", "update"]),
        DeploymentHistory.image.isnot(None)
    ).order_by(DeploymentHistory.performed_at.desc()).offset(1).first()

    if not previous or not previous.image:
        raise HTTPException(status_code=400, detail="No previous deployment found to rollback to")

    k8s = KubernetesManager()

    try:
        # Rollback in Kubernetes
        update = DeploymentUpdate(
            image=previous.image,
            replicas=previous.replicas
        )
        k8s.update_deployment(app_name, update)

        # Update database
        deployment.image = previous.image
        if previous.replicas:
            deployment.replicas = previous.replicas

        # Add history entry
        history = DeploymentHistory(
            deployment_id=deployment.id,
            action="rollback",
            image=previous.image,
            replicas=previous.replicas
        )
        db.add(history)

        db.commit()
        db.refresh(deployment)

        logger.info(f"Rolled back app {app_name} to {previous.image}")

        response = DeploymentResponse.from_orm(deployment)
        response.url = f"https://{deployment.domain}" if deployment.domain else None

        return response

    except Exception as e:
        logger.error(f"Failed to rollback app: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to rollback app: {str(e)}")
