# Bambu MCP Server - Project Overview

## What This Is

A **Model Context Protocol (MCP) server** that allows Claude Desktop to control your Bambu Lab H2D 3D printer via the Bambu Cloud API. Deployed on Railway for remote access from anywhere.

## Architecture

```
┌──────────────────┐
│ Claude Desktop   │  (Your computer, anywhere)
│   (MCP Client)   │
└────────┬─────────┘
         │ HTTPS/SSE
         │
┌────────▼─────────┐
│  Railway Cloud   │  (Hosting platform)
│ ┌──────────────┐ │
│ │ FastAPI App  │ │  - Health checks
│ │ MCP Server   │ │  - SSE transport
│ │ Auth Manager │ │  - Tool handlers
│ └──────┬───────┘ │
└────────┼─────────┘
         │ Cloud API (HTTPS + MQTT)
         │
┌────────▼─────────┐
│  Bambu Cloud     │  (Bambu Lab servers)
│  - Auth Service  │
│  - MQTT Broker   │
│  - File Storage  │
└────────┬─────────┘
         │ Internet
         │
    ┌────▼─────┐
    │ H2D      │  (Your printer, at home)
    │ Printer  │
    │ + AMS    │
    └──────────┘
```

## File Structure

```
bambu-printer/
├── Documentation
│   ├── README.md              # Main documentation
│   ├── QUICK_START.md         # 10-minute setup guide
│   ├── DEPLOYMENT.md          # Railway deployment guide
│   ├── SETUP_2FA.md           # 2FA authentication flow
│   └── PROJECT_OVERVIEW.md    # This file
│
├── Python Package
│   └── src/bambu_mcp/
│       ├── __init__.py        # Package exports
│       ├── server.py          # FastAPI + MCP server (main entry)
│       ├── bambu_tools.py     # Tool implementations (9 tools)
│       ├── auth.py            # Authentication & token caching
│       ├── setup.py           # 2FA setup endpoints
│       └── config.py          # Settings management (Pydantic)
│
├── Configuration
│   ├── pyproject.toml         # Package metadata
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example           # Environment template
│   ├── .gitignore             # Git exclusions
│   └── .dockerignore          # Docker exclusions
│
├── Deployment
│   ├── Dockerfile             # Railway container
│   ├── railway.json           # Railway config (JSON)
│   ├── railway.toml           # Railway config (TOML)
│   └── start.sh               # Local dev script
│
└── IDE Config
    └── .claude/settings.local.json
```

## Core Components

### 1. MCP Server ([server.py](src/bambu_mcp/server.py))
- **Framework**: FastAPI for HTTP/SSE
- **Transport**: SSE (Server-Sent Events) for MCP protocol
- **Endpoints**:
  - `GET /` - Server info
  - `GET /health` - Railway health check
  - `GET /sse` - MCP connection endpoint
  - `POST /setup/login` - 2FA initiation
  - `POST /setup/verify` - 2FA verification
  - `GET /setup/status` - Setup status

### 2. Tool Handler ([bambu_tools.py](src/bambu_mcp/bambu_tools.py))
Implements 9 MCP tools:

**Status & Monitoring**
- `get_printer_status()` - Real-time printer state
- `get_ams_status()` - Filament slot info

**File Management**
- `list_cloud_files()` - Cloud storage listing
- `upload_file()` - 3MF upload

**Print Control**
- `start_print()` - Begin print job
- `pause_print()` - Pause active print
- `resume_print()` - Resume print
- `cancel_print()` - Stop print

**Configuration**
- `list_presets()` - Bambu Studio presets (if available)

### 3. Authentication ([auth.py](src/bambu_mcp/auth.py))
- **Token Caching**: Stores access token in memory
- **Auto-Refresh**: Renews token when expired
- **2FA Support**: Handles verification codes

### 4. Setup Flow ([setup.py](src/bambu_mcp/setup.py))
- **One-Time Setup**: Get token via web endpoints
- **Security**: Optional `SETUP_KEY` protection
- **Flow**:
  1. POST `/setup/login` → Sends 2FA email
  2. Check email for code
  3. POST `/setup/verify` → Returns token
  4. Add token to Railway env vars

### 5. Configuration ([config.py](src/bambu_mcp/config.py))
- **Pydantic Settings**: Type-safe environment variables
- **Auto-Loading**: Reads from `.env` or Railway
- **Validation**: Ensures required vars are set

## Dependencies

### Core Libraries
```
mcp>=1.1.0                    # MCP protocol SDK
bambu-lab-cloud-api>=0.1.0    # Bambu API client
fastapi>=0.115.0              # Web framework
uvicorn[standard]>=0.32.0     # ASGI server
pydantic>=2.0.0               # Settings validation
pydantic-settings>=2.0.0      # Environment loader
python-dotenv>=1.0.0          # .env file support
```

### Bambu API Features Used
- **Authentication**: Token-based with email/password
- **Device Control**: Cloud API (not LAN)
- **Real-Time Data**: MQTT for live status
- **File Storage**: Cloud upload/download

## Environment Variables

### Required
```bash
BAMBU_EMAIL=your-email@example.com          # Bambu account
BAMBU_PASSWORD=your-password                # Bambu password
BAMBU_DEVICE_ID=0948BB5B1200532            # Printer serial
```

### Optional
```bash
BAMBU_TOKEN=eyJhbG...                       # Cached token (auto-generated)
PORT=8000                                    # Server port (Railway sets this)
SETUP_KEY=a7f9e2c3...                       # 2FA endpoint protection
MCP_SERVER_NAME=bambu-printer               # MCP server name
MCP_SERVER_VERSION=0.1.0                    # Server version
RAILWAY_ENVIRONMENT=production              # Railway flag
```

## Data Flow

### 1. Claude Desktop → MCP Server
```
User: "What's my printer status?"
  ↓
Claude Desktop calls tool: get_printer_status
  ↓
HTTP POST to /sse (MCP protocol)
  ↓
MCP Server receives request
```

### 2. MCP Server → Bambu Cloud
```
MCP Server calls bambu_tools.get_printer_status()
  ↓
BambuClient makes API request with token
  ↓
Bambu Cloud API returns printer data
  ↓
MQTT client subscribes for real-time updates
```

### 3. Response Back to Claude
```
Bambu Cloud → MCP Server: JSON data
  ↓
MCP Server formats as TextContent
  ↓
SSE sends response to Claude Desktop
  ↓
Claude processes and shows user-friendly response
```

## Security Model

### Authentication Layers
1. **Bambu Cloud**: Email/password + optional 2FA
2. **Token Storage**: Encrypted in Railway env vars
3. **Setup Endpoints**: Optional `SETUP_KEY` protection
4. **Transport**: HTTPS enforced by Railway

### Best Practices
- ✅ Credentials in environment variables (not code)
- ✅ `.env` excluded from git
- ✅ Token caching (no repeated auth)
- ✅ HTTPS only (Railway enforces)
- ✅ Optional password removal after getting token
- ✅ Setup key for one-time 2FA flow

## Deployment Flow

### Local Development
```bash
./start.sh                    # Quick start
# or
python -m bambu_mcp.server    # Manual start
```

### Railway Deployment
```
1. Push to GitHub
   ↓
2. Railway detects Dockerfile
   ↓
3. Builds Docker image (Python 3.11 + deps)
   ↓
4. Sets PORT env var
   ↓
5. Runs health checks (/health)
   ↓
6. Assigns public URL
   ↓
7. Ready! (SSE endpoint available)
```

## Testing

### Health Check
```bash
curl https://your-app.railway.app/health
# Expected: {"status":"healthy",...}
```

### Setup Status
```bash
curl https://your-app.railway.app/setup/status
# Expected: {"setup_complete":true,...}
```

### MCP Connection
Configure in Claude Desktop:
```json
{
  "mcpServers": {
    "bambu-printer": {
      "transport": {
        "type": "sse",
        "url": "https://your-app.railway.app/sse"
      }
    }
  }
}
```

Then test in Claude:
```
What's my printer status?
```

## Monitoring

### Railway Dashboard
- **Logs**: Real-time application logs
- **Metrics**: CPU, memory, network usage
- **Deployments**: Build history & rollbacks
- **Variables**: Environment configuration

### Health Monitoring
Set up external monitoring (e.g., UptimeRobot):
- Endpoint: `https://your-app.railway.app/health`
- Interval: Every 5 minutes
- Alert on: Non-200 response

### Claude Desktop Logs
Check MCP connection logs:
- macOS: `~/Library/Logs/Claude/mcp*.log`
- Windows: `%APPDATA%\Claude\logs\mcp*.log`
- Linux: `~/.config/Claude/logs/mcp*.log`

## Development Workflow

### Adding New Tools

1. **Add tool method** to [bambu_tools.py](src/bambu_mcp/bambu_tools.py):
```python
async def my_new_tool(self, param: str) -> dict[str, Any]:
    client = await self._get_client()
    result = await client.some_api_method(param)
    return {"result": result}
```

2. **Register tool** in [server.py](src/bambu_mcp/server.py) `list_tools()`:
```python
Tool(
    name="my_new_tool",
    description="Does something useful",
    inputSchema={
        "type": "object",
        "properties": {
            "param": {"type": "string", "description": "Parameter desc"}
        },
        "required": ["param"]
    }
)
```

3. **Add handler** in [server.py](src/bambu_mcp/server.py) `call_tool()`:
```python
elif name == "my_new_tool":
    result = await bambu_tools.my_new_tool(arguments["param"])
```

4. **Test locally**, then push to Railway:
```bash
git add .
git commit -m "Add my_new_tool"
git push
```

Railway auto-deploys in ~2 minutes.

## Troubleshooting Guide

| Issue | Check | Fix |
|-------|-------|-----|
| Build fails | Railway logs | Fix syntax errors, check dependencies |
| Auth fails | Email/password correct? | Verify credentials, check 2FA |
| Health check fails | `/health` returns 200? | Check PORT var, verify FastAPI starts |
| MCP connection fails | Claude config correct? | Verify URL ends with `/sse` |
| Tools don't work | Printer online? | Check Bambu Handy app, verify device ID |
| Token expired | Auto-refresh enabled? | Re-run 2FA setup to get new token |

## Performance

### Latency
- Claude → Railway: ~100-300ms (depends on region)
- Railway → Bambu Cloud: ~200-500ms (API call)
- **Total**: ~300-800ms per tool call

### Optimization
- Token caching (no re-auth on every call)
- MQTT for real-time updates (faster than polling)
- Railway edge network (low latency)

### Scaling
- Free tier: ~500 hours/month
- Hobby tier ($5/mo): Always-on
- Pro tier: Auto-scaling available

## Cost Estimate

### Railway
- **Free tier**: $5 credit/month (plenty for personal use)
- **Hobby tier**: $5/month (always-on, recommended)
- **Usage**: Minimal (mostly idle, spikes on tool calls)

### Bambu Cloud
- **API**: Free (included with printer)
- **Storage**: Free (reasonable limits)

**Total**: $0-5/month depending on tier

## Limitations

### API Constraints
- **Cloud API only**: No LAN mode support in this version
- **Rate limits**: Bambu Cloud may throttle excessive requests
- **Preset access**: May not be available via cloud API

### MCP Limitations
- **Read-only logs**: Can't download print logs (yet)
- **No video**: Can't stream camera feed
- **No manual control**: Can't jog axes or manual commands

### Railway Limitations
- **Cold starts**: Free tier may sleep after inactivity
- **Region**: Deployed to single region (US-based usually)

## Future Enhancements

Potential features to add:

1. **Webhooks**: Real-time printer status push notifications
2. **Timelapse**: Download timelapse videos
3. **Multi-Printer**: Support multiple printers in one server
4. **Print Queue**: Queue multiple print jobs
5. **Metrics**: Prometheus endpoint for monitoring
6. **Web Dashboard**: Simple UI for status overview
7. **LAN Mode**: Add support for local network control
8. **Notifications**: Discord/Slack/email alerts

## Resources

- **MCP Docs**: https://modelcontextprotocol.io
- **Bambu API**: https://github.com/coelacant1/Bambu-Lab-Cloud-API
- **Railway Docs**: https://docs.railway.app
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Claude Desktop MCP**: https://docs.anthropic.com/claude/docs/mcp

## Support & Contributions

This is a personal project, but feel free to:
- Fork and customize for your setup
- Report issues on GitHub
- Submit PRs for improvements
- Share your enhancements

## License

MIT - Use freely, no warranty provided.

---

Built with Claude Code 🤖
