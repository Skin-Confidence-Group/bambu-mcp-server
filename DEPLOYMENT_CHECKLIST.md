# Deployment Checklist

Use this checklist to deploy your Bambu MCP Server step-by-step.

## Pre-Deployment

### Local Testing
- [ ] `.env` file created from `.env.example`
- [ ] Credentials added to `.env`
- [ ] Local server starts without errors: `./start.sh`
- [ ] Health check works: `curl http://localhost:8000/health`
- [ ] At least one tool tested successfully

### GitHub Repository
- [ ] Git initialized: `git init`
- [ ] `.gitignore` includes `.env`
- [ ] All files committed
- [ ] GitHub repo created
- [ ] Code pushed to `main` branch

## Railway Setup

### Account & Project
- [ ] Railway account created (free or paid)
- [ ] GitHub connected to Railway
- [ ] New project created from GitHub repo
- [ ] Dockerfile detected automatically

### Environment Variables
Required variables set:
- [ ] `BAMBU_EMAIL` = your Bambu account email
- [ ] `BAMBU_PASSWORD` = your Bambu password
- [ ] `BAMBU_DEVICE_ID` = 0948BB5B1200532 (your printer serial)

Optional variables:
- [ ] `SETUP_KEY` = random hex key (for 2FA security)
- [ ] `BAMBU_TOKEN` = (will be added after 2FA setup)

### Initial Deployment
- [ ] Build completes successfully (~2 min)
- [ ] Health check passes
- [ ] Railway assigns public URL
- [ ] URL copied for next steps

## 2FA Authentication (If Required)

Skip this section if your Bambu account doesn't have 2FA enabled.

### Generate Setup Key (Optional)
```bash
openssl rand -hex 32
```
- [ ] Setup key generated
- [ ] Added to Railway as `SETUP_KEY`
- [ ] Setup key saved securely (for later cleanup)

### Login Flow
- [ ] Railway URL confirmed: `https://your-app.railway.app`
- [ ] Login endpoint called (see [SETUP_2FA.md](SETUP_2FA.md))
- [ ] 2FA email received from Bambu Lab
- [ ] Verification code copied

### Token Retrieval
- [ ] Verify endpoint called with code
- [ ] Token received in response
- [ ] Token copied to clipboard

### Token Configuration
- [ ] `BAMBU_TOKEN` added to Railway variables
- [ ] Deployment restarted (automatic)
- [ ] Health check passes after restart
- [ ] Setup status confirmed: `curl https://your-app.railway.app/setup/status`

### Security Cleanup (Optional)
- [ ] `BAMBU_PASSWORD` removed from Railway (if desired)
- [ ] `SETUP_KEY` removed from Railway (if desired)
- [ ] Final redeploy successful

## Claude Desktop Configuration

### Config File Location
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

- [ ] Config file location confirmed
- [ ] Config file exists (create if not)

### MCP Configuration
Add this block to the config:
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

- [ ] Railway URL replaced in config
- [ ] URL ends with `/sse`
- [ ] JSON syntax is valid
- [ ] Config file saved

### Claude Desktop Restart
- [ ] Claude Desktop completely quit (not just minimized)
- [ ] Claude Desktop relaunched
- [ ] MCP connection established (check logs if needed)

## Testing

### Basic Connectivity
- [ ] Health endpoint: `curl https://your-app.railway.app/health`
- [ ] Root endpoint: `curl https://your-app.railway.app/`
- [ ] Setup status: `curl https://your-app.railway.app/setup/status`

### Tool Testing in Claude
Try these commands in Claude Desktop:

- [ ] "What's my 3D printer's status?"
  - Expected: Status, temps, progress returned

- [ ] "List my cloud files"
  - Expected: List of 3MF files (or empty list)

- [ ] "What filaments are in my AMS?"
  - Expected: Slot info with colors/materials

- [ ] "What's the current print progress?"
  - Expected: Percentage and time remaining

### Error Handling
Test error cases:

- [ ] Command when printer is offline
  - Expected: Graceful error message

- [ ] Invalid file ID for print
  - Expected: Error with explanation

## Monitoring Setup

### Railway Dashboard
- [ ] Metrics tab reviewed
- [ ] Logs tab checked for errors
- [ ] Deployment history visible

### External Monitoring (Optional)
- [ ] Uptime monitor configured (e.g., UptimeRobot)
- [ ] Health check URL: `https://your-app.railway.app/health`
- [ ] Alert notifications configured

### Claude Desktop Logs
- [ ] Log file location confirmed
- [ ] Initial connection logged successfully
- [ ] No error messages in logs

## Documentation

### Local Documentation
- [ ] README.md reviewed
- [ ] QUICK_START.md reviewed
- [ ] DEPLOYMENT.md reviewed
- [ ] SETUP_2FA.md reviewed (if 2FA used)
- [ ] PROJECT_OVERVIEW.md reviewed

### Custom Notes
- [ ] Railway URL documented
- [ ] Device ID documented
- [ ] Any customizations noted
- [ ] Setup date recorded

## Post-Deployment

### Security Review
- [ ] No credentials in git history
- [ ] `.env` not committed
- [ ] Railway variables encrypted
- [ ] Setup endpoints secured (or disabled)
- [ ] 2FA enabled on Bambu account
- [ ] 2FA enabled on Railway account

### Backup & Recovery
- [ ] Railway URL saved
- [ ] `BAMBU_TOKEN` saved securely (in password manager)
- [ ] Device ID documented
- [ ] Rollback plan understood

### Usage Documentation
Create a quick reference for yourself:

**Railway URL**: `https://your-app.railway.app`
**MCP Endpoint**: `https://your-app.railway.app/sse`
**Setup Date**: `____________________`
**Device ID**: `0948BB5B1200532`
**Token Expiry**: `Check every 90 days`

## Maintenance Tasks

### Weekly
- [ ] Check Railway metrics for unusual activity
- [ ] Review logs for errors

### Monthly
- [ ] Verify token is still valid
- [ ] Check Railway billing/usage
- [ ] Test all tools still work

### Quarterly (Every 90 Days)
- [ ] Rotate `BAMBU_TOKEN` if desired
- [ ] Review security settings
- [ ] Update dependencies (if available)

### As Needed
- [ ] Update when new tools added
- [ ] Redeploy when bugs fixed
- [ ] Check for library updates

## Troubleshooting Reference

### If Deployment Fails
1. Check Railway logs: `railway logs`
2. Verify Dockerfile syntax
3. Check dependencies in requirements.txt
4. Review build output for errors

### If Authentication Fails
1. Verify email/password in Railway variables
2. Check if token expired
3. Re-run 2FA setup flow
4. Test credentials in Bambu Handy app

### If Health Check Fails
1. Verify `PORT` variable (auto-set by Railway)
2. Check FastAPI is starting (logs)
3. Test locally first
4. Review Railway startup command

### If MCP Connection Fails
1. Verify URL in Claude config
2. Ensure URL ends with `/sse`
3. Restart Claude Desktop
4. Check Claude logs for details
5. Test health endpoint separately

### If Tools Don't Work
1. Check printer is online (Bambu Handy app)
2. Verify `BAMBU_DEVICE_ID` is correct
3. Review Railway logs for API errors
4. Test with simpler tools first (get_status)
5. Check token hasn't expired

## Success Criteria

You're done when:
- [ ] Health check returns healthy status
- [ ] Claude Desktop connects without errors
- [ ] At least 3 tools tested successfully
- [ ] No errors in Railway logs
- [ ] Printer responds to commands
- [ ] Documentation reviewed and understood

## Getting Help

If stuck:
1. Review logs (Railway + Claude Desktop)
2. Check documentation files in this repo
3. Verify environment variables
4. Test with curl commands
5. Review Railway dashboard metrics

## Notes Section

Use this space for your own notes:

```
Deployment Date: _______________
Railway URL: _______________
Any issues encountered: _______________
Custom configurations: _______________
```

---

**Checklist complete? Congratulations!** 🎉

Your Bambu printer is now Claude-enabled. Try asking Claude:
- "What's my printer doing?"
- "Start printing benchy.3mf"
- "How much filament is left?"
