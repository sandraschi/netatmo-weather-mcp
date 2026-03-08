"""
Weather monitoring tools for Netatmo weather stations.

Provides portmanteau pattern tools for comprehensive weather station management,
data retrieval, and monitoring operations.
"""

import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

import structlog

from ..core.netatmo_client import NetatmoClient, NetatmoCredentials
from ..core.exceptions import NetatmoError, DeviceNotFoundError, DataUnavailableError

logger = structlog.get_logger(__name__)


class WeatherMonitoringTools:
    """Portmanteau weather monitoring tools with conversational AI support."""

    def __init__(self, credentials: Optional[NetatmoCredentials] = None):
        self._credentials = credentials
        self._client: Optional[NetatmoClient] = None

    async def _get_client(self) -> NetatmoClient:
        """Lazy initialization of Netatmo client."""
        if self._client is None:
            self._client = NetatmoClient(self._credentials) if self._credentials else NetatmoClient()
        return self._client

    async def manage_stations(
        self,
        operation: str,
        station_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Manage weather stations with comprehensive operations.

        Args:
            operation: Operation type ('list', 'get_info', 'get_status')
            station_id: Station ID for specific operations

        Returns:
            Dict with operation results and conversational context
        """
        try:
            client = await self._get_client()

            if operation == "list":
                stations = await client.get_stations()
                return {
                    "success": True,
                    "operation": "list_stations",
                    "stations": [
                        {
                            "id": s.id,
                            "name": s.name,
                            "home_name": s.home_name,
                            "reachable": s.reachable,
                            "modules_count": len(s.modules),
                            "data_types": s.data_types
                        }
                        for s in stations
                    ],
                    "total_count": len(stations),
                    "reachable_count": sum(1 for s in stations if s.reachable)
                }

            elif operation == "get_info":
                if not station_id:
                    raise ValueError("station_id required for get_info operation")

                stations = await client.get_stations()
                station = next((s for s in stations if s.id == station_id), None)

                if not station:
                    raise DeviceNotFoundError(station_id, "station")

                return {
                    "success": True,
                    "operation": "get_station_info",
                    "station": {
                        "id": station.id,
                        "name": station.name,
                        "home_id": station.home_id,
                        "home_name": station.home_name,
                        "reachable": station.reachable,
                        "data_types": station.data_types,
                        "last_seen": station.last_seen.isoformat() if station.last_seen else None,
                        "modules": [
                            {
                                "id": m["id"],
                                "name": m["name"],
                                "type": m["type"],
                                "reachable": m["reachable"]
                            }
                            for m in station.modules
                        ]
                    }
                }

            elif operation == "get_status":
                if not station_id:
                    raise ValueError("station_id required for get_status operation")

                status = await client.get_station_status(station_id)
                return {
                    "success": True,
                    "operation": "get_station_status",
                    "status": status
                }

            else:
                raise ValueError(f"Unsupported operation: {operation}")

        except Exception as e:
            logger.error("Station management operation failed",
                        operation=operation, station_id=station_id, error=str(e))
            return {
                "success": False,
                "operation": operation,
                "error": str(e),
                "error_type": type(e).__name__
            }

    async def process_weather_data(
        self,
        operation: str,
        station_id: str,
        timeframe: Optional[str] = "1h",
        data_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process weather data with comprehensive operations.

        Args:
            operation: Operation type ('current', 'historical', 'sample', 'analyze')
            station_id: Weather station ID
            timeframe: Timeframe for historical operations
            data_types: Specific data types to retrieve

        Returns:
            Dict with weather data and processing results
        """
        try:
            client = await self._get_client()

            if operation == "current":
                weather_data = await client.get_station_data(station_id)

                return {
                    "success": True,
                    "operation": "get_current_weather",
                    "station_id": station_id,
                    "timestamp": weather_data.timestamp.isoformat(),
                    "data": {
                        "temperature": weather_data.temperature,
                        "humidity": weather_data.humidity,
                        "pressure": weather_data.pressure,
                        "co2": weather_data.co2,
                        "noise": weather_data.noise,
                        "rain": weather_data.rain,
                        "wind_strength": weather_data.wind_strength,
                        "wind_angle": weather_data.wind_angle,
                        "gust_strength": weather_data.gust_strength,
                        "gust_angle": weather_data.gust_angle
                    },
                    "data_points": sum(1 for v in [
                        weather_data.temperature, weather_data.humidity, weather_data.pressure,
                        weather_data.co2, weather_data.noise, weather_data.rain,
                        weather_data.wind_strength, weather_data.wind_angle,
                        weather_data.gust_strength, weather_data.gust_angle
                    ] if v is not None)
                }

            elif operation == "historical":
                # Parse timeframe
                if timeframe.endswith("h"):
                    hours = int(timeframe[:-1])
                    start_date = datetime.now() - timedelta(hours=hours)
                elif timeframe.endswith("d"):
                    days = int(timeframe[:-1])
                    start_date = datetime.now() - timedelta(days=days)
                else:
                    raise ValueError(f"Unsupported timeframe format: {timeframe}")

                end_date = datetime.now()

                historical_data = await client.get_historical_data(
                    station_id, start_date, end_date, data_types
                )

                return {
                    "success": True,
                    "operation": "get_historical_weather",
                    "station_id": station_id,
                    "timeframe": timeframe,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "historical_data": [
                        {
                            "timestamp": data.timestamp.isoformat(),
                            "temperature": data.temperature,
                            "humidity": data.humidity,
                            "pressure": data.pressure,
                            "co2": data.co2,
                            "noise": data.noise,
                            "rain": data.rain,
                            "wind_strength": data.wind_strength,
                            "wind_angle": data.wind_angle,
                            "gust_strength": data.gust_strength,
                            "gust_angle": data.gust_angle
                        }
                        for data in historical_data
                    ],
                    "record_count": len(historical_data)
                }

            elif operation == "sample":
                # Generate weather data samples for AI training
                current_data = await client.get_station_data(station_id)

                # Create variations for sampling
                samples = []
                base_temp = current_data.temperature or 20.0

                for i in range(5):  # Generate 5 samples
                    variation = {
                        "sample_id": i + 1,
                        "timestamp": (datetime.now() + timedelta(minutes=i*10)).isoformat(),
                        "temperature": base_temp + (i - 2) * 0.5,  # +/- 2 degrees
                        "humidity": min(100, max(0, (current_data.humidity or 50) + (i - 2) * 2)),
                        "pressure": (current_data.pressure or 1013) + (i - 2) * 2,
                        "co2": (current_data.co2 or 400) + (i - 2) * 10,
                        "noise": (current_data.noise or 30) + (i - 2) * 2,
                        "variation_type": "ai_generated_sample"
                    }
                    samples.append(variation)

                return {
                    "success": True,
                    "operation": "sample_weather_data",
                    "station_id": station_id,
                    "samples": samples,
                    "sample_count": len(samples),
                    "base_conditions": {
                        "temperature": current_data.temperature,
                        "humidity": current_data.humidity,
                        "pressure": current_data.pressure
                    }
                }

            elif operation == "analyze":
                # Basic weather data analysis
                historical_data = await client.get_historical_data(
                    station_id,
                    datetime.now() - timedelta(hours=24),
                    datetime.now()
                )

                if not historical_data:
                    return {
                        "success": True,
                        "operation": "analyze_weather",
                        "station_id": station_id,
                        "analysis": "insufficient_data",
                        "message": "Not enough historical data for analysis"
                    }

                # Calculate basic statistics
                temperatures = [d.temperature for d in historical_data if d.temperature is not None]
                humidities = [d.humidity for d in historical_data if d.humidity is not None]

                analysis = {
                    "data_points": len(historical_data),
                    "temperature_range": {
                        "min": min(temperatures) if temperatures else None,
                        "max": max(temperatures) if temperatures else None,
                        "avg": sum(temperatures) / len(temperatures) if temperatures else None
                    },
                    "humidity_range": {
                        "min": min(humidities) if humidities else None,
                        "max": max(humidities) if humidities else None,
                        "avg": sum(humidities) / len(humidities) if humidities else None
                    },
                    "time_span_hours": 24,
                    "analysis_type": "basic_statistics"
                }

                return {
                    "success": True,
                    "operation": "analyze_weather",
                    "station_id": station_id,
                    "analysis": analysis
                }

            else:
                raise ValueError(f"Unsupported operation: {operation}")

        except Exception as e:
            logger.error("Weather data processing failed",
                        operation=operation, station_id=station_id, error=str(e))
            return {
                "success": False,
                "operation": operation,
                "station_id": station_id,
                "error": str(e),
                "error_type": type(e).__name__
            }