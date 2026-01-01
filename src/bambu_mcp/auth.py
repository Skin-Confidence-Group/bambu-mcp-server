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

            # Initialize authenticator (new API - no args in constructor)
            self.authenticator = BambuAuthenticator()

            # Perform authentication (sync method, not async)
            # This will raise an exception if 2FA code is needed
            self._token = self.authenticator.login(
                username=self.settings.bambu_email,
                password=self.settings.bambu_password
            )

            if not self._token:
                raise Exception("Authentication failed: No access token received")

            logger.info("Successfully authenticated with Bambu Cloud")

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
