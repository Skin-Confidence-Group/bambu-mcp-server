# Bambu Lab Cloud MCP Server

A Model Context Protocol (MCP) server for controlling Bambu Lab 3D printers via their Cloud API. Designed for deployment on Railway and remote access from Claude Desktop.

## Features

- **Remote MCP Server**: HTTP/SSE transport for cloud deployment
- **Printer Control**: Real-time status, print management (start/pause/resume/cancel)
- **File Management**: Upload 3MF files to cloud, list available files
- **AMS Support**: Monitor filament slots on AMS 2 Pro
- **Cloud Authentication**: Secure token-based auth with auto-refresh
- **Railway Ready**: Health checks, Docker support, zero-config deployment

## Printer Details

- **Model**: Bambu Lab H2D
- **Serial**: 0948BB5B1200532
- **AMS**: AMS 2 Pro (Serial: 19C06A5A3100241)
- **Firmware**: 01.02.02.00

## Architecture

```
┌─────────────────┐
│ Claude Desktop  │
│   (MCP Client)  │
└────────┬────────┘
         │ HTTP/SSE
         │
┌────────▼────────┐
│  Railway Host   │
│  ┌───────────┐  │
│  │ MCP Server│  │
│  │  FastAPI  │  │
│  └─────┬─────┘  │
└────────┼────────┘
         │ Cloud API
┌────────▼────────┐
│  Bambu Cloud    │
│   MQTT Broker   │
└────────┬────────┘
         │
    ┌────▼────┐
    │ H2D     │
    │ Printer │
    └─────────┘
```

## MCP Tools

### Printer Status
- `get_printer_status` - Get current state, temperatures, print progress, layer info

### File Management
- `list_cloud_files` - List all files in Bambu Cloud storage
- `upload_file` - Upload 3MF files to cloud

### Print Control
- `start_print` - Start a print job from cloud file
- `pause_print` - Pause current print
- `resume_print` - Resume paused print
- `cancel_print` - Cancel current print

### Filament & Presets
- `get_ams_status` - Get AMS filament slot status (colors, materials, remaining %)
- `list_presets` - List Bambu Studio presets (if available via API)

## Local Development

### Prerequisites
- Python 3.11+
- Bambu Lab account with cloud access
- Your printer connected to Bambu Cloud

### Setup

1. **Clone and install dependencies**:
```bash
git clone <your-repo>
cd bambu-printer
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your credentials:
# BAMBU_EMAIL=your-email@example.com
# BAMBU_PASSWORD=your-password
# BAMBU_DEVICE_ID=0948BB5B1200532
```

3. **Run locally**:
```bash
python -m bambu_mcp.server
# Server starts on http://localhost:8000
# Health check: http://localhost:8000/health
# MCP endpoint: http://localhost:8000/sse
```

### Testing Tools

Test individual tools:
```python
import asyncio
from bambu_mcp.config import get_settings
from bambu_mcp.auth import BambuAuthManager
from bambu_mcp.bambu_tools import BambuPrinterTools

async def test():
    settings = get_settings()
    auth = BambuAuthManager(settings)
    tools = BambuPrinterTools(settings, auth)

    # Get printer status
    status = await tools.get_printer_status()
    print(status)

    # List cloud files
    files = await tools.list_cloud_files()
    print(files)

asyncio.run(test())
```

## Railway Deployment

### Step 1: Prepare Repository
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo>
git push -u origin main
```

### Step 2: Deploy to Railway

1. Go to [Railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect the Dockerfile

### Step 3: Configure Environment Variables

In Railway dashboard, add these variables:
```
BAMBU_EMAIL=your-email@example.com
BAMBU_PASSWORD=your-password
BAMBU_DEVICE_ID=0948BB5B1200532
```

Optional (will be auto-generated):
```
BAMBU_TOKEN=<cached-token>
PORT=<auto-assigned-by-railway>
```

### Step 3.5: 2FA Setup (If Enabled)

**If your Bambu account has 2FA enabled**, you'll need to complete a one-time setup to get an access token. See [SETUP_2FA.md](SETUP_2FA.md) for the complete guide.

Quick version:
1. Deploy without `BAMBU_TOKEN` first
2. Call `POST /setup/login` to trigger 2FA email
3. Call `POST /setup/verify` with the code from your email
4. Copy the token and add it to Railway as `BAMBU_TOKEN`
5. Redeploy - done!

Detailed guide: [SETUP_2FA.md](SETUP_2FA.md)

### Step 4: Get Your MCP Server URL

After deployment, Railway provides a URL like:
```
https://bambu-printer-production.up.railway.app
```

Your MCP SSE endpoint will be:
```
https://bambu-printer-production.up.railway.app/sse
```

## Claude Desktop Configuration

Add to your Claude Desktop MCP settings file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "bambu-printer": {
      "transport": {
        "type": "sse",
        "url": "https://your-railway-app.up.railway.app/sse"
      }
    }
  }
}
```

Restart Claude Desktop. The printer tools will now be available!

## Usage Examples

### Check Printer Status
```
Hey Claude, can you check my 3D printer's status?
```

### Start a Print
```
Claude, list my cloud files and start printing the "benchy.3mf" file
```

### Monitor Print Progress
```
What's the current print progress and estimated time remaining?
```

### Check Filament
```
What filaments are loaded in my AMS?
```

## API Reference

### Authentication Flow

1. Server authenticates on startup using `BAMBU_EMAIL` and `BAMBU_PASSWORD`
2. Access token is cached in memory (and optionally in `BAMBU_TOKEN` env var)
3. Token is automatically refreshed when needed
4. All API calls use the cached token

### Cloud API vs LAN API

This server uses the **Cloud API** (not LAN mode) because:
- Works remotely from anywhere
- No need for local network access or access codes
- Better suited for Railway cloud deployment
- Supports all major features (status, file management, print control)

## Troubleshooting

### Authentication Fails
- Verify email/password in Railway environment variables
- Check if 2FA is enabled (may need to handle verification codes)
- Check logs: `railway logs`

### Health Check Fails
- Ensure `PORT` environment variable is set (Railway does this automatically)
- Check Dockerfile health check command
- Verify FastAPI is running: `curl https://your-app.railway.app/health`

### Tools Not Working
- Check printer is online and connected to Bambu Cloud
- Verify `BAMBU_DEVICE_ID` matches your printer serial
- Check Railway logs for API errors

### Connection Timeout
- Cloud API may have rate limits
- Check your Bambu Lab account status
- Verify printer firmware is up to date (01.02.02.00+)

## Development

### Project Structure
```
bambu-printer/
├── src/
│   └── bambu_mcp/
│       ├── __init__.py
│       ├── server.py          # MCP server + FastAPI app
│       ├── bambu_tools.py     # Tool implementations
│       ├── auth.py            # Authentication manager
│       └── config.py          # Settings management
├── Dockerfile                 # Railway deployment
├── railway.json               # Railway config
├── railway.toml               # Alternative Railway config
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Package metadata
└── README.md
```

### Adding New Tools

1. Add method to `BambuPrinterTools` class in [bambu_tools.py](src/bambu_mcp/bambu_tools.py)
2. Register tool schema in `list_tools()` in [server.py](src/bambu_mcp/server.py)
3. Add handler in `call_tool()` in [server.py](src/bambu_mcp/server.py)

Example:
```python
# In bambu_tools.py
async def my_new_tool(self, param: str) -> dict[str, Any]:
    client = await self._get_client()
    result = await client.some_api_call(param)
    return {"result": result}

# In server.py - list_tools()
Tool(
    name="my_new_tool",
    description="Does something cool",
    inputSchema={
        "type": "object",
        "properties": {
            "param": {"type": "string", "description": "A parameter"}
        },
        "required": ["param"]
    }
)

# In server.py - call_tool()
elif name == "my_new_tool":
    result = await bambu_tools.my_new_tool(arguments["param"])
```

## Dependencies

- [`mcp`](https://pypi.org/project/mcp/) - Model Context Protocol SDK
- [`bambu-lab-cloud-api`](https://github.com/coelacant1/Bambu-Lab-Cloud-API) - Bambu Cloud API client
- [`fastapi`](https://fastapi.tiangolo.com/) - Web framework for health checks
- [`uvicorn`](https://www.uvicorn.org/) - ASGI server
- [`pydantic`](https://docs.pydantic.dev/) - Settings management

## Security Notes

- Store credentials in Railway environment variables (encrypted at rest)
- Never commit `.env` file to git
- Tokens are cached in memory only (not persisted to disk)
- Consider implementing token refresh logic for long-running deployments
- HTTPS is enforced by Railway for all external connections

## License

MIT

## Contributing

Issues and PRs welcome! This is a custom MCP server for personal use but feel free to fork and adapt.

## References

- [Bambu Lab Cloud API Docs](https://github.com/coelacant1/Bambu-Lab-Cloud-API)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Railway Deployment Docs](https://docs.railway.app/)
- [Claude Desktop MCP Setup](https://docs.anthropic.com/claude/docs/mcp)
