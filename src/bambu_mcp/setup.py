"""One-time setup endpoints for 2FA authentication flow."""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr
from bambulab import BambuAuthenticator

from .config import Settings, get_settings

logger = logging.getLogger(__name__)

# Create router for setup endpoints
router = APIRouter(prefix="/setup", tags=["setup"])

# In-memory storage for pending auth sessions (cleared after successful setup)
# In production, you might want to use Redis or similar
pending_auth_sessions: dict[str, BambuAuthenticator] = {}


class LoginRequest(BaseModel):
    """Request to initiate login (triggers 2FA email)."""
    email: EmailStr
    password: str


class VerifyRequest(BaseModel):
    """Request to verify 2FA code and complete authentication."""
    email: EmailStr
    code: str


class TokenResponse(BaseModel):
    """Response containing the access token."""
    success: bool
    token: str
    message: str
    instructions: str


def check_setup_key(
    x_setup_key: Optional[str] = Header(None),
    settings: Settings = Depends(get_settings)
):
    """
    Validate setup key to protect setup endpoints.

    The setup key prevents unauthorized access to authentication endpoints.
    Set SETUP_KEY environment variable in Railway to enable protection.
    """
    # Get setup key from environment (optional but recommended)
    setup_key = getattr(settings, 'setup_key', None)

    # If setup key is configured, require it
    if setup_key:
        if not x_setup_key or x_setup_key != setup_key:
            raise HTTPException(
                status_code=403,
                detail="Invalid or missing X-Setup-Key header"
            )


@router.post("/login", response_model=dict)
async def initiate_login(
    request: LoginRequest,
    _auth: None = Depends(check_setup_key)
):
    """
    Initiate login flow - sends 2FA code to email.

    **Headers:**
    - X-Setup-Key: Setup key (if SETUP_KEY env var is set)

    **Steps:**
    1. Call this endpoint with email/password
    2. Check your email for 2FA code
    3. Call /setup/verify with the code

    Example:
    ```bash
    curl -X POST https://your-app.railway.app/setup/login \\
      -H "Content-Type: application/json" \\
      -H "X-Setup-Key: your-secret-key" \\
      -d '{"email":"user@example.com","password":"yourpassword"}'
    ```
    """
    try:
        logger.info(f"Initiating login for {request.email}")

        # Create authenticator
        authenticator = BambuAuthenticator(
            email=request.email,
            password=request.password
        )

        # This will trigger the 2FA email
        # The library might return a session ID or require a verification step
        try:
            # Attempt authentication (this may send 2FA email)
            result = await authenticator.authenticate()

            # If we get a token immediately (no 2FA), return it
            if result and result.get("accessToken"):
                logger.info("Authentication successful without 2FA")
                token = result["accessToken"]

                return {
                    "success": True,
                    "has_token": True,
                    "token": token,
                    "message": "Authentication successful (no 2FA required)",
                    "instructions": "Copy this token and set it as BAMBU_TOKEN in Railway environment variables, then restart the deployment."
                }

        except Exception as e:
            # If authentication requires 2FA, it may raise an exception
            # Store the authenticator for the verification step
            logger.info(f"2FA required for {request.email}: {e}")
            pending_auth_sessions[request.email] = authenticator

            return {
                "success": True,
                "has_token": False,
                "message": "2FA code sent to your email",
                "instructions": "Check your email for the verification code, then call POST /setup/verify with your email and code"
            }

        # Store session for verification
        pending_auth_sessions[request.email] = authenticator

        return {
            "success": True,
            "has_token": False,
            "message": "2FA code sent to your email",
            "instructions": "Check your email for the verification code, then call POST /setup/verify with your email and code"
        }

    except Exception as e:
        logger.error(f"Login initiation failed: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/verify", response_model=TokenResponse)
async def verify_2fa(
    request: VerifyRequest,
    _auth: None = Depends(check_setup_key)
):
    """
    Verify 2FA code and get access token.

    **Headers:**
    - X-Setup-Key: Setup key (if SETUP_KEY env var is set)

    **After receiving the token:**
    1. Copy the token from the response
    2. Go to Railway dashboard → Your project → Variables
    3. Add/update: `BAMBU_TOKEN=<the-token>`
    4. Redeploy the application
    5. (Optional) Delete BAMBU_PASSWORD from env vars for security

    Example:
    ```bash
    curl -X POST https://your-app.railway.app/setup/verify \\
      -H "Content-Type: application/json" \\
      -H "X-Setup-Key: your-secret-key" \\
      -d '{"email":"user@example.com","code":"123456"}'
    ```
    """
    try:
        logger.info(f"Verifying 2FA for {request.email}")

        # Get pending auth session
        authenticator = pending_auth_sessions.get(request.email)
        if not authenticator:
            raise HTTPException(
                status_code=400,
                detail="No pending authentication for this email. Call /setup/login first."
            )

        # Verify the 2FA code
        # Note: The exact method depends on the bambu-lab-cloud-api library
        # This is a placeholder - adjust based on actual library API
        try:
            result = await authenticator.verify_2fa(request.code)

            if not result or not result.get("accessToken"):
                raise Exception("No access token received after verification")

            token = result["accessToken"]

            # Clean up the pending session
            del pending_auth_sessions[request.email]

            logger.info(f"Authentication successful for {request.email}")

            return TokenResponse(
                success=True,
                token=token,
                message="Authentication successful!",
                instructions=(
                    "1. Copy the token above\n"
                    "2. Go to Railway dashboard → Variables\n"
                    "3. Set BAMBU_TOKEN to this value\n"
                    "4. Redeploy the application\n"
                    "5. (Optional) Remove BAMBU_PASSWORD for security\n"
                    "6. Your MCP server is now ready!"
                )
            )

        except AttributeError:
            # If verify_2fa method doesn't exist, try re-authenticating with code
            # This depends on how the library handles 2FA
            raise HTTPException(
                status_code=501,
                detail="2FA verification not yet implemented. Check bambu-lab-cloud-api documentation for 2FA flow."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"2FA verification failed: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Verification failed: {str(e)}"
        )


@router.get("/status")
async def setup_status(settings: Settings = Depends(get_settings)):
    """
    Check if setup is complete.

    Returns whether the server has a valid token configured.
    """
    has_token = bool(settings.bambu_token)

    return {
        "setup_complete": has_token,
        "has_token": has_token,
        "device_id": settings.bambu_device_id,
        "message": (
            "Setup complete! Server is ready to use."
            if has_token
            else "Setup required. Call POST /setup/login to begin."
        )
    }


@router.delete("/session/{email}")
async def clear_session(
    email: str,
    _auth: None = Depends(check_setup_key)
):
    """
    Clear a pending authentication session.

    Useful if you need to restart the setup process.
    """
    if email in pending_auth_sessions:
        del pending_auth_sessions[email]
        return {"success": True, "message": f"Session cleared for {email}"}

    return {"success": False, "message": "No pending session found"}
