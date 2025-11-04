"""
Buildpack builder service
Uses Cloud Native Buildpacks (CNCF) to build Docker images without Dockerfile
"""

import subprocess
import tempfile
import shutil
import os
import logging
from pathlib import Path
from typing import Optional, Dict
import git

logger = logging.getLogger(__name__)


class BuildpackBuilder:
    """
    Build Docker images using Cloud Native Buildpacks (Paketo)
    Zero Dockerfile needed!
    """

    DEFAULT_BUILDER = "paketobuildpacks/builder:base"

    def __init__(self, registry_url: str = "localhost:5000"):
        """
        Initialize Buildpack builder

        Args:
            registry_url: Docker registry URL (default: localhost:5000)
        """
        self.registry_url = registry_url
        self._check_pack_installed()

    def _check_pack_installed(self):
        """Check if pack CLI is installed"""
        try:
            result = subprocess.run(
                ["pack", "version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"Pack CLI found: {result.stdout.strip()}")
            else:
                raise RuntimeError("Pack CLI not working properly")
        except FileNotFoundError:
            raise RuntimeError(
                "Pack CLI not found. Install with: "
                "(brew install buildpacks/tap/pack) or "
                "(curl -sSL 'https://github.com/buildpacks/pack/releases/download/v0.32.1/pack-v0.32.1-linux.tgz' | sudo tar -C /usr/local/bin/ --no-same-owner -xzv pack)"
            )

    def clone_repository(self, git_url: str, branch: str = "main") -> str:
        """
        Clone Git repository to temporary directory

        Args:
            git_url: Git repository URL
            branch: Branch to clone (default: main)

        Returns:
            Path to cloned repository
        """
        temp_dir = tempfile.mkdtemp(prefix="app-sink-build-")
        logger.info(f"Cloning {git_url} (branch: {branch}) to {temp_dir}")

        try:
            # Try main branch first, fallback to master
            try:
                git.Repo.clone_from(git_url, temp_dir, branch=branch, depth=1)
            except git.exc.GitCommandError:
                logger.info(f"Branch {branch} not found, trying 'master'")
                git.Repo.clone_from(git_url, temp_dir, branch="master", depth=1)

            logger.info(f"Repository cloned successfully to {temp_dir}")
            return temp_dir
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(f"Failed to clone repository: {str(e)}")

    def build_image(
        self,
        source_path: str,
        image_name: str,
        builder: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Build Docker image using Cloud Native Buildpacks

        Args:
            source_path: Path to source code
            image_name: Name for the built image
            builder: Buildpack builder to use (default: paketobuildpacks/builder:base)
            env_vars: Environment variables for build

        Returns:
            Full image tag
        """
        builder = builder or self.DEFAULT_BUILDER
        full_image_tag = f"{self.registry_url}/{image_name}"

        logger.info(f"Building image {full_image_tag} from {source_path}")
        logger.info(f"Using builder: {builder}")

        # Build pack command
        cmd = [
            "pack", "build",
            full_image_tag,
            "--path", source_path,
            "--builder", builder,
            "--trust-builder"
        ]

        # Add environment variables
        if env_vars:
            for key, value in env_vars.items():
                cmd.extend(["--env", f"{key}={value}"])

        try:
            # Run pack build
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes timeout
                cwd=source_path
            )

            if result.returncode != 0:
                logger.error(f"Build failed: {result.stderr}")
                raise RuntimeError(f"Buildpack build failed: {result.stderr}")

            logger.info(f"Image built successfully: {full_image_tag}")
            logger.debug(f"Build output: {result.stdout}")

            return full_image_tag

        except subprocess.TimeoutExpired:
            raise RuntimeError("Build timed out after 10 minutes")
        except Exception as e:
            raise RuntimeError(f"Build failed: {str(e)}")

    def push_image(self, image_tag: str) -> None:
        """
        Push image to registry

        Args:
            image_tag: Full image tag to push
        """
        logger.info(f"Pushing image {image_tag}")

        try:
            result = subprocess.run(
                ["docker", "push", image_tag],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes
            )

            if result.returncode != 0:
                logger.error(f"Push failed: {result.stderr}")
                raise RuntimeError(f"Failed to push image: {result.stderr}")

            logger.info(f"Image pushed successfully: {image_tag}")

        except subprocess.TimeoutExpired:
            raise RuntimeError("Push timed out after 5 minutes")
        except Exception as e:
            raise RuntimeError(f"Push failed: {str(e)}")

    def build_from_git(
        self,
        git_url: str,
        image_name: str,
        branch: str = "main",
        builder: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        push: bool = True
    ) -> str:
        """
        Complete workflow: Clone → Build → Push

        Args:
            git_url: Git repository URL
            image_name: Name for the image
            branch: Git branch
            builder: Buildpack builder to use
            env_vars: Environment variables
            push: Whether to push to registry

        Returns:
            Full image tag
        """
        temp_dir = None
        try:
            # Clone repository
            temp_dir = self.clone_repository(git_url, branch)

            # Build image
            image_tag = self.build_image(
                source_path=temp_dir,
                image_name=image_name,
                builder=builder,
                env_vars=env_vars
            )

            # Push to registry
            if push:
                self.push_image(image_tag)

            return image_tag

        finally:
            # Cleanup
            if temp_dir and os.path.exists(temp_dir):
                logger.info(f"Cleaning up {temp_dir}")
                shutil.rmtree(temp_dir, ignore_errors=True)

    def detect_builder(self, source_path: str) -> str:
        """
        Detect which buildpack builder to use based on project files

        Args:
            source_path: Path to source code

        Returns:
            Recommended builder
        """
        files = os.listdir(source_path)

        # Language-specific builders (faster than base)
        if "package.json" in files:
            return "paketobuildpacks/builder:base"  # Node.js
        elif "requirements.txt" in files or "Pipfile" in files:
            return "paketobuildpacks/builder:base"  # Python
        elif "go.mod" in files:
            return "paketobuildpacks/builder:base"  # Go
        elif "Gemfile" in files:
            return "paketobuildpacks/builder:base"  # Ruby
        elif "pom.xml" in files or "build.gradle" in files:
            return "paketobuildpacks/builder:base"  # Java
        elif "composer.json" in files:
            return "paketobuildpacks/builder:base"  # PHP
        else:
            return self.DEFAULT_BUILDER
