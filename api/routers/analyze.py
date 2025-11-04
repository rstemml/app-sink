"""
AI-powered repository analysis endpoints
"""

import logging
import tempfile
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import git

from models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    DeployAnalyzeRequest,
    DeploymentResponse
)
from models.database import APIKey
from core.ai import AIAnalyzer
from core.auth import verify_api_key
from core.database import get_db
from routers.apps import create_app

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_repository(
    request: AnalyzeRequest,
    api_key: APIKey = Depends(verify_api_key)
):
    """
    Analyze a repository using AI to generate deployment configuration
    """

    temp_dir = None
    try:
        # Determine repo path
        if request.git_url:
            # Clone repository to temp directory
            temp_dir = tempfile.mkdtemp()
            logger.info(f"Cloning {request.git_url} to {temp_dir}")

            git.Repo.clone_from(
                request.git_url,
                temp_dir,
                branch=request.branch,
                depth=1
            )
            repo_path = temp_dir

        elif request.repo_path:
            repo_path = request.repo_path
            if not Path(repo_path).exists():
                raise HTTPException(status_code=400, detail="Repository path does not exist")

        else:
            raise HTTPException(status_code=400, detail="Either git_url or repo_path must be provided")

        # Analyze repository
        analyzer = AIAnalyzer()
        analysis = analyzer.analyze_repository(repo_path)

        logger.info(f"Analysis complete: {analysis.detected_language}")

        return analysis

    except git.GitCommandError as e:
        logger.error(f"Git clone failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to clone repository: {str(e)}")

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    finally:
        # Cleanup temp directory
        if temp_dir and Path(temp_dir).exists():
            shutil.rmtree(temp_dir)


@router.post("/analyze-and-deploy", response_model=DeploymentResponse, status_code=201)
async def analyze_and_deploy(
    request: DeployAnalyzeRequest,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(verify_api_key)
):
    """
    Analyze repository and deploy in one step

    This is a convenience endpoint that:
    1. Clones the repository
    2. Analyzes it with AI
    3. Generates deployment config
    4. Deploys the application

    Note: You still need to build and push the Docker image separately
    """

    temp_dir = None
    try:
        # Clone repository
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Cloning {request.git_url} to {temp_dir}")

        git.Repo.clone_from(
            request.git_url,
            temp_dir,
            branch=request.branch,
            depth=1
        )

        # Analyze repository
        analyzer = AIAnalyzer()
        app_name = Path(request.git_url).stem.lower().replace("_", "-")
        analysis = analyzer.analyze_repository(temp_dir, app_name=app_name)

        logger.info(f"Analysis complete: {analysis.detected_language}")

        # Merge user-provided env vars with suggested ones
        env_vars = request.env or {}

        # Update deployment config
        deployment_config = analysis.deployment_config
        deployment_config.domain = request.domain
        deployment_config.env = env_vars

        # Deploy application
        deployment = await create_app(deployment_config, db, api_key)

        logger.info(f"Deployed app: {app_name}")

        return deployment

    except git.GitCommandError as e:
        logger.error(f"Git clone failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to clone repository: {str(e)}")

    except Exception as e:
        logger.error(f"Deploy failed: {e}")
        raise HTTPException(status_code=500, detail=f"Deploy failed: {str(e)}")

    finally:
        # Cleanup temp directory
        if temp_dir and Path(temp_dir).exists():
            shutil.rmtree(temp_dir)


@router.post("/generate-dockerfile")
async def generate_dockerfile(
    request: AnalyzeRequest,
    api_key: APIKey = Depends(verify_api_key)
):
    """
    Generate a Dockerfile based on repository analysis
    """

    temp_dir = None
    try:
        # Determine repo path
        if request.git_url:
            temp_dir = tempfile.mkdtemp()
            git.Repo.clone_from(
                request.git_url,
                temp_dir,
                branch=request.branch,
                depth=1
            )
            repo_path = temp_dir
        elif request.repo_path:
            repo_path = request.repo_path
        else:
            raise HTTPException(status_code=400, detail="Either git_url or repo_path must be provided")

        # Analyze and generate Dockerfile
        analyzer = AIAnalyzer()
        analysis = analyzer.analyze_repository(repo_path)
        dockerfile = analyzer.generate_dockerfile(analysis, repo_path)

        return {
            "dockerfile": dockerfile,
            "analysis": analysis
        }

    except Exception as e:
        logger.error(f"Dockerfile generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate Dockerfile: {str(e)}")

    finally:
        if temp_dir and Path(temp_dir).exists():
            shutil.rmtree(temp_dir)
