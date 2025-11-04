# Cloud Native Buildpacks Integration

**Build Docker images WITHOUT writing Dockerfiles!** 🚀

App-Sink now supports **Cloud Native Buildpacks** (CNCF) for automatic image building from Git repositories.

## 🎯 What are Buildpacks?

Buildpacks automatically detect your application's language/framework and build an optimized Docker image - no Dockerfile needed!

### Traditional Way (WITH Dockerfile):
```bash
# You write:
FROM node:18
COPY package*.json ./
RUN npm install
COPY . .
CMD ["node", "server.js"]

# Then:
docker build -t myapp .
docker push myapp
kubectl apply -f deployment.yaml
```

### With Buildpacks (NO Dockerfile):
```bash
# You just push code:
git push

# App-Sink does everything:
✅ Detects: Node.js + Express
✅ Builds optimized image
✅ Pushes to registry
✅ Deploys to Kubernetes
```

## 🚀 Quick Start

### Prerequisites

1. **Install Pack CLI:**

**macOS:**
```bash
brew install buildpacks/tap/pack
```

**Linux:**
```bash
curl -sSL 'https://github.com/buildpacks/pack/releases/download/v0.32.1/pack-v0.32.1-linux.tgz' | sudo tar -C /usr/local/bin/ --no-same-owner -xzv pack
```

**Windows:**
```powershell
choco install pack
```

2. **Docker Registry** (one of):
   - Local: `docker run -d -p 5000:5000 --restart=always --name registry registry:2`
   - GHCR: Use GitHub Container Registry
   - Docker Hub: Use your Docker Hub account

3. **Configure App-Sink:**

Add to `.env`:
```env
DOCKER_REGISTRY_URL=localhost:5000
# or
DOCKER_REGISTRY_URL=ghcr.io/youruser
```

## 📖 Usage

### Option 1: API Call

```bash
curl -X POST http://localhost:8000/api/v1/build-and-deploy \
  -H "Authorization: Bearer ask_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "git_url": "https://github.com/user/myapp",
    "name": "myapp",
    "branch": "main",
    "replicas": 2
  }'
```

Response:
```json
{
  "deployment_id": "abc123",
  "name": "myapp",
  "image": "building...",
  "git_url": "https://github.com/user/myapp",
  "status": "building",
  "message": "Build started in background. Use GET /apps/myapp to check status."
}
```

### Option 2: MCP Server (via Claude Code)

```
User: "Build and deploy my app from github.com/user/myapp without a Dockerfile"

Claude: [Uses app_sink_build_and_deploy]
        🚀 Build and deploy started!
        ✨ No Dockerfile needed - using Cloud Native Buildpacks!

        Status: building

        The build is running in the background.
```

### Option 3: CLI (coming soon)

```bash
app-sink build-and-deploy \
  --git-url https://github.com/user/myapp \
  --name myapp \
  --replicas 3
```

## 🔍 How It Works

```
┌─────────────────────────────────────────┐
│ 1. You: POST /build-and-deploy         │
│    {                                    │
│      "git_url": "github.com/user/app",  │
│      "name": "myapp"                    │
│    }                                    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│ 2. App-Sink: Clone Repository           │
│    git clone github.com/user/app        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│ 3. Buildpack: Detect Language           │
│    ✅ Found package.json → Node.js      │
│    ✅ Detected: Express framework       │
│    ✅ Port: 3000 (from package.json)    │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│ 4. Buildpack: Build Image               │
│    pack build myapp                      │
│    ✅ Install Node.js 18.x              │
│    ✅ Run npm install                   │
│    ✅ Optimize for production           │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│ 5. Push to Registry                     │
│    docker push localhost:5000/myapp     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│ 6. Deploy to Kubernetes                 │
│    kubectl apply -f deployment.yaml     │
│    ✅ Deployment created                │
│    ✅ Service exposed                   │
│    ✅ Ingress configured                │
└─────────────────────────────────────────┘
```

## 📦 Supported Languages

Buildpacks auto-detect these languages:

| Language | Detection File | Builder |
|----------|---------------|---------|
| Node.js | package.json | paketobuildpacks/builder:base |
| Python | requirements.txt, Pipfile | paketobuildpacks/builder:base |
| Go | go.mod | paketobuildpacks/builder:base |
| Ruby | Gemfile | paketobuildpacks/builder:base |
| Java | pom.xml, build.gradle | paketobuildpacks/builder:base |
| PHP | composer.json | paketobuildpacks/builder:base |
| .NET | *.csproj | paketobuildpacks/builder:base |

## ⚙️ Configuration

### Environment Variables

Pass build-time environment variables:

```json
{
  "git_url": "github.com/user/app",
  "name": "myapp",
  "environment_variables": {
    "NODE_ENV": "production",
    "API_URL": "https://api.example.com"
  }
}
```

### Custom Builder

Use a different buildpack builder:

```json
{
  "git_url": "github.com/user/app",
  "name": "myapp",
  "builder": "paketobuildpacks/builder:tiny"
}
```

Available builders:
- `paketobuildpacks/builder:base` - Most languages (default)
- `paketobuildpacks/builder:full` - All languages + extras
- `paketobuildpacks/builder:tiny` - Minimal (Go, Java)

### Private Repositories

For private Git repos, use SSH or access tokens:

```bash
# SSH (add SSH key to App-Sink host):
git_url: "git@github.com:user/private-app.git"

# HTTPS with token:
git_url: "https://TOKEN@github.com/user/private-app.git"
```

## 🎯 Real-World Examples

### Example 1: Node.js Express App

**Repository:** `github.com/user/express-api`

```
express-api/
├── package.json
├── server.js
└── routes/
```

**Deploy:**
```bash
curl -X POST localhost:8000/api/v1/build-and-deploy \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "git_url": "https://github.com/user/express-api",
    "name": "api",
    "replicas": 3
  }'
```

**Result:**
- ✅ Detects Node.js 18
- ✅ Runs `npm install`
- ✅ Exposes port 3000
- ✅ Deployed with 3 replicas

### Example 2: Python Flask App

**Repository:** `github.com/user/flask-app`

```
flask-app/
├── requirements.txt
├── app.py
└── templates/
```

**Deploy via MCP:**
```
User: "Build my Flask app from github.com/user/flask-app and deploy it"

Claude: [Calls app_sink_build_and_deploy]
        🚀 Build started!
        Language: Python
        Framework: Flask
        Status: building...
```

### Example 3: Go Microservice

**Repository:** `github.com/user/go-service`

```
go-service/
├── go.mod
├── go.sum
└── main.go
```

**Deploy:**
```bash
POST /api/v1/build-and-deploy
{
  "git_url": "https://github.com/user/go-service",
  "name": "go-svc",
  "builder": "paketobuildpacks/builder:tiny",
  "replicas": 5
}
```

**Result:**
- ✅ Minimal image (< 50MB)
- ✅ Optimized for Go
- ✅ Fast startup

## 🔒 Security

### Best Practices

1. **Private Registry:** Use authenticated registry
2. **Scan Images:** Add vulnerability scanning
3. **Resource Limits:** Set CPU/memory limits
4. **Network Policies:** Isolate workloads

### Image Security

Buildpacks provide:
- ✅ Regular security updates
- ✅ Minimal attack surface
- ✅ Non-root user by default
- ✅ SBOM (Software Bill of Materials)

## 📊 Monitoring Build Progress

Check build status:

```bash
# Get deployment status
GET /api/v1/apps/myapp

Response:
{
  "name": "myapp",
  "status": "building",  # or "running", "failed"
  "image": "building..." # or full image tag when done
}
```

## ❌ Troubleshooting

### "Pack CLI not found"

Install pack:
```bash
brew install buildpacks/tap/pack  # macOS
# or see installation instructions above
```

### "Failed to push image"

Check registry authentication:
```bash
docker login localhost:5000
# or
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

### "Build timed out"

Increase timeout in `buildpack.py`:
```python
timeout=600  # 10 minutes → 1200 (20 minutes)
```

### "Unsupported language"

Add custom buildpack or use Dockerfile deployment instead.

## 🆚 Buildpacks vs Dockerfile

| Feature | Buildpacks | Dockerfile |
|---------|-----------|------------|
| Setup | Zero config | Write Dockerfile |
| Security | Auto-updates | Manual updates |
| Optimization | Automatic | Manual tuning |
| Consistency | Guaranteed | Varies by author |
| Control | Limited | Full control |
| Learning Curve | Easy | Medium |

**Use Buildpacks when:**
- ✅ Standard web applications
- ✅ Teams without DevOps expertise
- ✅ Fast iteration/prototyping
- ✅ Heroku-style workflows

**Use Dockerfile when:**
- ✅ Custom base images needed
- ✅ Exotic system dependencies
- ✅ Minimal image size critical
- ✅ Full control required

## 🔗 Links

- [Cloud Native Buildpacks](https://buildpacks.io/)
- [Paketo Buildpacks](https://paketo.io/)
- [Pack CLI Docs](https://buildpacks.io/docs/tools/pack/)
- [Buildpack Spec](https://github.com/buildpacks/spec)

## 🎓 Further Reading

- [Why Buildpacks?](https://buildpacks.io/docs/concepts/)
- [Writing Custom Buildpacks](https://buildpacks.io/docs/buildpack-author-guide/)
- [Cloud Native Computing Foundation](https://www.cncf.io/)

---

**Built with ❤️ using Paketo Buildpacks (100% Open Source, CNCF)**
