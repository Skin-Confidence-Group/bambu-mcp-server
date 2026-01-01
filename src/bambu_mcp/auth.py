"""Bambu Lab Cloud authentication manager with token caching."""
import logging
from typing import Optional
from bambulab import BambuAuthenticator
from .config import Settings

logger = logging.getLogger(__name__)


class BambuAuthManager:
    """Manages authentication with Bambu Cloud API."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.authenticator: Optional[BambuAuthenticator] = None
        self._token: Optional[str] = settings.bambu_token

    async def authenticate(self) -> str:
        """
        Authenticate with Bambu Cloud and return access token.

        Returns:
            str: Access token for API requests

        Raises:
            Exception: If authentication fails
        """
        try:
            # Use cached token if available
            if self._token:
                logger.info("Using cached authentication token")
                return self._token

            logger.info(f"Authenticating with Bambu Cloud as {self.settings.bambu_email}")

            # Initialize authenticator
            self.authenticator = BambuAuthenticator(
                email=self.settings.bambu_email,
                password=self.settings.bambu_password
            )

            # Perform authentication
            auth_response = await self.authenticator.authenticate()

            if not auth_response or not auth_response.get("accessToken"):
                raise Exception("Authentication failed: No access token received")

            self._token = auth_response["accessToken"]
            logger.info("Successfully authenticated with Bambu Cloud")

            # In production, you might want to save this token to persistent storage
            # For now, we'll just keep it in memory

            return self._token

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise Exception(f"Failed to authenticate with Bambu Cloud: {e}")

    async def get_token(self) -> str:
        """
        Get valid access token, authenticating if necessary.

        Returns:
            str: Valid access token
        """
        if not self._token:
            await self.authenticate()
        return self._token

    def invalidate_token(self):
        """Invalidate the current token, forcing re-authentication."""
        logger.info("Invalidating cached token")
        self._token = None
