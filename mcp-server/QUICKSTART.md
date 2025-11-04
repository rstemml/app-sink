# Quick Start Guide - App-Sink MCP Server

Get up and running in 5 minutes!

## Prerequisites

- ✅ App-Sink API running on `http://localhost:8000`
- ✅ Node.js 18+ installed
- ✅ Claude Code (or compatible AI tool)

## Step 1: Get an API Key

### Via Webapp (Easiest)
```bash
# Start webapp if not running
cd ../webapp
npm run dev
```

1. Open http://localhost:5173
2. Login with `admin` / `admin`
3. Click "API Keys" in sidebar
4. Click "New Key"
5. Name it "MCP Server"
6. **Copy the key immediately** (starts with `ask_`)

### Via CLI
```bash
cd ../cli
python -m app_sink_cli.cli config init
# Follow prompts to create API key
```

## Step 2: Build the MCP Server

```bash
cd mcp-server

# Install dependencies
npm install

# Build TypeScript
npm run build
```

## Step 3: Configure Claude Code

### Find your config file:
- **macOS/Linux**: `~/.config/claude/mcp.json`
- **Windows**: `%APPDATA%\claude\mcp.json`

### Add this configuration:

```json
{
  "mcpServers": {
    "app-sink": {
      "command": "node",
      "args": [
        "/FULL/PATH/TO/app-sink/mcp-server/dist/index.js"
      ],
      "env": {
        "APP_SINK_API_KEY": "ask_YOUR_KEY_HERE",
        "APP_SINK_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

**Important**: Replace `/FULL/PATH/TO/` with your actual path!

To get your full path:
```bash
cd /path/to/app-sink/mcp-server
pwd
# Use this output in the config
```

## Step 4: Restart Claude Code

Completely restart Claude Code to load the MCP server.

## Step 5: Test It! 🚀

In Claude Code, try these:

### Example 1: List Deployments
```
User: "Show me all my Kubernetes deployments"

Claude: [Uses app_sink_list tool]
```

### Example 2: Deploy an App
```
User: "Deploy nginx:latest as 'web-server' with 2 replicas"

Claude: [Uses app_sink_deploy tool]
        ✅ Deployment created!
```

### Example 3: Check Logs
```
User: "Show me the logs from web-server"

Claude: [Uses app_sink_logs tool]
        [Displays logs]
```

### Example 4: Scale Up
```
User: "Scale web-server to 5 replicas"

Claude: [Uses app_sink_scale tool]
        ✅ Scaled to 5 replicas
```

## Troubleshooting

### "APP_SINK_API_KEY environment variable is required"
- Check your `mcp.json` config
- Make sure the API key is in the `env` section

### "ENOENT: no such file or directory"
- Use absolute path (starting with `/` on Linux/Mac)
- Run `pwd` in mcp-server directory to get the full path

### MCP Server not appearing in Claude Code
1. Check JSON syntax in `mcp.json` (use a JSON validator)
2. Restart Claude Code completely
3. Check Claude Code developer console for errors

### "Connection refused"
- Make sure App-Sink API is running:
  ```bash
  curl http://localhost:8000/api/v1/health
  ```

## What's Next?

Try these more advanced scenarios:

**Deploy from Git with AI Analysis:**
```
"Deploy my app from https://github.com/user/myapp and scale it to 3 replicas"
```

**Multi-step Workflows:**
```
"Deploy nginx as 'test-app', check if it's running, and show me the logs"
```

**Debugging:**
```
"My payment-service is down. Show me the status and recent logs"
```

**Resource Management:**
```
"What deployments am I running? Scale down anything using more than 2 replicas"
```

---

🎉 **You're all set!** Start deploying with natural language!

Need help? Check the full [README.md](README.md) for detailed documentation.
