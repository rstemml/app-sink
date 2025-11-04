# Quick Start Guide

## Installation

### 1. On Your VM (Server)

```bash
# Clone the repository
git clone https://github.com/yourusername/app-sink.git
cd app-sink

# Run setup (requires root)
sudo ./scripts/setup.sh
```

The setup script will:
- Install K3s (lightweight Kubernetes)
- Install PostgreSQL database
- Install App-Sink API
- Install App-Sink CLI
- Configure Traefik ingress controller
- Generate initial API key

### 2. On Your Local Machine (Client)

```bash
# Install CLI
pip install app-sink-cli

# Configure
app-sink config init

# Follow prompts to enter:
# - API Endpoint: https://your-vm-ip-or-domain
# - API Key: (from setup script output)
```

## First Deployment

### Method 1: Using CLI (AI-Powered)

```bash
# Navigate to your application directory
cd my-awesome-app

# Deploy with AI analysis
app-sink deploy --image ghcr.io/username/my-app:v1.0

# The CLI will:
# 1. Analyze your code with AI
# 2. Detect language, framework, dependencies
# 3. Generate optimal Kubernetes configuration
# 4. Deploy to your cluster
```

### Method 2: Using API (CI/CD)

```bash
curl -X POST https://your-vm/api/v1/apps \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-app",
    "image": "ghcr.io/username/my-app:v1.0",
    "port": 3000,
    "domain": "myapp.example.com",
    "replicas": 2
  }'
```

## Managing Applications

### List Apps
```bash
app-sink list
```

### Get Details
```bash
app-sink get my-app
```

### View Logs
```bash
app-sink logs my-app --tail 100 --follow
```

### Scale
```bash
app-sink scale my-app 5
```

### Update
```bash
app-sink update my-app --image ghcr.io/username/my-app:v2.0
```

### Rollback
```bash
app-sink rollback my-app
```

### Delete
```bash
app-sink delete my-app
```

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: |
          docker build -t ghcr.io/${{ github.repository }}:${{ github.sha }} .
          docker push ghcr.io/${{ github.repository }}:${{ github.sha }}

      - name: Deploy
        run: |
          pip install app-sink-cli
          app-sink config set endpoint ${{ secrets.APP_SINK_URL }}
          app-sink config set api-key ${{ secrets.APP_SINK_API_KEY }}
          app-sink deploy --image ghcr.io/${{ github.repository }}:${{ github.sha }}
```

## DNS Configuration

Point your domain to your VM:

```
A     myapp.example.com    -> YOUR_VM_IP
A     *.apps.example.com   -> YOUR_VM_IP  (wildcard)
```

Traefik will automatically provision SSL certificates via Let's Encrypt.

## Monitoring

Access monitoring dashboards:

- **Grafana**: https://your-vm/grafana
  - User: admin
  - Password: app-sink-admin

- **Prometheus**: https://your-vm/prometheus

## Troubleshooting

### Check API Status
```bash
app-sink status
```

### Check Kubernetes
```bash
sudo k3s kubectl get pods --all-namespaces
```

### View API Logs
```bash
sudo journalctl -u app-sink-api -f
```

### Restart Services
```bash
sudo systemctl restart app-sink-api
sudo systemctl restart k3s
```

## Next Steps

- Read the [full documentation](../README.md)
- Check [CI/CD examples](../examples/)
- Explore [Kubernetes templates](../k8s-templates/)
