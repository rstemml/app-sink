"""
AI-powered repository analysis using Claude or GPT
"""

import logging
import os
import json
from typing import Dict, Optional, List
from pathlib import Path
import anthropic
import openai

from core.config import get_settings
from models.schemas import (
    AnalyzeResponse,
    DeploymentCreate,
    ResourceRequirements,
    HealthCheck
)

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """Analyzes code repositories using AI to generate deployment configs"""

    def __init__(self):
        self.settings = get_settings()
        if self.settings.ai_provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=self.settings.ai_api_key)
        elif self.settings.ai_provider == "openai":
            openai.api_key = self.settings.ai_api_key
        else:
            raise ValueError(f"Unsupported AI provider: {self.settings.ai_provider}")

    def _scan_repository(self, repo_path: str) -> Dict[str, str]:
        """Scan repository files to gather context"""
        repo_path = Path(repo_path)
        files_content = {}

        # Important files to analyze
        important_files = [
            "package.json",
            "requirements.txt",
            "Pipfile",
            "go.mod",
            "Cargo.toml",
            "Gemfile",
            "composer.json",
            "Dockerfile",
            "docker-compose.yml",
            ".env.example",
            "README.md",
            "main.py",
            "app.py",
            "index.js",
            "server.js",
            "main.go",
            "main.rs"
        ]

        for file_name in important_files:
            file_path = repo_path / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files_content[file_name] = f.read()[:5000]  # Limit to 5000 chars
                except Exception as e:
                    logger.warning(f"Could not read {file_name}: {e}")

        # Scan for common entry point patterns
        common_paths = [
            "src/index.js",
            "src/main.py",
            "src/app.py",
            "src/server.js",
            "cmd/main.go",
            "index.ts",
            "app.ts"
        ]

        for path in common_paths:
            file_path = repo_path / path
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files_content[path] = f.read()[:3000]
                except Exception as e:
                    logger.warning(f"Could not read {path}: {e}")

        return files_content

    def _create_analysis_prompt(self, files_content: Dict[str, str]) -> str:
        """Create prompt for AI analysis"""
        files_str = "\n\n".join([
            f"=== {filename} ===\n{content}"
            for filename, content in files_content.items()
        ])

        return f"""Analyze this application repository and provide deployment configuration.

Repository files:
{files_str}

Please analyze these files and provide a JSON response with the following structure:
{{
    "detected_language": "string (e.g., node, python, go, rust, ruby, php)",
    "detected_framework": "string or null (e.g., express, fastapi, django, rails)",
    "package_manager": "string or null (e.g., npm, pip, cargo, bundler)",
    "entry_point": "string or null (main file path)",
    "detected_port": "integer or null (port the app listens on)",
    "dependencies": ["list", "of", "external", "dependencies"],
    "database_required": "boolean",
    "database_type": "string or null (postgres, mysql, redis, mongodb)",
    "cache_required": "boolean",
    "cache_type": "string or null",
    "recommended_cpu": "string (e.g., 500m, 1)",
    "recommended_memory": "string (e.g., 512Mi, 1Gi)",
    "environment_variables": ["list", "of", "required", "env", "vars"],
    "health_check_path": "string (e.g., /health, /api/health)",
    "confidence": "float 0.0-1.0"
}}

Analyze the code carefully and provide realistic resource recommendations based on the application type and complexity.
If you detect database connections, include the database type.
Look for environment variable usage and list required ones.
Detect the port from code (like app.listen(3000), uvicorn.run(port=8000), etc.)
"""

    def _call_anthropic(self, prompt: str) -> Dict:
        """Call Anthropic Claude API"""
        try:
            message = self.client.messages.create(
                model=self.settings.ai_model,
                max_tokens=2048,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text

            # Extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_str = response_text[start_idx:end_idx]

            return json.loads(json_str)

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    def _call_openai(self, prompt: str) -> Dict:
        """Call OpenAI GPT API"""
        try:
            response = openai.ChatCompletion.create(
                model=self.settings.ai_model,
                messages=[
                    {"role": "system", "content": "You are an expert DevOps engineer who analyzes code and generates deployment configurations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            response_text = response.choices[0].message.content

            # Extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_str = response_text[start_idx:end_idx]

            return json.loads(json_str)

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    def analyze_repository(self, repo_path: str, app_name: Optional[str] = None) -> AnalyzeResponse:
        """
        Analyze repository and generate deployment configuration

        Args:
            repo_path: Path to local repository
            app_name: Optional app name (will be generated if not provided)

        Returns:
            AnalyzeResponse with deployment configuration
        """
        logger.info(f"Analyzing repository: {repo_path}")

        # Scan repository files
        files_content = self._scan_repository(repo_path)

        if not files_content:
            raise ValueError("No recognizable files found in repository")

        # Create prompt
        prompt = self._create_analysis_prompt(files_content)

        # Call AI provider
        if self.settings.ai_provider == "anthropic":
            analysis = self._call_anthropic(prompt)
        else:
            analysis = self._call_openai(prompt)

        logger.info(f"Analysis complete: {analysis.get('detected_language')}")

        # Generate app name if not provided
        if not app_name:
            app_name = Path(repo_path).name.lower().replace("_", "-")

        # Create deployment config
        deployment_config = DeploymentCreate(
            name=app_name,
            image="placeholder:latest",  # Will be provided by user or CI/CD
            port=analysis.get("detected_port", 8080),
            replicas=1,
            resources=ResourceRequirements(
                cpu=analysis.get("recommended_cpu", "500m"),
                memory=analysis.get("recommended_memory", "512Mi")
            ),
            healthcheck=HealthCheck(
                path=analysis.get("health_check_path", "/health"),
                interval=30,
                timeout=5,
                initial_delay=10
            ),
            env={}
        )

        # Build response
        return AnalyzeResponse(
            detected_language=analysis.get("detected_language", "unknown"),
            detected_framework=analysis.get("detected_framework"),
            package_manager=analysis.get("package_manager"),
            entry_point=analysis.get("entry_point"),
            detected_port=analysis.get("detected_port"),
            dependencies=analysis.get("dependencies", []),
            recommended_resources=ResourceRequirements(
                cpu=analysis.get("recommended_cpu", "500m"),
                memory=analysis.get("recommended_memory", "512Mi")
            ),
            suggested_env_vars=analysis.get("environment_variables", []),
            deployment_config=deployment_config,
            confidence=analysis.get("confidence", 0.8)
        )

    def generate_dockerfile(self, analysis: AnalyzeResponse, repo_path: str) -> str:
        """Generate Dockerfile based on analysis"""
        language = analysis.detected_language.lower()

        dockerfiles = {
            "node": """FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE {port}
CMD ["npm", "start"]
""",
            "python": """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE {port}
CMD ["python", "{entry_point}"]
""",
            "go": """FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.* ./
RUN go mod download
COPY . .
RUN go build -o main .

FROM alpine:latest
WORKDIR /root/
COPY --from=builder /app/main .
EXPOSE {port}
CMD ["./main"]
""",
        }

        template = dockerfiles.get(language, dockerfiles["node"])
        return template.format(
            port=analysis.detected_port or 8080,
            entry_point=analysis.entry_point or "main.py"
        )
