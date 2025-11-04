# App-Sink 🚀

**Kubernetes Abstraction Layer** - Deploy apps to K3s with a simple API or CLI

App-Sink provides a simple REST API and intelligent CLI to deploy and manage applications on a lightweight Kubernetes (K3s) cluster. Perfect for self-hosted multi-app deployments on a single VM.

## Features

- 🤖 **AI-Powered Deployment** - CLI analyzes your repo and generates optimal K8s configs
- 🔌 **Simple REST API** - Deploy apps with a single HTTP request
- 🔒 **Secure by Default** - API keys, SSL/TLS via Let's Encrypt, namespace isolation
- 📦 **Zero-Config Deployments** - Automatic service discovery and ingress routing
- 🔄 **CI/CD Ready** - Easy integration with GitHub Actions, GitLab CI, etc.
- 📊 **Built-in Monitoring** - Prometheus & Grafana included
- ⚡ **Lightweight** - Runs on K3s, minimal resource footprint

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         VM/Server                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌─────────────────────────┐  │
│  │  App-Sink API    │◄────────┤  K3s Kubernetes Cluster │  │
│  │  (FastAPI)       │         │                         │  │
│  │                  │         │  ┌─────────┐ ┌────────┐ │  │
│  │ - Auth & API Keys│         │  │  App 1  │ │ App 2  │ │  │
│  │ - Deployment Mgmt│         │  │  (Pod)  │ │ (Pod)  │ │  │
│  │ - AI Integration │         │  └─────────┘ └────────┘ │  │
│  │ - PostgreSQL DB  │         │                         │  │
│  └──────────────────┘         │  ┌──────────────────┐  │  │
│          ▲                     │  │ Traefik Ingress  │  │  │
│          │                     │  └──────────────────┘  │  │
│          │                     └─────────────────────────┘  │
└──────────┼──────────────────────────────────────────────────┘
           │
    ┌──────┴───────┐
    │              │
┌───▼────┐  ┌─────▼──────┐
│  CLI   │  │   CI/CD    │
│  Tool  │  │  Pipeline  │
└────────┘  └────────────┘
```

## Quick Start

### 1. Install on VM

```bash
# Clone repository
git clone https://github.com/yourusername/app-sink.git
cd app-sink

# Run setup (installs K3s, API, CLI)
sudo ./scripts/setup.sh

# Get your API key
sudo app-sink api-key create --name "my-ci-cd"
```

### 2. Deploy with CLI (AI-Powered)

```bash
# Install CLI locally
pip install app-sink-cli

# Configure
app-sink config set endpoint https://your-vm.com
app-sink config set api-key YOUR_API_KEY

# Deploy from any app repo
cd ~/my-awesome-app
app-sink deploy

# ↳ AI analyzes your code
# ↳ Detects: Node.js app, port 3000, needs PostgreSQL
# ↳ Generates manifest
# ↳ Deploys to K3s
# ↳ Sets up SSL & domain
```

### 3. Deploy with API (CI/CD)

```bash
# In your CI/CD pipeline
curl -X POST https://your-vm.com/api/v1/apps \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "name": "my-app",
    "image": "ghcr.io/user/my-app:v1.0",
    "port": 3000,
    "domain": "myapp.example.com"
  }'
```

## CLI Usage

### Deploy Applications

```bash
# Auto-detect and deploy
app-sink deploy

# With custom domain
app-sink deploy --domain myapp.example.com

# With environment variables
app-sink deploy --env DATABASE_URL=postgres://... --env API_KEY=secret

# Dry run (see generated manifest)
app-sink deploy --dry-run
```

### Manage Applications

```bash
# List all apps
app-sink list

# Get app details
app-sink get my-app

# View logs
app-sink logs my-app --follow

# Scale app
app-sink scale my-app --replicas 3

# Update image
app-sink update my-app --image ghcr.io/user/my-app:v2.0

# Rollback
app-sink rollback my-app

# Delete app
app-sink delete my-app
```

### AI Analysis

```bash
# Analyze repo without deploying
app-sink analyze

# Output:
# Detected: Node.js 20.x
# Package manager: npm
# Entry point: src/index.js
# Port: 3000
# Dependencies: PostgreSQL, Redis
# Recommended resources: 512Mi RAM, 0.5 CPU
```

## API Documentation

### Authentication

All API requests require an API key:

```bash
Authorization: Bearer YOUR_API_KEY
```

### Endpoints

#### Deploy Application

```http
POST /api/v1/apps
Content-Type: application/json

{
  "name": "my-app",
  "image": "registry.example.com/my-app:v1.0",
  "port": 3000,
  "domain": "myapp.example.com",
  "env": {
    "DATABASE_URL": "postgres://...",
    "API_KEY": "secret"
  },
  "resources": {
    "cpu": "500m",
    "memory": "512Mi"
  },
  "replicas": 2,
  "healthcheck": {
    "path": "/health",
    "interval": 30
  }
}
```

#### List Applications

```http
GET /api/v1/apps
```

#### Get Application Details

```http
GET /api/v1/apps/{app_name}
```

#### Update Application

```http
PUT /api/v1/apps/{app_name}

{
  "image": "registry.example.com/my-app:v2.0",
  "replicas": 3
}
```

#### Scale Application

```http
PUT /api/v1/apps/{app_name}/scale

{
  "replicas": 5
}
```

#### Get Logs

```http
GET /api/v1/apps/{app_name}/logs?tail=100&follow=true
```

#### Rollback Application

```http
POST /api/v1/apps/{app_name}/rollback
```

#### Delete Application

```http
DELETE /api/v1/apps/{app_name}
```

#### AI-Powered Deployment

```http
POST /api/v1/apps/analyze-and-deploy
Content-Type: application/json

{
  "git_url": "https://github.com/user/my-app.git",
  "branch": "main",
  "domain": "myapp.example.com"
}
```

## Configuration

### Server Configuration

Edit `/etc/app-sink/config.yaml`:

```yaml
server:
  host: 0.0.0.0
  port: 8000
  workers: 4

database:
  url: postgresql://app-sink:password@localhost/app-sink

kubernetes:
  kubeconfig: /etc/rancher/k3s/k3s.yaml
  namespace_prefix: app-

ingress:
  class: traefik
  tls_issuer: letsencrypt-prod
  default_domain: apps.example.com

ai:
  provider: anthropic  # or openai
  api_key: sk-...
  model: claude-3-5-sonnet-20241022

registry:
  enabled: true
  url: registry.local:5000
```

### CLI Configuration

```bash
# Interactive setup
app-sink config init

# Manual configuration
app-sink config set endpoint https://your-vm.com
app-sink config set api-key YOUR_API_KEY
app-sink config set default-domain apps.example.com
```

## CI/CD Integration Examples

### GitHub Actions

```yaml
name: Deploy to App-Sink

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker Image
        run: |
          docker build -t ghcr.io/${{ github.repository }}:${{ github.sha }} .
          docker push ghcr.io/${{ github.repository }}:${{ github.sha }}

      - name: Deploy to App-Sink
        run: |
          curl -X POST ${{ secrets.APP_SINK_URL }}/api/v1/apps/my-app \
            -H "Authorization: Bearer ${{ secrets.APP_SINK_API_KEY }}" \
            -d "{\"image\": \"ghcr.io/${{ github.repository }}:${{ github.sha }}\"}"
```

### GitLab CI

```yaml
deploy:
  stage: deploy
  script:
    - |
      curl -X PUT $APP_SINK_URL/api/v1/apps/my-app \
        -H "Authorization: Bearer $APP_SINK_API_KEY" \
        -d "{\"image\": \"$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA\"}"
  only:
    - main
```

## How It Works

### 1. AI-Powered Analysis

The CLI uses AI (Claude or GPT) to analyze your repository:

1. Scans files: `package.json`, `Dockerfile`, `requirements.txt`, etc.
2. Detects framework: Node.js, Python, Go, Ruby, etc.
3. Identifies dependencies: Databases, caches, message queues
4. Determines resource requirements
5. Generates optimized Kubernetes manifests

### 2. Deployment Process

```
1. CLI/API receives deployment request
   ↓
2. Validates configuration
   ↓
3. Generates Kubernetes resources:
   - Namespace
   - Deployment
   - Service
   - Ingress (with TLS)
   - ConfigMap
   - Secrets
   ↓
4. Applies to K3s cluster
   ↓
5. K3s orchestrates:
   - Pulls container image
   - Starts pods
   - Configures networking
   ↓
6. Traefik configures routing:
   - Issues SSL certificate (Let's Encrypt)
   - Routes domain → service
   ↓
7. Application is live!
```

## Resource Requirements

### Minimal Setup
- 2 CPU cores
- 4 GB RAM
- 20 GB storage
- Supports: ~10 small apps

### Recommended
- 4 CPU cores
- 8 GB RAM
- 50 GB storage
- Supports: ~50 apps

### Production
- 8+ CPU cores
- 16+ GB RAM
- 100+ GB storage
- Supports: 100+ apps

## Monitoring

Access built-in monitoring:

```bash
# Prometheus
https://your-vm.com/prometheus

# Grafana
https://your-vm.com/grafana
# Default: admin / app-sink-admin
```

## Security

- **API Authentication**: Bearer token authentication
- **TLS/SSL**: Automatic via Let's Encrypt
- **Namespace Isolation**: Each app in separate namespace
- **Network Policies**: Restricted inter-pod communication
- **Secret Management**: Encrypted at rest
- **RBAC**: Role-based access control

## Troubleshooting

```bash
# Check API status
app-sink status

# View system logs
sudo journalctl -u app-sink-api -f

# Check K3s cluster
sudo k3s kubectl get pods --all-namespaces

# Restart services
sudo systemctl restart app-sink-api
sudo systemctl restart k3s
```

## Development

```bash
# Clone repository
git clone https://github.com/yourusername/app-sink.git
cd app-sink

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run API locally
cd api
uvicorn main:app --reload

# Run tests
pytest

# Install CLI in development mode
cd cli
pip install -e .
```

## Roadmap

- [ ] Multi-node K3s cluster support
- [ ] Built-in database provisioning (PostgreSQL, MySQL, Redis)
- [ ] Automatic backup & restore
- [ ] Blue/green deployments
- [ ] Canary releases
- [ ] Cost estimation & resource optimization
- [ ] Web UI dashboard
- [ ] Marketplace for pre-configured apps

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- Documentation: https://docs.app-sink.io
- Issues: https://github.com/yourusername/app-sink/issues
- Discussions: https://github.com/yourusername/app-sink/discussions
