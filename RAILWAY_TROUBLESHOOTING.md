# Railway Deployment Troubleshooting

## Common Railway Deployment Issues

### Issue 1: Build Fails - Missing Environment Variables

**Error**: `ValidationError: 2 validation errors for Settings`

**Cause**: Environment variables not set in Railway before deployment

**Solution**:
1. Go to Railway dashboard → Your project
2. Click on the **Variables** tab
3. Ensure these are set **BEFORE** deployment:
   ```
   BAMBU_EMAIL=your-email@example.com
   BAMBU_PASSWORD=your-password
   BAMBU_DEVICE_ID=0948BB5B1200532
   ```
4. Click **"Redeploy"** in the Deployments tab

**Important**: Railway needs these variables BEFORE it builds the container!

### Issue 2: Health Check Fails

**Error**: `Health check timeout` or `Service unhealthy`

**Possible Causes**:
- Server started but health endpoint not responding
- Wrong PORT configuration
- Authentication failing on startup

**Solutions**:

1. **Check the Logs**:
   - Railway dashboard → Click on your deployment
   - View the logs for startup errors
   - Look for lines starting with "ERROR" or "CRITICAL"

2. **Verify PORT**:
   - Railway automatically sets `$PORT`
   - You don't need to add it manually
   - The Dockerfile uses `${PORT:-8000}` as fallback

3. **Test Health Endpoint**:
   ```bash
   curl https://your-app.railway.app/health
   ```
   Should return:
   ```json
   {"status":"healthy","server":"bambu-printer",...}
   ```

### Issue 3: Authentication Fails on Startup

**Error in logs**: `Failed to authenticate: ...`

**Cause**: Invalid Bambu Lab credentials or 2FA required

**Solutions**:

1. **Verify Credentials**:
   - Test login in Bambu Handy app
   - Ensure no typos in `BAMBU_EMAIL` and `BAMBU_PASSWORD`
   - Password should be URL-safe (no special chars that need escaping)

2. **If 2FA is Enabled**:
   - The server will show auth errors in logs
   - This is EXPECTED on first deploy
   - Follow the 2FA setup in [SETUP_2FA.md](SETUP_2FA.md)
   - Add `BAMBU_TOKEN` to Railway variables
   - Redeploy

### Issue 4: Build Succeeds but Crashes Immediately

**Error in logs**: Python import errors or missing modules

**Check**:
1. Dockerfile installed all dependencies?
2. Look for `ModuleNotFoundError` in logs
3. Check if `requirements.txt` is complete

**Solution**:
```bash
# Locally test the build:
docker build -t bambu-test .
docker run -p 8000:8000 --env-file .env bambu-test
```

### Issue 5: "No default builder" or Docker Issues

**Error**: Railway can't find Dockerfile

**Solution**:
1. Ensure `Dockerfile` is in the repository root
2. Check `railway.json` points to correct path:
   ```json
   "build": {
     "builder": "DOCKERFILE",
     "dockerfilePath": "Dockerfile"
   }
   ```
3. Verify file is committed to git:
   ```bash
   git ls-files | grep Dockerfile
   ```

## Step-by-Step Debugging

### 1. Check Railway Logs

```
Railway Dashboard → Your Project → Deployments → Click latest deployment → View Logs
```

Look for:
- `ERROR` or `CRITICAL` messages
- `ValidationError` (missing env vars)
- `ImportError` (missing dependencies)
- `Failed to authenticate` (Bambu credentials)

### 2. Verify Environment Variables

Required (must be set BEFORE first deployment):
- ✅ `BAMBU_EMAIL`
- ✅ `BAMBU_PASSWORD`
- ✅ `BAMBU_DEVICE_ID`

Auto-set by Railway:
- ✅ `PORT` (do NOT add manually)

Optional (add after 2FA setup):
- `BAMBU_TOKEN`
- `SETUP_KEY`

### 3. Test Locally with Docker

Build the exact Railway environment:

```bash
# Build
docker build -t bambu-test .

# Run with your .env
docker run -p 8000:8000 --env-file .env bambu-test

# Test health
curl http://localhost:8000/health
```

### 4. Check GitHub Repository

Ensure all files are committed:
```bash
git status
git ls-files | grep -E '(Dockerfile|requirements.txt|railway.json)'
```

### 5. Railway Configuration

Check these Railway settings:

**Build Settings**:
- Builder: Dockerfile
- Root Directory: `/`
- Dockerfile Path: `Dockerfile`

**Deploy Settings**:
- Start Command: (leave empty, uses CMD from Dockerfile)
- Health Check Path: `/health`
- Health Check Timeout: 100 seconds

## Quick Fixes

### Fix 1: Redeploy After Adding Variables

If you added environment variables AFTER the first deployment:

1. Go to Deployments tab
2. Click **"Redeploy"** on latest deployment
3. Watch the logs for success

### Fix 2: Check Service is Running

```bash
# Test root endpoint
curl https://your-app.railway.app/

# Test health
curl https://your-app.railway.app/health

# Test setup status
curl https://your-app.railway.app/setup/status
```

### Fix 3: Enable Railway Logs

In Railway dashboard:
1. Click on your service
2. Enable "Persistent Logs"
3. Redeploy to see full output

## Common Error Messages Decoded

### `ValidationError: Field required`
**Meaning**: Missing environment variable
**Fix**: Add the variable in Railway → Variables

### `ModuleNotFoundError: No module named 'X'`
**Meaning**: Dependency not installed
**Fix**: Add to `requirements.txt`, commit, push

### `Failed to authenticate with Bambu Cloud`
**Meaning**: Invalid credentials or 2FA needed
**Fix**: Check credentials or complete 2FA setup

### `Health check timeout`
**Meaning**: Server not responding on /health
**Fix**: Check logs for startup errors, verify PORT

### `Exit code 1` or `Exit code 137`
**Meaning**: Server crashed or OOM (out of memory)
**Fix**: Check logs for Python errors

## Still Stuck?

### Get Railway Logs

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

### Check These Files

1. **Dockerfile** - Correct CMD and EXPOSE?
2. **railway.json** - Correct paths and commands?
3. **requirements.txt** - All dependencies listed?
4. **.env.example** - Shows required variables?

### Test Sequence

1. ✅ Build succeeds (no Python/Docker errors)
2. ✅ Container starts (logs show "Uvicorn running")
3. ✅ Health check passes (200 OK on /health)
4. ✅ Authentication works (or shows expected 2FA error)
5. ✅ MCP endpoint responds (/sse)

## Getting Help

If still failing:

1. **Copy the error** from Railway logs
2. **Check which step fails**:
   - Build stage?
   - Start stage?
   - Health check stage?
3. **Verify variables** are set in Railway
4. **Try local Docker build** to isolate issue

## Success Indicators

✅ Build logs show:
```
Successfully built <image-id>
Successfully tagged <name>
```

✅ Deployment logs show:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:<port>
INFO:     Application startup complete
```

✅ Health check passes:
```
Health check passed for <deployment>
```

✅ Service status:
```
Active - Running
```

Once all green, proceed to [SETUP_2FA.md](SETUP_2FA.md) if needed!
