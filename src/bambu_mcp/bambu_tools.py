"""Bambu Lab printer tools implementation."""
import logging
from typing import Any, Optional
from bambulab import BambuClient, MQTTClient
from .auth import BambuAuthManager
from .config import Settings

logger = logging.getLogger(__name__)


class BambuPrinterTools:
    """Tools for interacting with Bambu Lab printer via Cloud API."""

    def __init__(self, settings: Settings, auth_manager: BambuAuthManager):
        self.settings = settings
        self.auth_manager = auth_manager
        self.client: Optional[BambuClient] = None
        self.mqtt_client: Optional[MQTTClient] = None

    async def _get_client(self) -> BambuClient:
        """Get or create Bambu API client."""
        if not self.client:
            token = await self.auth_manager.get_token()
            # New API: BambuClient takes 'token' parameter (not 'access_token')
            self.client = BambuClient(token=token)
        return self.client

    async def _get_mqtt_client(self) -> MQTTClient:
        """Get or create MQTT client for real-time data."""
        if not self.mqtt_client:
            token = await self.auth_manager.get_token()
            self.mqtt_client = MQTTClient(
                access_token=token,
                device_id=self.settings.bambu_device_id
            )
            await self.mqtt_client.connect()
        return self.mqtt_client

    async def get_printer_status(self) -> dict[str, Any]:
        """
        Get current printer status including temperatures and print progress.

        Returns:
            dict: Printer status information
        """
        try:
            client = await self._get_client()
            # New API: get_print_status() returns print status for specific device
            print_status = client.get_print_status(self.settings.bambu_device_id)
            device_info = client.get_device_info(self.settings.bambu_device_id)

            return {
                "device_id": self.settings.bambu_device_id,
                "device_info": device_info,
                "print_status": print_status,
                "status": print_status.get("gcode_state", "unknown") if print_status else "unknown",
            }
        except Exception as e:
            logger.error(f"Error getting printer status: {e}")
            raise

    async def list_cloud_files(self) -> dict[str, Any]:
        """
        List files stored in Bambu Cloud.

        Returns:
            dict: Cloud file listing
        """
        try:
            client = await self._get_client()
            # New API: get_cloud_files() is synchronous
            files_response = client.get_cloud_files()

            return {
                "files": files_response if isinstance(files_response, list) else files_response.get("files", []),
                "total_count": len(files_response) if isinstance(files_response, list) else len(files_response.get("files", [])),
                "raw_response": files_response,
            }
        except Exception as e:
            logger.error(f"Error listing cloud files: {e}")
            raise

    async def upload_file(self, file_path: str, file_name: Optional[str] = None) -> dict[str, Any]:
        """
        Upload a 3MF file to Bambu Cloud.

        Args:
            file_path: Local path to the 3MF file
            file_name: Optional custom name for the file

        Returns:
            dict: Upload result
        """
        try:
            client = await self._get_client()

            # New API: upload_file() is synchronous
            result = client.upload_file(
                file_path=file_path,
                file_name=file_name
            )

            return {
                "success": True,
                "result": result,
                "message": "File uploaded successfully",
            }
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise

    async def start_print(self, file_id: str, plate_number: int = 1) -> dict[str, Any]:
        """
        Start a print job from a cloud file.

        Args:
            file_id: Cloud file ID to print
            plate_number: Build plate number (default: 1)

        Returns:
            dict: Print start result
        """
        try:
            client = await self._get_client()
            # New API: start_cloud_print() is synchronous
            result = client.start_cloud_print(
                device_id=self.settings.bambu_device_id,
                file_id=file_id,
                plate_number=plate_number
            )

            return {
                "success": True,
                "result": result,
                "message": "Print started successfully",
            }
        except Exception as e:
            logger.error(f"Error starting print: {e}")
            raise

    async def pause_print(self) -> dict[str, Any]:
        """
        Pause the current print job.

        Returns:
            dict: Pause result
        """
        try:
            # Note: The new API may not have direct pause/resume/cancel methods
            # These might need to be done via MQTT or tasks API
            return {
                "success": False,
                "message": "Pause functionality requires MQTT or Tasks API - not yet implemented",
            }
        except Exception as e:
            logger.error(f"Error pausing print: {e}")
            raise

    async def resume_print(self) -> dict[str, Any]:
        """
        Resume a paused print job.

        Returns:
            dict: Resume result
        """
        try:
            # Note: The new API may not have direct pause/resume/cancel methods
            return {
                "success": False,
                "message": "Resume functionality requires MQTT or Tasks API - not yet implemented",
            }
        except Exception as e:
            logger.error(f"Error resuming print: {e}")
            raise

    async def cancel_print(self) -> dict[str, Any]:
        """
        Cancel the current print job.

        Returns:
            dict: Cancel result
        """
        try:
            # Note: The new API may not have direct pause/resume/cancel methods
            return {
                "success": False,
                "message": "Cancel functionality requires MQTT or Tasks API - not yet implemented",
            }
        except Exception as e:
            logger.error(f"Error cancelling print: {e}")
            raise

    async def get_ams_status(self) -> dict[str, Any]:
        """
        Get AMS (Automatic Material System) status and filament information.

        Returns:
            dict: AMS status with filament slots
        """
        try:
            client = await self._get_client()
            # New API: get_ams_filaments() is synchronous
            ams_data = client.get_ams_filaments(self.settings.bambu_device_id)

            return {
                "ams_serial": "19C06A5A3100241",
                "ams_model": "AMS 2 Pro",
                "device_id": self.settings.bambu_device_id,
                "ams_data": ams_data,
            }
        except Exception as e:
            logger.error(f"Error getting AMS status: {e}")
            raise

    async def list_presets(self) -> dict[str, Any]:
        """
        List available Bambu Studio presets (if accessible via API).

        Returns:
            dict: Available presets
        """
        try:
            client = await self._get_client()

            # New API: Check if get_slicer_settings is available
            try:
                slicer_settings = client.get_slicer_settings()
                return {
                    "supported": True,
                    "slicer_settings": slicer_settings,
                }
            except (AttributeError, Exception) as e:
                logger.warning(f"Preset listing not supported: {e}")
                return {
                    "supported": False,
                    "message": "Preset listing not available via Cloud API. Use Bambu Studio locally.",
                }
        except Exception as e:
            logger.error(f"Error listing presets: {e}")
            raise

    async def cleanup(self):
        """Clean up connections."""
        if self.mqtt_client:
            await self.mqtt_client.disconnect()
