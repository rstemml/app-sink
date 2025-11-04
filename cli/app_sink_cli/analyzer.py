"""
Local repository analyzer using AI
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional
import anthropic

from .config import config


class LocalAnalyzer:
    """Analyzes local repositories using AI"""

    def __init__(self):
        # Try to get AI key from config or env
        self.ai_key = config.get("ai_api_key") or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.ai_provider = config.get("ai_provider", "anthropic")

        if self.ai_key and self.ai_provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=self.ai_key)
        else:
            self.client = None

    def _scan_files(self, repo_path: str) -> Dict[str, str]:
        """Scan important files in repository"""
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
        ]

        for file_name in important_files:
            file_path = repo_path / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files_content[file_name] = f.read()[:5000]
                except:
                    pass

        return files_content

    def _simple_analysis(self, files: Dict[str, str], app_name: Optional[str] = None) -> Dict:
        """Simple rule-based analysis (fallback when no AI available)"""
        detected_language = "unknown"
        detected_framework = None
        package_manager = None
        entry_point = None
        detected_port = 8080
        dependencies = []

        # Detect language and framework
        if "package.json" in files:
            detected_language = "node"
            package_manager = "npm"
            try:
                pkg = json.loads(files["package.json"])
                dependencies = list(pkg.get("dependencies", {}).keys())[:10]
                if "express" in dependencies:
                    detected_framework = "express"
                    detected_port = 3000
                elif "next" in dependencies:
                    detected_framework = "nextjs"
                    detected_port = 3000
                elif "@nestjs/core" in dependencies:
                    detected_framework = "nestjs"
                    detected_port = 3000
            except:
                pass

        elif "requirements.txt" in files:
            detected_language = "python"
            package_manager = "pip"
            dependencies = [line.split("==")[0] for line in files["requirements.txt"].split("\n") if line and not line.startswith("#")][:10]
            if any("fastapi" in dep.lower() for dep in dependencies):
                detected_framework = "fastapi"
                detected_port = 8000
            elif any("django" in dep.lower() for dep in dependencies):
                detected_framework = "django"
                detected_port = 8000
            elif any("flask" in dep.lower() for dep in dependencies):
                detected_framework = "flask"
                detected_port = 5000

        elif "go.mod" in files:
            detected_language = "go"
            package_manager = "go"
            detected_port = 8080

        elif "Cargo.toml" in files:
            detected_language = "rust"
            package_manager = "cargo"
            detected_port = 8080

        elif "Gemfile" in files:
            detected_language = "ruby"
            package_manager = "bundler"
            detected_framework = "rails" if "rails" in files["Gemfile"].lower() else None
            detected_port = 3000

        # Generate app name
        if not app_name:
            app_name = Path(os.getcwd()).name.lower().replace("_", "-")

        return {
            "detected_language": detected_language,
            "detected_framework": detected_framework,
            "package_manager": package_manager,
            "entry_point": entry_point,
            "detected_port": detected_port,
            "dependencies": dependencies,
            "recommended_resources": {
                "cpu": "500m",
                "memory": "512Mi"
            },
            "suggested_env_vars": [],
            "deployment_config": {
                "name": app_name,
                "image": f"placeholder/{app_name}:latest",
                "port": detected_port,
                "resources": {
                    "cpu": "500m",
                    "memory": "512Mi"
                },
                "healthcheck": {
                    "path": "/health",
                    "interval": 30
                }
            },
            "confidence": 0.7
        }

    def _ai_analysis(self, files: Dict[str, str], app_name: Optional[str] = None) -> Dict:
        """AI-powered analysis using Claude"""
        files_str = "\n\n".join([
            f"=== {filename} ===\n{content}"
            for filename, content in files.items()
        ])

        prompt = f"""Analyze this application repository and provide deployment configuration.

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
    "recommended_cpu": "string (e.g., 500m, 1)",
    "recommended_memory": "string (e.g., 512Mi, 1Gi)",
    "environment_variables": ["list", "of", "required", "env", "vars"],
    "health_check_path": "string (e.g., /health, /api/health)",
    "confidence": "float 0.0-1.0"
}}

Return ONLY valid JSON, no additional text.
"""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text

            # Extract JSON
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_str = response_text[start_idx:end_idx]

            analysis = json.loads(json_str)

            # Generate app name
            if not app_name:
                app_name = Path(os.getcwd()).name.lower().replace("_", "-")

            return {
                "detected_language": analysis.get("detected_language", "unknown"),
                "detected_framework": analysis.get("detected_framework"),
                "package_manager": analysis.get("package_manager"),
                "entry_point": analysis.get("entry_point"),
                "detected_port": analysis.get("detected_port", 8080),
                "dependencies": analysis.get("dependencies", []),
                "recommended_resources": {
                    "cpu": analysis.get("recommended_cpu", "500m"),
                    "memory": analysis.get("recommended_memory", "512Mi")
                },
                "suggested_env_vars": analysis.get("environment_variables", []),
                "deployment_config": {
                    "name": app_name,
                    "image": f"placeholder/{app_name}:latest",
                    "port": analysis.get("detected_port", 8080),
                    "resources": {
                        "cpu": analysis.get("recommended_cpu", "500m"),
                        "memory": analysis.get("recommended_memory", "512Mi")
                    },
                    "healthcheck": {
                        "path": analysis.get("health_check_path", "/health"),
                        "interval": 30
                    }
                },
                "confidence": analysis.get("confidence", 0.8)
            }

        except Exception as e:
            print(f"AI analysis failed: {e}")
            # Fallback to simple analysis
            return self._simple_analysis(files, app_name)

    def analyze_local_repo(self, repo_path: str = ".", app_name: Optional[str] = None) -> Dict:
        """
        Analyze local repository

        Args:
            repo_path: Path to repository
            app_name: Optional app name

        Returns:
            Analysis result
        """
        files = self._scan_files(repo_path)

        if not files:
            raise ValueError("No recognizable files found in repository")

        # Use AI if available, otherwise simple analysis
        if self.client:
            return self._ai_analysis(files, app_name)
        else:
            return self._simple_analysis(files, app_name)
