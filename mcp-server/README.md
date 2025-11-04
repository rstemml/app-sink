# App-Sink MCP Server

**Deploy to Kubernetes with natural language using AI!**

MCP (Model Context Protocol) Server for [App-Sink](../README.md) - enables Claude Code, Cursor, and other AI coding tools to deploy applications directly to Kubernetes.

## 🚀 Features

- **Natural Language Deployments** - "Deploy my Node.js app to Kubernetes"
- **AI-Powered Analysis** - Automatically detects language, framework, and requirements
- **Full Kubernetes Control** - Deploy, scale, rollback, delete, and view logs
- **Zero YAML** - No Kubernetes manifests needed
- **Works with Any AI Tool** - Compatible with Claude Code, Cursor, Windsurf, etc.

## 🛠️ Available Tools

The MCP server exposes these tools to AI assistants:

### `app_sink_deploy`
Deploy an application to Kubernetes. Supports both Git repositories (with AI analysis) and Docker images.

**Parameters:**
- `name` (required) - Deployment name
- `git_url` - Git repository URL (auto-analyzed)
- `image` - Docker image (alternative to git_url)
- `port` - Application port
- `domain` - Custom domain
- `replicas` - Number of replicas (default: 1)

**Example:**
```
"Deploy my app from https://github.com/user/myapp"
```

### `app_sink_list`
List all deployments running on Kubernetes.

**Example:**
```
"Show me all my deployments"
```

### `app_sink_get_status`
Get detailed information about a specific deployment.

**Parameters:**
- `name` (required) - Deployment name

**Example:**
```
"What's the status of my api-service?"
```

### `app_sink_logs`
Get logs from a deployment.

**Parameters:**
- `name` (required) - Deployment name
- `lines` - Number of log lines (default: 100)

**Example:**
```
"Show me the last 200 lines of logs from webapp"
```

### `app_sink_scale`
Scale a deployment to a specific number of replicas.

**Parameters:**
- `name` (required) - Deployment name
- `replicas` (required) - Target replica count

**Example:**
```
"Scale my api-service to 5 replicas"
```

### `app_sink_rollback`
Rollback a deployment to the previous version.

**Parameters:**
- `name` (required) - Deployment name

**Example:**
```
"Rollback user-dashboard to the previous version"
```

### `app_sink_delete`
Delete a deployment from Kubernetes.

**Parameters:**
- `name` (required) - Deployment name

**Example:**
```
"Delete the staging-api deployment"
```

### `app_sink_analyze`
Analyze a Git repository to detect language, framework, and deployment requirements.

**Parameters:**
- `git_url` (required) - Git repository URL
- `branch` - Git branch (default: main/master)

**Example:**
```
"Analyze this repo: https://github.com/user/myapp"
```

## 📦 Installation

### Prerequisites

1. **App-Sink API** must be running
2. **API Key** from App-Sink (get from webapp or CLI)
3. **Node.js** 18+ installed

### Setup

```bash
# Clone the repository
cd app-sink/mcp-server

# Install dependencies
npm install

# Build TypeScript
npm run build
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Required
APP_SINK_API_KEY=ask_your_api_key_here

# Optional (defaults shown)
APP_SINK_API_URL=http://localhost:8000
```

### Get an API Key

**Option 1: Via Webapp**
1. Open http://localhost:5173
2. Login (admin/admin)
3. Go to "API Keys"
4. Click "New Key"
5. Copy the generated key

**Option 2: Via CLI**
```bash
cd ../cli
python -m app_sink_cli.cli config init
# Follow prompts to create API key
```

## 🎯 Usage with Claude Code

### 1. Add to Claude Code Config

Edit your Claude Code MCP settings (`~/.config/claude/mcp.json` or via settings):

```json
{
  "mcpServers": {
    "app-sink": {
      "command": "node",
      "args": ["/path/to/app-sink/mcp-server/dist/index.js"],
      "env": {
        "APP_SINK_API_KEY": "ask_your_key_here",
        "APP_SINK_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

**Or using npm (if globally installed):**
```json
{
  "mcpServers": {
    "app-sink": {
      "command": "app-sink-mcp",
      "env": {
        "APP_SINK_API_KEY": "ask_your_key_here"
      }
    }
  }
}
```

### 2. Restart Claude Code

Restart Claude Code to load the MCP server.

### 3. Start Using!

Now you can use natural language:

```
You: "Deploy my Node.js app from https://github.com/myuser/webapp"

Claude: *Uses app_sink_deploy tool*
        *Analyzes repository*
        *Creates deployment*

        ✅ Deployed successfully!
        Name: webapp
        Image: myuser/webapp:latest
        Replicas: 1
        Status: running
        Domain: webapp.k3s.local
```

## 💡 Example Conversations

### Deploy from Git
```
User: "I want to deploy my API from github.com/user/myapi.
       Scale it to 3 replicas and give it 2GB of memory."

Claude: [Uses app_sink_deploy]
        ✅ Analyzed: Python + FastAPI
        ✅ Deployed with 3 replicas
        ✅ Memory limit: 2Gi
```

### Check Status & Logs
```
User: "What's the status of my deployments?"

Claude: [Uses app_sink_list]
        You have 3 deployments:
        1. webapp - 2 replicas - running
        2. api-service - 3 replicas - running
        3. worker - 1 replica - running

User: "Show me logs from api-service"

Claude: [Uses app_sink_logs]
        [Displays last 100 lines of logs]
```

### Scale & Rollback
```
User: "My api-service is getting too much traffic, scale it to 10"

Claude: [Uses app_sink_scale]
        ✅ Scaled api-service to 10 replicas

User: "Actually that broke something, rollback to the previous version"

Claude: [Uses app_sink_rollback]
        ✅ Rolled back api-service to previous image
```

### Multi-Step Workflows
```
User: "Deploy my webapp from github.com/user/webapp,
       then check if it's running,
       and show me the logs"

Claude: [Uses app_sink_deploy]
        ✅ Deployed webapp

        [Uses app_sink_get_status]
        Status: running, 1 replica

        [Uses app_sink_logs]
        [Shows logs confirming app started successfully]
```

## 🧪 Testing

Test the MCP server manually:

```bash
# Start in dev mode
npm run dev

# The server will wait for MCP protocol messages on stdin/stdout
# You can test with the MCP inspector or Claude Code
```

## 🔒 Security

- **API Keys** are transmitted via Bearer token authentication
- **HTTPS** recommended for production API endpoints
- **Rate Limiting** - App-Sink API should have rate limits configured
- **Audit Logs** - All MCP actions are logged by App-Sink

## 🐛 Troubleshooting

### "API Key required" error
Make sure `APP_SINK_API_KEY` is set in your MCP config.

### "Connection refused"
Check that App-Sink API is running:
```bash
curl http://localhost:8000/api/v1/health
```

### "Invalid API key"
Verify your API key is active:
1. Open webapp
2. Go to API Keys
3. Check if your key is active

### MCP Server not showing in Claude Code
1. Check `~/.config/claude/mcp.json` syntax
2. Restart Claude Code completely
3. Check Claude Code logs for errors

## 📊 Architecture

```
┌─────────────────┐
│  Claude Code    │
│  (or Cursor)    │
└────────┬────────┘
         │ MCP Protocol
         │
┌────────▼────────┐
│   MCP Server    │
│  (this package) │
└────────┬────────┘
         │ REST API
         │
┌────────▼────────┐
│  App-Sink API   │
│   (FastAPI)     │
└────────┬────────┘
         │
┌────────▼────────┐
│   Kubernetes    │
│     (K3s)       │
└─────────────────┘
```

## 🤝 Contributing

This MCP server is part of the App-Sink project. See the main [README](../README.md) for contribution guidelines.

## 📝 License

MIT - See [LICENSE](../LICENSE) for details

## 🔗 Links

- [App-Sink Repository](../)
- [Model Context Protocol Spec](https://modelcontextprotocol.io/)
- [Claude Code](https://claude.ai/)

---

**Built with ❤️ for the AI-powered DevOps future**
