# Quick Start Guide

Get your Bambu MCP server running in 10 minutes.

## Local Testing (No Deployment)

```bash
# Clone/navigate to project
cd bambu-printer

# Quick start script
./start.sh

# Or manually:
python -m venv venv
source venv/bin/activate
pip install -e .
cp .env.example .env
# Edit .env with your credentials
python -m bambu_mcp.server
```

Server runs on `http://localhost:8000`

Test it:
```bash
curl http://localhost:8000/health
```

## Railway Deployment (5 Minutes)

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
gh repo create bambu-mcp --public --source=. --push
```

### 2. Deploy on Railway
1. Go to [railway.app](https://railway.app)
2. New Project → Deploy from GitHub → Select your repo
3. Wait for build (~2 minutes)

### 3. Set Environment Variables
In Railway dashboard → Variables:
```
BAMBU_EMAIL=your@email.com
BAMBU_PASSWORD=yourpassword
BAMBU_DEVICE_ID=0948BB5B1200532
```

### 4. (If 2FA) Get Token
```bash
# Your Railway URL
RAILWAY_URL="https://your-app.railway.app"

# Trigger 2FA email
curl -X POST $RAILWAY_URL/setup/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpassword"}'

# Check email, then verify (replace 123456 with your code)
curl -X POST $RAILWAY_URL/setup/verify \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","code":"123456"}'

# Copy the token from response
# Add to Railway: BAMBU_TOKEN=<your-token>
```

Full 2FA guide: [SETUP_2FA.md](SETUP_2FA.md)

### 5. Get Your URL
Railway assigns a URL like:
```
https://bambu-mcp-production.up.railway.app
```

MCP endpoint:
```
https://bambu-mcp-production.up.railway.app/sse
```

## Claude Desktop Setup (2 Minutes)

### 1. Edit Config File

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

### 2. Add MCP Server

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

### 3. Restart Claude Desktop

Quit completely and relaunch.

### 4. Test It!

In Claude Desktop:
```
Hey Claude, what's my 3D printer's current status?
```

Claude should call `get_printer_status` and return real-time data!

## Available Tools

Once connected, Claude can use these tools:

### Status & Monitoring
- `get_printer_status` - Temps, progress, layer count, time remaining
- `get_ams_status` - Filament colors, materials, remaining %

### File Management
- `list_cloud_files` - View all files in Bambu Cloud
- `upload_file` - Upload 3MF files

### Print Control
- `start_print` - Begin printing from cloud file
- `pause_print` - Pause active print
- `resume_print` - Resume paused print
- `cancel_print` - Stop and cancel print

### Presets (if available)
- `list_presets` - Get Bambu Studio presets

## Example Commands

```
Claude, show me my printer status
Claude, list my cloud files
Claude, what filaments are loaded?
Claude, start printing the file called "benchy.3mf"
Claude, pause the current print
Claude, how much time is left on this print?
```

## Troubleshooting

### Can't connect to server
```bash
# Check if server is running
curl https://your-app.railway.app/health

# Should return:
# {"status":"healthy","server":"bambu-printer",...}
```

### Authentication fails
```bash
# Check setup status
curl https://your-app.railway.app/setup/status

# Should show: "setup_complete": true
```

### Tools don't work
1. Verify printer is online in Bambu Handy app
2. Check `BAMBU_DEVICE_ID` matches your printer serial
3. View Railway logs for errors:
   ```bash
   railway logs
   ```

### Claude doesn't see the tools
1. Verify `claude_desktop_config.json` has correct URL
2. Ensure URL ends with `/sse` (not just the domain)
3. Restart Claude Desktop completely
4. Check Claude logs:
   - macOS: `~/Library/Logs/Claude/mcp*.log`
   - Windows: `%APPDATA%\Claude\logs\mcp*.log`

## Next Steps

- Read the full [README.md](README.md) for detailed info
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for Railway tips
- See [SETUP_2FA.md](SETUP_2FA.md) for 2FA auth details
- Monitor your printer usage in Railway dashboard

## Project Structure

```
bambu-printer/
├── src/bambu_mcp/
│   ├── server.py         # Main MCP server + FastAPI
│   ├── bambu_tools.py    # Tool implementations
│   ├── auth.py           # Authentication manager
│   ├── setup.py          # 2FA setup endpoints
│   └── config.py         # Settings
├── Dockerfile            # Railway deployment
├── railway.json          # Railway config
├── requirements.txt      # Python dependencies
└── README.md            # Full documentation
```

## Support

- **Railway Issues**: Check logs with `railway logs`
- **MCP Issues**: Check Claude Desktop logs
- **API Issues**: Verify printer connection in Bambu Handy app

## Security Checklist

- [ ] Never commit `.env` file
- [ ] Use `SETUP_KEY` for production 2FA setup
- [ ] Delete `SETUP_KEY` after getting token
- [ ] (Optional) Delete `BAMBU_PASSWORD` after getting token
- [ ] Keep `BAMBU_TOKEN` secure in Railway environment
- [ ] Use strong Bambu account password with 2FA

---

**You're all set!** Your 3D printer is now Claude-enabled. 🎉
