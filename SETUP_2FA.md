# 2FA Authentication Setup Guide

This guide covers the one-time setup process for authenticating with Bambu Cloud when 2FA is enabled.

## Overview

Bambu Cloud uses email-based 2FA (not printer-based). The setup flow:

1. Deploy to Railway with email/password (no token yet)
2. Call `/setup/login` endpoint to trigger 2FA email
3. Check your email for the verification code
4. Call `/setup/verify` with the code to get the access token
5. Add the token to Railway environment variables
6. Redeploy - server will use the cached token going forward

## Prerequisites

- Railway deployment complete
- Bambu Lab account credentials (email/password)
- Access to your email for 2FA codes

## Option 1: Simple Setup (No Setup Key)

If you skip setting `SETUP_KEY`, the endpoints are publicly accessible (but still require knowledge of the URLs).

### Step 1: Deploy Without Token

In Railway, set only these variables:
```
BAMBU_EMAIL=your-email@example.com
BAMBU_PASSWORD=your-password
BAMBU_DEVICE_ID=0948BB5B1200532
```

**Do not set** `BAMBU_TOKEN` yet.

Deploy the app. It may show auth errors in logs - this is expected.

### Step 2: Initiate Login

```bash
curl -X POST https://your-app.railway.app/setup/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "your-password"
  }'
```

Response:
```json
{
  "success": true,
  "has_token": false,
  "message": "2FA code sent to your email",
  "instructions": "Check your email for the verification code..."
}
```

If you're lucky and 2FA is disabled, you'll get:
```json
{
  "success": true,
  "has_token": true,
  "token": "eyJhbGciOiJIUzI1...",
  "message": "Authentication successful (no 2FA required)"
}
```

Skip to Step 4 if you got the token immediately.

### Step 3: Check Email & Verify

Check your email for a message from Bambu Lab with a verification code (usually 6 digits).

Then verify:
```bash
curl -X POST https://your-app.railway.app/setup/verify \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "code": "123456"
  }'
```

Response:
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "message": "Authentication successful!",
  "instructions": "1. Copy the token above\n2. Go to Railway dashboard..."
}
```

### Step 4: Save Token to Railway

1. Copy the `token` from the response
2. Go to Railway dashboard → Your project → Variables
3. Click "New Variable"
4. Set `BAMBU_TOKEN` to the token value
5. Click "Add"
6. Railway will automatically redeploy

### Step 5: (Optional) Remove Password

For security, you can now remove `BAMBU_PASSWORD`:

1. In Railway Variables, delete `BAMBU_PASSWORD`
2. Keep `BAMBU_EMAIL` and `BAMBU_TOKEN`
3. Redeploy

The server will use the cached token and won't need the password anymore.

## Option 2: Secure Setup (With Setup Key)

Recommended for production - protects the setup endpoints with a secret key.

### Step 1: Generate Setup Key

```bash
# Generate a random 32-byte hex string
openssl rand -hex 32
```

Example output:
```
a7f9e2c3b8d4a1f5e9c7b2d6f8a3e1c4d9f7b5a2e8c6d1f4a9b7e3c5d2f8a6b1
```

### Step 2: Deploy With Setup Key

In Railway, set:
```
BAMBU_EMAIL=your-email@example.com
BAMBU_PASSWORD=your-password
BAMBU_DEVICE_ID=0948BB5B1200532
SETUP_KEY=a7f9e2c3b8d4a1f5e9c7b2d6f8a3e1c4d9f7b5a2e8c6d1f4a9b7e3c5d2f8a6b1
```

### Step 3: Initiate Login (With Header)

```bash
curl -X POST https://your-app.railway.app/setup/login \
  -H "Content-Type: application/json" \
  -H "X-Setup-Key: a7f9e2c3b8d4a1f5e9c7b2d6f8a3e1c4d9f7b5a2e8c6d1f4a9b7e3c5d2f8a6b1" \
  -d '{
    "email": "your-email@example.com",
    "password": "your-password"
  }'
```

Note the `X-Setup-Key` header matching your Railway variable.

### Step 4: Verify With Header

```bash
curl -X POST https://your-app.railway.app/setup/verify \
  -H "Content-Type: application/json" \
  -H "X-Setup-Key: a7f9e2c3b8d4a1f5e9c7b2d6f8a3e1c4d9f7b5a2e8c6d1f4a9b7e3c5d2f8a6b1" \
  -d '{
    "email": "your-email@example.com",
    "code": "123456"
  }'
```

### Step 5: Save Token & Clean Up

1. Add `BAMBU_TOKEN` to Railway (same as Option 1)
2. Redeploy
3. (Optional) Delete `BAMBU_PASSWORD` and `SETUP_KEY` for security
4. Now only the token is stored

## Check Setup Status

Check if setup is complete:

```bash
curl https://your-app.railway.app/setup/status
```

Response when setup is complete:
```json
{
  "setup_complete": true,
  "has_token": true,
  "device_id": "0948BB5B1200532",
  "message": "Setup complete! Server is ready to use."
}
```

Response when token is missing:
```json
{
  "setup_complete": false,
  "has_token": false,
  "device_id": "0948BB5B1200532",
  "message": "Setup required. Call POST /setup/login to begin."
}
```

## Testing with curl Scripts

Create a local `setup.sh` script:

```bash
#!/bin/bash
# setup.sh - Automate 2FA setup

RAILWAY_URL="https://your-app.railway.app"
SETUP_KEY="your-setup-key-here"  # Optional
EMAIL="your-email@example.com"
PASSWORD="your-password"

# Step 1: Login
echo "🔐 Initiating login..."
if [ -n "$SETUP_KEY" ]; then
  RESPONSE=$(curl -s -X POST "$RAILWAY_URL/setup/login" \
    -H "Content-Type: application/json" \
    -H "X-Setup-Key: $SETUP_KEY" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")
else
  RESPONSE=$(curl -s -X POST "$RAILWAY_URL/setup/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")
fi

echo "$RESPONSE" | jq .

# Check if we got a token immediately
HAS_TOKEN=$(echo "$RESPONSE" | jq -r '.has_token')
if [ "$HAS_TOKEN" = "true" ]; then
  TOKEN=$(echo "$RESPONSE" | jq -r '.token')
  echo ""
  echo "✅ Got token without 2FA!"
  echo "🔑 Token: $TOKEN"
  echo ""
  echo "Add this to Railway:"
  echo "BAMBU_TOKEN=$TOKEN"
  exit 0
fi

# Step 2: Wait for user to get code
echo ""
echo "📧 Check your email for the 2FA code"
read -p "Enter the code: " CODE

# Step 3: Verify
echo "🔍 Verifying code..."
if [ -n "$SETUP_KEY" ]; then
  RESPONSE=$(curl -s -X POST "$RAILWAY_URL/setup/verify" \
    -H "Content-Type: application/json" \
    -H "X-Setup-Key: $SETUP_KEY" \
    -d "{\"email\":\"$EMAIL\",\"code\":\"$CODE\"}")
else
  RESPONSE=$(curl -s -X POST "$RAILWAY_URL/setup/verify" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$EMAIL\",\"code\":\"$CODE\"}")
fi

echo "$RESPONSE" | jq .

# Extract and display token
TOKEN=$(echo "$RESPONSE" | jq -r '.token')
if [ "$TOKEN" != "null" ]; then
  echo ""
  echo "✅ Authentication successful!"
  echo "🔑 Token: $TOKEN"
  echo ""
  echo "Add this to Railway Variables:"
  echo "BAMBU_TOKEN=$TOKEN"
else
  echo "❌ Verification failed"
  exit 1
fi
```

Make it executable:
```bash
chmod +x setup.sh
./setup.sh
```

## Troubleshooting

### "Invalid or missing X-Setup-Key header"

You set `SETUP_KEY` in Railway but forgot to include the header in your curl request. Either:
- Add `-H "X-Setup-Key: your-key"` to your curl command, or
- Remove `SETUP_KEY` from Railway to disable protection

### "No pending authentication for this email"

You called `/setup/verify` without calling `/setup/login` first. The flow must be:
1. `/setup/login` (sends email)
2. `/setup/verify` (uses code)

The session is stored in memory and cleared after 30 minutes of inactivity.

### "Verification failed"

- Double-check the 2FA code (case-sensitive, no spaces)
- Make sure you're using the most recent code
- Codes expire after a few minutes - request a new one if needed

### "2FA verification not yet implemented"

The `bambu-lab-cloud-api` library may not support the 2FA verification method used in this code. You'll need to:

1. Check the library documentation for the correct 2FA flow
2. Update [setup.py](src/bambu_mcp/setup.py) `verify_2fa()` method accordingly
3. Or manually authenticate using the library's CLI tool and paste the token into Railway

### Token Expires

If your token expires (usually after 30-90 days):

1. The server will auto-refresh if `BAMBU_EMAIL` and `BAMBU_PASSWORD` are still set
2. If you removed the password, run the setup flow again to get a new token
3. Update `BAMBU_TOKEN` in Railway

## Alternative: Local Token Generation

If the Railway setup flow doesn't work, generate the token locally:

```python
# get_token.py
import asyncio
from bambulab import BambuAuthenticator

async def get_token():
    auth = BambuAuthenticator(
        email="your-email@example.com",
        password="your-password"
    )

    # This will prompt for 2FA if needed
    result = await auth.authenticate()
    print(f"Token: {result['accessToken']}")

asyncio.run(get_token())
```

Run:
```bash
python get_token.py
```

Then paste the token into Railway as `BAMBU_TOKEN`.

## Security Best Practices

1. **Use SETUP_KEY** in production to protect setup endpoints
2. **Delete SETUP_KEY** after setup is complete (no longer needed)
3. **Delete BAMBU_PASSWORD** after getting token (optional but recommended)
4. **Never commit** tokens or credentials to git
5. **Rotate tokens** every 90 days (or when compromised)
6. **Use HTTPS** only (Railway enforces this automatically)

## What Happens After Setup?

Once `BAMBU_TOKEN` is set:

1. Server uses the cached token on startup (no password needed)
2. Token is auto-refreshed when it expires (if email/password still available)
3. `/setup` endpoints can be disabled by removing `SETUP_KEY`
4. MCP tools work normally - Claude Desktop can connect

You're ready to use the MCP server!

## Next Steps

After successful setup:

1. Configure Claude Desktop with your Railway URL
2. Test the MCP tools
3. (Optional) Set up monitoring/alerts
4. Enjoy controlling your 3D printer with Claude!
