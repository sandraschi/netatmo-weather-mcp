"""
FastAPI web application for Netatmo Weather MCP webapp.

Exposes REST API for the frontend: health, stations list, station status, current weather.
Uses the same WeatherMonitoringTools as the MCP server.
"""

import logging
import os
from pathlib import Path

# Ensure src is on path when run via uvicorn from repo root or web_sota
_current_file = Path(__file__).resolve()
_src = _current_file.parent.parent
if _src.exists() and str(_src) not in os.environ.get("PYTHONPATH", ""):
    import sys
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .core.netatmo_client import NetatmoCredentials
from .tools.weather_monitoring import WeatherMonitoringTools

logger = logging.getLogger(__name__)


class CredentialsBody(BaseModel):
    """Netatmo credentials from Settings UI."""

    client_id: str
    client_secret: str
    username: str
    password: str
    scope: str = "read_station"

app = FastAPI(
    title="Netatmo Weather MCP API",
    description="REST API for Netatmo weather station data",
    version="1.0.0",
)

_origins = ["http://localhost:10822", "http://127.0.0.1:10822"]
_extra = os.environ.get("WEBAPP_ORIGIN", "").strip()
if _extra:
    _origins.append(_extra)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_tools: Optional[WeatherMonitoringTools] = None
_credentials_override: Optional[NetatmoCredentials] = None


def get_tools() -> WeatherMonitoringTools:
    global _tools
    if _tools is None:
        _tools = WeatherMonitoringTools(credentials=_credentials_override)
    return _tools


@app.get("/api/health")
async def health():
    """Health check for the webapp backend."""
    return {"success": True, "status": "online", "service": "netatmo-weather-mcp"}


@app.get("/api/config/credentials")
async def get_credentials_status():
    """Return whether credentials have been set via Settings (no secrets)."""
    return {"configured": _credentials_override is not None}


@app.post("/api/config/credentials")
async def set_credentials(body: CredentialsBody):
    """Store Netatmo credentials from Settings. Used for this session only (in-memory)."""
    global _credentials_override, _tools
    _credentials_override = NetatmoCredentials(
        client_id=body.client_id,
        client_secret=body.client_secret,
        username=body.username,
        password=body.password,
        scope=body.scope or "read_station",
    )
    _tools = None
    return {"success": True, "message": "Credentials saved for this session."}


@app.get("/api/stations")
async def list_stations():
    """List all Netatmo weather stations."""
    import asyncio
    tools = get_tools()
    result = await tools.manage_stations("list")
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("error", "Station list failed"))
    return result


@app.get("/api/stations/{station_id}")
async def get_station(station_id: str):
    """Get details for one station."""
    tools = get_tools()
    result = await tools.manage_stations("get_info", station_id=station_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "Station not found"))
    return result


@app.get("/api/stations/{station_id}/status")
async def get_station_status(station_id: str):
    """Get reachability/status for one station."""
    tools = get_tools()
    result = await tools.manage_stations("get_status", station_id=station_id)
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("error", "Status failed"))
    return result


@app.get("/api/weather/current")
async def get_current_weather(station_id: str):
    """Get current weather data for a station."""
    tools = get_tools()
    result = await tools.process_weather_data("current", station_id)
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("error", "Weather data failed"))
    return result
