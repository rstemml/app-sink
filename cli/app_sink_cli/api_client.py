"""
API client for App-Sink
"""

import requests
from typing import Dict, Optional, List
from .config import config


class APIClient:
    """Client for App-Sink API"""

    def __init__(self):
        self.endpoint = config.endpoint
        self.api_key = config.api_key

        if not self.endpoint or not self.api_key:
            raise ValueError("API endpoint and key not configured. Run: app-sink config init")

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Make API request"""
        url = f"{self.endpoint}{path}"
        response = self.session.request(method, url, **kwargs)

        if response.status_code >= 400:
            try:
                error = response.json().get("error", response.text)
            except:
                error = response.text
            raise Exception(f"API Error ({response.status_code}): {error}")

        return response

    def health(self) -> Dict:
        """Check API health"""
        return self._request("GET", "/api/v1/health").json()

    def create_app(self, deployment: Dict) -> Dict:
        """Create new app"""
        return self._request("POST", "/api/v1/apps", json=deployment).json()

    def list_apps(self) -> List[Dict]:
        """List all apps"""
        data = self._request("GET", "/api/v1/apps").json()
        return data.get("deployments", [])

    def get_app(self, name: str) -> Dict:
        """Get app details"""
        return self._request("GET", f"/api/v1/apps/{name}").json()

    def update_app(self, name: str, update: Dict) -> Dict:
        """Update app"""
        return self._request("PUT", f"/api/v1/apps/{name}", json=update).json()

    def scale_app(self, name: str, replicas: int) -> Dict:
        """Scale app"""
        return self._request("PUT", f"/api/v1/apps/{name}/scale", json={"replicas": replicas}).json()

    def delete_app(self, name: str) -> Dict:
        """Delete app"""
        return self._request("DELETE", f"/api/v1/apps/{name}").json()

    def get_logs(self, name: str, tail: int = 100) -> str:
        """Get app logs"""
        response = self._request("GET", f"/api/v1/apps/{name}/logs?tail={tail}")
        return response.json().get("logs", "")

    def rollback_app(self, name: str) -> Dict:
        """Rollback app"""
        return self._request("POST", f"/api/v1/apps/{name}/rollback").json()

    def analyze_repo(self, repo_path: str) -> Dict:
        """Analyze repository with AI"""
        return self._request("POST", "/api/v1/analyze", json={"repo_path": repo_path}).json()

    def analyze_and_deploy(self, git_url: str, branch: str = "main", domain: Optional[str] = None, env: Optional[Dict] = None) -> Dict:
        """Analyze and deploy in one step"""
        data = {
            "git_url": git_url,
            "branch": branch
        }
        if domain:
            data["domain"] = domain
        if env:
            data["env"] = env

        return self._request("POST", "/api/v1/analyze-and-deploy", json=data).json()
