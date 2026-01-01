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
            self.client = BambuClient(
                access_token=token,
                device_id=self.settings.bambu_device_id
            )
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
            status = await client.get_device_status()

            return {
                "device_id": self.settings.bambu_device_id,
                "status": status.get("status", "unknown"),
                "print_progress": status.get("print_progress", 0),
                "temperatures": {
                    "nozzle": status.get("nozzle_temp", 0),
                    "bed": status.get("bed_temp", 0),
                    "chamber": status.get("chamber_temp", 0),
                },
                "current_file": status.get("current_file"),
                "layer_info": {
                    "current": status.get("current_layer", 0),
                    "total": status.get("total_layers", 0),
                },
                "time_remaining": status.get("time_remaining", 0),
                "raw_status": status,
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
            files = await client.get_cloud_files()

            return {
                "files": [
                    {
                        "name": f.get("name"),
                        "id": f.get("id"),
                        "size": f.get("size"),
                        "uploaded_at": f.get("uploaded_at"),
                        "thumbnail": f.get("thumbnail_url"),
                    }
                    for f in files.get("files", [])
                ],
                "total_count": len(files.get("files", [])),
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

            with open(file_path, "rb") as f:
                file_data = f.read()

            result = await client.upload_file(
                file_data=file_data,
                file_name=file_name or file_path.split("/")[-1]
            )

            return {
                "success": True,
                "file_id": result.get("file_id"),
                "file_name": result.get("file_name"),
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
            result = await client.start_print(
                file_id=file_id,
                plate_number=plate_number
            )

            return {
                "success": True,
                "job_id": result.get("job_id"),
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
            client = await self._get_client()
            await client.pause_print()

            return {
                "success": True,
                "message": "Print paused successfully",
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
            client = await self._get_client()
            await client.resume_print()

            return {
                "success": True,
                "message": "Print resumed successfully",
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
            client = await self._get_client()
            await client.cancel_print()

            return {
                "success": True,
                "message": "Print cancelled successfully",
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
            ams_data = await client.get_ams_status()

            slots = []
            for slot in ams_data.get("slots", []):
                slots.append({
                    "slot_number": slot.get("slot_id"),
                    "color": slot.get("color"),
                    "material_type": slot.get("material_type"),
                    "remaining": slot.get("remaining_percentage", 0),
                    "empty": slot.get("is_empty", True),
                })

            return {
                "ams_serial": "19C06A5A3100241",
                "ams_model": "AMS 2 Pro",
                "slots": slots,
                "total_slots": len(slots),
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

            # Note: This depends on what the bambu-lab-cloud-api library supports
            # If presets aren't available via cloud API, we'll return a placeholder
            try:
                presets = await client.get_presets()
            except AttributeError:
                logger.warning("Preset listing not supported by current API version")
                return {
                    "supported": False,
                    "message": "Preset listing not available via Cloud API. Use Bambu Studio locally.",
                }

            return {
                "supported": True,
                "print_presets": presets.get("print", []),
                "filament_presets": presets.get("filament", []),
                "machine_presets": presets.get("machine", []),
            }
        except Exception as e:
            logger.error(f"Error listing presets: {e}")
            raise

    async def cleanup(self):
        """Clean up connections."""
        if self.mqtt_client:
            await self.mqtt_client.disconnect()
