"""Bambu Lab MCP Server with HTTP/SSE transport for Railway deployment."""
import asyncio
import logging
from typing import Any
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
)
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

from .config import get_settings
from .auth import BambuAuthManager
from .bambu_tools import BambuPrinterTools
from .setup import router as setup_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
settings = get_settings()
auth_manager = BambuAuthManager(settings)
bambu_tools = BambuPrinterTools(settings, auth_manager)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(f"Starting Bambu MCP Server v{settings.mcp_server_version}")
    logger.info(f"Device ID: {settings.bambu_device_id}")

    # Initialize authentication on startup
    try:
        await auth_manager.authenticate()
        logger.info("Authentication successful")
    except Exception as e:
        logger.error(f"Failed to authenticate: {e}")

    yield

    # Cleanup on shutdown
    logger.info("Shutting down Bambu MCP Server")
    await bambu_tools.cleanup()


# Create FastAPI app for health checks and SSE
app = FastAPI(
    title="Bambu Lab MCP Server",
    version=settings.mcp_server_version,
    lifespan=lifespan
)

# Include setup router for 2FA authentication flow
app.include_router(setup_router)

# Create MCP server
mcp_server = Server(settings.mcp_server_name)


# Health check endpoint for Railway
@app.get("/health")
async def health_check():
    """Health check endpoint for Railway."""
    return JSONResponse({
        "status": "healthy",
        "server": settings.mcp_server_name,
        "version": settings.mcp_server_version,
        "device_id": settings.bambu_device_id
    })


@app.get("/")
async def root():
    """Root endpoint with server info."""
    return JSONResponse({
        "name": settings.mcp_server_name,
        "version": settings.mcp_server_version,
        "description": "Bambu Lab 3D Printer MCP Server",
        "endpoints": {
            "health": "/health",
            "mcp_sse": "/sse",
            "api_tool": "/api/tool",
        }
    })


@app.post("/api/tool")
async def handle_tool_call(request: dict[str, Any]):
    """HTTP endpoint for tool calls (used by local bridge)."""
    try:
        name = request.get("name")
        arguments = request.get("arguments", {})

        logger.info(f"HTTP tool call: {name} with arguments: {arguments}")

        # Route to appropriate tool handler
        if name == "get_printer_status":
            result = await bambu_tools.get_printer_status()
        elif name == "list_cloud_files":
            result = await bambu_tools.list_cloud_files()
        elif name == "upload_file":
            result = await bambu_tools.upload_file(
                file_path=arguments["file_path"],
                file_name=arguments.get("file_name")
            )
        elif name == "start_print":
            result = await bambu_tools.start_print(
                file_id=arguments["file_id"],
                plate_number=arguments.get("plate_number", 1)
            )
        elif name == "pause_print":
            result = await bambu_tools.pause_print()
        elif name == "resume_print":
            result = await bambu_tools.resume_print()
        elif name == "cancel_print":
            result = await bambu_tools.cancel_print()
        elif name == "get_ams_status":
            result = await bambu_tools.get_ams_status()
        elif name == "list_presets":
            result = await bambu_tools.list_presets()
        else:
            return JSONResponse(
                {"error": f"Unknown tool: {name}"},
                status_code=400
            )

        return JSONResponse(result)

    except Exception as e:
        logger.error(f"HTTP tool call error: {e}", exc_info=True)
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )


# Register MCP tools
@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="get_printer_status",
            description="Get current printer status including temperatures, print progress, and layer information",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="list_cloud_files",
            description="List all files stored in Bambu Cloud storage",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="upload_file",
            description="Upload a 3MF file to Bambu Cloud storage",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Local path to the 3MF file to upload"
                    },
                    "file_name": {
                        "type": "string",
                        "description": "Optional custom name for the uploaded file"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="start_print",
            description="Start a print job from a file in Bambu Cloud",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_id": {
                        "type": "string",
                        "description": "Cloud file ID to print (from list_cloud_files)"
                    },
                    "plate_number": {
                        "type": "integer",
                        "description": "Build plate number (default: 1)",
                        "default": 1
                    }
                },
                "required": ["file_id"]
            }
        ),
        Tool(
            name="pause_print",
            description="Pause the current print job",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="resume_print",
            description="Resume a paused print job",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="cancel_print",
            description="Cancel the current print job",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_ams_status",
            description="Get AMS (Automatic Material System) status with filament slot information",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="list_presets",
            description="List available Bambu Studio presets (print, filament, machine)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    """Handle tool calls."""
    try:
        logger.info(f"Calling tool: {name} with arguments: {arguments}")

        # Route to appropriate tool handler
        if name == "get_printer_status":
            result = await bambu_tools.get_printer_status()

        elif name == "list_cloud_files":
            result = await bambu_tools.list_cloud_files()

        elif name == "upload_file":
            result = await bambu_tools.upload_file(
                file_path=arguments["file_path"],
                file_name=arguments.get("file_name")
            )

        elif name == "start_print":
            result = await bambu_tools.start_print(
                file_id=arguments["file_id"],
                plate_number=arguments.get("plate_number", 1)
            )

        elif name == "pause_print":
            result = await bambu_tools.pause_print()

        elif name == "resume_print":
            result = await bambu_tools.resume_print()

        elif name == "cancel_print":
            result = await bambu_tools.cancel_print()

        elif name == "get_ams_status":
            result = await bambu_tools.get_ams_status()

        elif name == "list_presets":
            result = await bambu_tools.list_presets()

        else:
            raise ValueError(f"Unknown tool: {name}")

        # Format result for MCP
        import json
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )
            ]
        )

    except Exception as e:
        logger.error(f"Tool call error: {e}", exc_info=True)
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )
            ],
            isError=True
        )


# SSE endpoint for MCP
@app.get("/sse")
async def handle_sse(request):
    """Handle SSE connections for MCP."""
    async with SseServerTransport("/messages") as transport:
        await mcp_server.run(
            transport.read_stream,
            transport.write_stream,
            mcp_server.create_initialization_options()
        )


def main():
    """Main entry point for the server."""
    port = settings.port
    logger.info(f"Starting server on port {port}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
