"""
Build and Deploy router
Complete Git → Build → Deploy workflow using Cloud Native Buildpacks
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
import logging

from core.database import get_db
from core.buildpack import BuildpackBuilder
from core.kubernetes import KubernetesManager
from core.config import get_settings
from core.auth import verify_api_key
from models.database import Deployment, DeploymentHistory
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

settings = get_settings()


class BuildAndDeployRequest(BaseModel):
    """Request to build from Git and deploy"""
    git_url: HttpUrl
    name: str
    branch: str = "main"
    domain: Optional[str] = None
    replicas: int = 1
    environment_variables: Optional[dict] = None
    builder: Optional[str] = None  # Optional custom builder
    registry_url: Optional[str] = None


class BuildAndDeployResponse(BaseModel):
    """Response from build and deploy"""
    deployment_id: str
    name: str
    image: str
    git_url: str
    status: str
    message: str


async def build_and_deploy_background(
    git_url: str,
    name: str,
    branch: str,
    domain: Optional[str],
    replicas: int,
    environment_variables: Optional[dict],
    builder: Optional[str],
    registry_url: Optional[str],
    db: Session
):
    """Background task to build and deploy"""
    try:
        # Initialize builder
        registry = registry_url or settings.docker_registry_url
        buildpack = BuildpackBuilder(registry_url=registry)
        k8s = KubernetesManager()

        logger.info(f"Starting build for {name} from {git_url}")

        # Build image with buildpack
        image_tag = buildpack.build_from_git(
            git_url=str(git_url),
            image_name=name,
            branch=branch,
            builder=builder,
            push=True
        )

        logger.info(f"Built image: {image_tag}")

        # Detect port (TODO: improve with AI analysis)
        port = 8080  # Default for buildpacks

        # Deploy to Kubernetes
        k8s.create_deployment(
            name=name,
            image=image_tag,
            port=port,
            replicas=replicas,
            domain=domain,
            environment_variables=environment_variables
        )

        # Update database
        deployment = db.query(Deployment).filter(Deployment.name == name).first()
        if deployment:
            deployment.status = "running"
            deployment.image = image_tag
            deployment.updated_at = datetime.utcnow()

            # Add to history
            history = DeploymentHistory(
                deployment_id=deployment.id,
                action="build_and_deploy",
                changes={"git_url": str(git_url), "image": image_tag}
            )
            db.add(history)
            db.commit()

        logger.info(f"Successfully deployed {name} from {git_url}")

    except Exception as e:
        logger.error(f"Build and deploy failed for {name}: {str(e)}")

        # Update deployment status to failed
        deployment = db.query(Deployment).filter(Deployment.name == name).first()
        if deployment:
            deployment.status = "failed"
            deployment.updated_at = datetime.utcnow()
            db.commit()


@router.post("/build-and-deploy", response_model=BuildAndDeployResponse, dependencies=[Depends(verify_api_key)])
async def build_and_deploy(
    request: BuildAndDeployRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Build from Git repository using Cloud Native Buildpacks and deploy to Kubernetes

    Complete workflow:
    1. Clone Git repository
    2. Detect language/framework automatically
    3. Build Docker image (NO Dockerfile needed!)
    4. Push to registry
    5. Deploy to Kubernetes

    Uses Paketo Buildpacks (CNCF) - 100% Open Source!

    **Note**: This is an async operation. The deployment will be created immediately
    with status 'building', and the actual build happens in the background.
    """
    try:
        # Check if deployment already exists
        existing = db.query(Deployment).filter(Deployment.name == request.name).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Deployment with name '{request.name}' already exists"
            )

        # Create deployment record
        deployment = Deployment(
            name=request.name,
            image="building...",
            port=8080,  # Default for buildpacks
            domain=request.domain,
            replicas=request.replicas,
            status="building",
            environment_variables=request.environment_variables,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(deployment)
        db.commit()
        db.refresh(deployment)

        # Start background build
        background_tasks.add_task(
            build_and_deploy_background,
            git_url=str(request.git_url),
            name=request.name,
            branch=request.branch,
            domain=request.domain,
            replicas=request.replicas,
            environment_variables=request.environment_variables,
            builder=request.builder,
            registry_url=request.registry_url,
            db=db
        )

        return BuildAndDeployResponse(
            deployment_id=str(deployment.id),
            name=request.name,
            image="building...",
            git_url=str(request.git_url),
            status="building",
            message="Build started in background. Use GET /apps/{name} to check status."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start build: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start build: {str(e)}"
        )


@router.get("/buildpack/info")
async def get_buildpack_info(api_key = Depends(verify_api_key)):
    """
    Get information about available buildpack builders
    """
    return {
        "default_builder": BuildpackBuilder.DEFAULT_BUILDER,
        "supported_languages": [
            "Node.js (package.json)",
            "Python (requirements.txt, Pipfile)",
            "Go (go.mod)",
            "Ruby (Gemfile)",
            "Java (pom.xml, build.gradle)",
            "PHP (composer.json)",
            ".NET (*.csproj)"
        ],
        "features": [
            "No Dockerfile needed",
            "Auto-detection of language/framework",
            "Security patches included",
            "Optimized caching",
            "Cloud Native (CNCF standard)"
        ],
        "builder": "Paketo Buildpacks (Open Source)"
    }
