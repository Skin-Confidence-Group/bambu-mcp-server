# 🚀 Deploy to Railway NOW

Your code is ready and pushed to GitHub! Follow these steps to deploy.

## ✅ GitHub Repository

**Repository URL**: https://github.com/Skin-Confidence-Group/bambu-mcp-server
**Organization**: Skin-Confidence-Group

All code is pushed and ready for Railway to pull.

## Step 1: Go to Railway

Open in your browser: **https://railway.app**

## Step 2: Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. If prompted, authorize Railway to access your GitHub account
4. Search for: **`bambu-mcp-server`** or **`Skin-Confidence-Group`**
5. Select the repository: **`Skin-Confidence-Group/bambu-mcp-server`**
6. Click **"Deploy Now"**

Railway will automatically:
- Detect the Dockerfile
- Start building the container
- This takes ~2-3 minutes

## Step 3: Configure Environment Variables

While it's building, set up your environment variables:

1. Click on your project (if not already open)
2. Go to the **"Variables"** tab
3. Click **"New Variable"**
4. Add these **THREE REQUIRED** variables:

```
BAMBU_EMAIL = your-bambu-email@example.com
BAMBU_PASSWORD = your-bambu-password
BAMBU_DEVICE_ID = 0948BB5B1200532
```

**Important**:
- Use your actual Bambu Lab account credentials
- The device ID is your printer serial (already correct for your H2D)
- Railway automatically sets `PORT`, you don't need to add it

## Step 4: Wait for Deployment

After adding variables, Railway will redeploy automatically (another ~2 minutes).

Watch for:
- ✅ Build succeeds
- ✅ Health check passes
- ✅ Status shows "Active"

## Step 5: Get Your URL

Once deployed:

1. Go to the **"Settings"** tab
2. Find the **"Public Networking"** section
3. Click **"Generate Domain"**
4. Copy the URL (looks like: `https://bambu-mcp-server-production-xxxx.up.railway.app`)

**Your MCP endpoint will be**: `https://your-url.railway.app/sse`

## Step 6: Test Deployment

Test the health endpoint:

```bash
curl https://your-url.railway.app/health
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

## Step 7: Setup 2FA (If Your Account Has It)

**If your Bambu account has 2FA enabled**, you need to get a token:

### Check if you need 2FA:
```bash
curl https://your-url.railway.app/setup/status
```

If it says `"setup_complete": false`, run the 2FA flow:

### Option A: Quick Script

```bash
#!/bin/bash
RAILWAY_URL="https://your-url.railway.app"
EMAIL="your-email@example.com"
PASSWORD="your-password"

# Step 1: Login (triggers 2FA email)
curl -X POST "$RAILWAY_URL/setup/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}"

# Check your email for the code, then:
read -p "Enter 2FA code: " CODE

# Step 2: Verify
curl -X POST "$RAILWAY_URL/setup/verify" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"code\":\"$CODE\"}"
```

### Option B: Manual cURL

**Trigger 2FA email:**
```bash
curl -X POST https://your-url.railway.app/setup/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpass"}'
```

**Check your email**, then verify with code:
```bash
curl -X POST https://your-url.railway.app/setup/verify \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","code":"123456"}'
```

**Copy the token** from the response, then:

1. Go to Railway → Variables
2. Add: `BAMBU_TOKEN = <the-token-you-got>`
3. Railway will redeploy automatically

Full guide: [SETUP_2FA.md](SETUP_2FA.md)

## Step 8: Configure Claude Desktop

Edit your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add this (replace with your actual Railway URL):

```json
{
  "mcpServers": {
    "bambu-printer": {
      "transport": {
        "type": "sse",
        "url": "https://your-url.railway.app/sse"
      }
    }
  }
}
```

**Important**:
- Replace `your-url.railway.app` with your actual Railway domain
- URL must end with `/sse`

## Step 9: Restart Claude Desktop

1. **Completely quit** Claude Desktop (don't just minimize)
2. **Relaunch** it
3. Wait 5-10 seconds for MCP connection

## Step 10: Test It! 🎉

In Claude Desktop, try:

```
Hey Claude, what's my 3D printer's current status?
```

Claude should respond with real-time printer information!

Other things to try:
- "List my cloud files"
- "What filaments are in my AMS?"
- "Show me the current print progress"

## Troubleshooting

### Build Fails
- Check Railway logs (click "Deployments" → Latest deployment → "View Logs")
- Look for Python errors
- Verify Dockerfile syntax

### Health Check Fails
```bash
# Test manually
curl https://your-url.railway.app/health

# Check Railway logs for errors
```

### Authentication Fails
- Verify `BAMBU_EMAIL` and `BAMBU_PASSWORD` are correct
- Try logging into Bambu Handy app with same credentials
- If 2FA is enabled, make sure you completed Step 7

### Claude Can't Connect
- Verify URL in `claude_desktop_config.json`
- Ensure URL ends with `/sse`
- Check Railway is showing "Active" status
- Restart Claude Desktop completely
- Check Claude logs:
  - macOS: `~/Library/Logs/Claude/mcp*.log`
  - Windows: `%APPDATA%\Claude\logs\mcp*.log`

### Tools Don't Work
- Ensure printer is online (check Bambu Handy app)
- Verify `BAMBU_DEVICE_ID` is correct (0948BB5B1200532)
- Check Railway logs for API errors

## Success Checklist

- [ ] Railway project created
- [ ] Environment variables set (email, password, device ID)
- [ ] Build succeeded
- [ ] Health check passes
- [ ] Domain generated and copied
- [ ] 2FA completed (if needed)
- [ ] Claude Desktop config updated
- [ ] Claude Desktop restarted
- [ ] Test command works in Claude

## Quick Reference

**GitHub**: https://github.com/Skin-Confidence-Group/bambu-mcp-server
**Organization**: Skin-Confidence-Group
**Railway**: https://railway.app
**Your Printer**: Bambu Lab H2D (Serial: 0948BB5B1200532)
**AMS**: AMS 2 Pro (Serial: 19C06A5A3100241)

## What's Next?

Once deployed, you can:
- Monitor prints from anywhere via Claude
- Upload 3MF files to cloud storage
- Start/stop prints remotely
- Check filament levels
- View real-time temperatures and progress

## Need Help?

- **Deployment issues**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **2FA problems**: [SETUP_2FA.md](SETUP_2FA.md)
- **Quick reference**: [QUICK_START.md](QUICK_START.md)
- **Full docs**: [README.md](README.md)

---

**Ready? Let's deploy!** 🚀

Start at: https://railway.app
