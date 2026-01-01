# Railway Deployment Guide

Step-by-step guide to deploy your Bambu MCP Server to Railway.

## Prerequisites

- GitHub account
- Railway account (free tier works)
- Bambu Lab account with cloud-connected printer
- Git installed locally

## Step 1: Prepare Repository

Initialize git and push to GitHub:

```bash
cd bambu-printer

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Bambu MCP Server"

# Create GitHub repo (via GitHub CLI or web interface)
gh repo create bambu-mcp-server --public --source=. --remote=origin

# Or manually add remote:
# git remote add origin https://github.com/YOUR_USERNAME/bambu-mcp-server.git

# Push to GitHub
git push -u origin main
```

## Step 2: Create Railway Project

1. Go to [railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub account
5. Select your `bambu-mcp-server` repository
6. Railway will automatically detect the Dockerfile and start building

## Step 3: Configure Environment Variables

In the Railway dashboard:

1. Click on your project
2. Click **"Variables"** tab
3. Add these environment variables:

```
BAMBU_EMAIL=your-email@example.com
BAMBU_PASSWORD=your-secure-password
BAMBU_DEVICE_ID=0948BB5B1200532
```

**Note**: Railway automatically sets the `PORT` variable.

## Step 4: Wait for Deployment

Railway will:
1. Build your Docker image (1-2 minutes)
2. Deploy the container
3. Run health checks
4. Assign a public URL

Watch the deployment logs in real-time.

## Step 5: Verify Deployment

Once deployed, Railway provides a URL like:
```
https://bambu-mcp-server-production.up.railway.app
```

Test the endpoints:

### Health Check
```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "server": "bambu-printer",
  "version": "0.1.0",
  "device_id": "0948BB5B1200532"
}
```

### Server Info
```bash
curl https://your-app.railway.app/
```

### MCP Endpoint
The MCP SSE endpoint will be:
```
https://your-app.railway.app/sse
```

## Step 6: Configure Claude Desktop

Get your Railway app URL from the dashboard, then:

### macOS
Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

### Windows
Edit: `%APPDATA%\Claude\claude_desktop_config.json`

### Linux
Edit: `~/.config/Claude/claude_desktop_config.json`

Add this configuration:

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

**Important**: Replace `your-app.railway.app` with your actual Railway domain!

## Step 7: Restart Claude Desktop

1. Quit Claude Desktop completely
2. Relaunch it
3. The MCP server should connect automatically

Check the Claude Desktop logs to verify connection:
- macOS: `~/Library/Logs/Claude/mcp*.log`
- Windows: `%APPDATA%\Claude\logs\mcp*.log`

## Step 8: Test the Connection

In Claude Desktop, try:

```
Hey Claude, can you check my 3D printer's status?
```

Claude should be able to call the `get_printer_status` tool and return real-time information!

## Troubleshooting

### Build Fails

Check Railway logs:
```bash
railway logs
```

Common issues:
- Missing dependencies in `requirements.txt`
- Python version mismatch (needs 3.11+)
- Syntax errors in Python files

### Authentication Fails

Symptoms:
- Health check passes but tools fail
- Logs show "Authentication failed"

Solutions:
1. Verify `BAMBU_EMAIL` and `BAMBU_PASSWORD` in Railway variables
2. Check if your Bambu account has 2FA enabled
3. Try logging into Bambu Cloud web interface to verify credentials
4. Check Railway logs: `railway logs`

### Health Check Fails

Symptoms:
- Deployment keeps restarting
- Railway shows "Unhealthy"

Solutions:
1. Check `PORT` variable is set (Railway does this automatically)
2. Verify Dockerfile `HEALTHCHECK` command
3. Check if FastAPI is starting: look for "Uvicorn running" in logs
4. Test manually: `curl https://your-app.railway.app/health`

### MCP Connection Fails

Symptoms:
- Claude Desktop doesn't see the tools
- Connection timeout errors

Solutions:
1. Verify Railway URL in `claude_desktop_config.json`
2. Ensure URL uses `https://` (not `http://`)
3. Test SSE endpoint: `curl https://your-app.railway.app/sse`
4. Check Claude Desktop logs for connection errors
5. Restart Claude Desktop after config changes

### Printer Not Found

Symptoms:
- Tools fail with "Device not found"
- Connection timeout to printer

Solutions:
1. Verify `BAMBU_DEVICE_ID` matches your printer serial exactly
2. Ensure printer is online and connected to Bambu Cloud
3. Check printer is not in LAN-only mode (needs cloud connection)
4. Test with Bambu Handy app to verify cloud connectivity

## Monitoring

### View Logs
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# View logs
railway logs
```

### Check Metrics

In Railway dashboard:
- **Deployments**: View build and deployment history
- **Metrics**: CPU, memory, network usage
- **Logs**: Real-time application logs
- **Settings**: Environment variables, domains

### Health Monitoring

Set up a cron job or uptime monitor (like UptimeRobot) to ping:
```
https://your-app.railway.app/health
```

This ensures your server stays alive (Railway may sleep inactive services on free tier).

## Updating the Server

### Push Updates

```bash
# Make changes to code
git add .
git commit -m "Update: your changes"
git push origin main
```

Railway automatically:
1. Detects the push
2. Rebuilds the Docker image
3. Deploys the new version
4. Runs health checks
5. Switches traffic to new deployment (zero downtime)

### Rollback

If something breaks:

1. Go to Railway dashboard
2. Click **"Deployments"**
3. Find the last working deployment
4. Click **"Redeploy"**

## Cost Management

### Free Tier Limits (as of 2024)
- $5 free credit per month
- ~500 hours of runtime
- Sleeps after 30 minutes of inactivity

### Optimization Tips

1. **Use Hobby Plan** ($5/month) for always-on service
2. **Minimize API calls** - cache status when possible
3. **Use webhooks** - instead of polling (if Bambu API supports)
4. **Monitor usage** - check Railway dashboard regularly

## Security Best Practices

1. **Never commit `.env`** - already in `.gitignore`
2. **Use strong passwords** - for Bambu account
3. **Rotate tokens** - periodically update `BAMBU_TOKEN`
4. **Monitor logs** - watch for suspicious activity
5. **Enable 2FA** - on both Railway and Bambu accounts
6. **Limit API access** - use Railway's built-in IP restrictions if needed

## Custom Domain (Optional)

Railway supports custom domains:

1. Go to **Settings** > **Domains**
2. Click **"Add Domain"**
3. Enter your domain (e.g., `bambu.yourdomain.com`)
4. Add the provided DNS records to your domain registrar
5. Wait for DNS propagation (5-60 minutes)

Update Claude config with new domain:
```json
{
  "mcpServers": {
    "bambu-printer": {
      "transport": {
        "type": "sse",
        "url": "https://bambu.yourdomain.com/sse"
      }
    }
  }
}
```

## Advanced: Environment-Specific Configs

For multiple printers or staging/production:

### Create Multiple Projects

1. Deploy same code to different Railway projects
2. Configure different `BAMBU_DEVICE_ID` for each
3. Use different names in Claude config:

```json
{
  "mcpServers": {
    "bambu-printer-h2d": {
      "transport": {
        "type": "sse",
        "url": "https://bambu-h2d.railway.app/sse"
      }
    },
    "bambu-printer-p1s": {
      "transport": {
        "type": "sse",
        "url": "https://bambu-p1s.railway.app/sse"
      }
    }
  }
}
```

Now Claude can control multiple printers!

## Support

- **Railway Docs**: https://docs.railway.app
- **MCP Specification**: https://modelcontextprotocol.io
- **Bambu API**: https://github.com/coelacant1/Bambu-Lab-Cloud-API
- **Claude Desktop MCP**: https://docs.anthropic.com/claude/docs/mcp

## Next Steps

- Add webhooks for real-time printer status updates
- Implement print job queueing
- Add timelapse download support
- Create a simple web dashboard
- Add Prometheus metrics for monitoring
