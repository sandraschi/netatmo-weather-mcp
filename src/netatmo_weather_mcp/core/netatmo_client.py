"""
Netatmo API client for weather station data access.

Provides authenticated access to Netatmo weather stations with comprehensive
error handling, caching, and rate limiting.
"""

import asyncio
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import structlog
from pyatmo import AsyncAccount
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .exceptions import (
    AuthenticationError,
    ConfigurationError,
    DataUnavailableError,
    DeviceNotFoundError,
    NetatmoError,
    NetworkError,
    RateLimitError,
    TokenExpiredError,
)

logger = structlog.get_logger(__name__)


@dataclass
class NetatmoCredentials:
    """Netatmo OAuth2 credentials."""

    client_id: str
    client_secret: str
    username: str
    password: str
    scope: str = "read_station read_thermostat write_thermostat"


@dataclass
class WeatherStation:
    """Netatmo weather station information."""

    id: str
    name: str
    home_id: str
    home_name: str
    reachable: bool
    modules: list[dict[str, Any]]
    data_types: list[str]
    last_seen: datetime | None


@dataclass
class WeatherData:
    """Weather measurement data."""

    timestamp: datetime
    temperature: float | None = None
    humidity: int | None = None
    pressure: float | None = None
    co2: int | None = None
    noise: int | None = None
    rain: float | None = None
    wind_strength: float | None = None
    wind_angle: int | None = None
    gust_strength: float | None = None
    gust_angle: int | None = None

    @classmethod
    def from_netatmo_data(cls, data: dict[str, Any]) -> "WeatherData":
        """Create WeatherData from Netatmo API response."""
        dashboard_data = data.get("dashboard_data", {})

        return cls(
            timestamp=datetime.fromtimestamp(data.get("time_utc", time.time())),
            temperature=dashboard_data.get("Temperature"),
            humidity=dashboard_data.get("Humidity"),
            pressure=dashboard_data.get("Pressure"),
            co2=dashboard_data.get("CO2"),
            noise=dashboard_data.get("Noise"),
            rain=dashboard_data.get("Rain"),
            wind_strength=dashboard_data.get("WindStrength"),
            wind_angle=dashboard_data.get("WindAngle"),
            gust_strength=dashboard_data.get("GustStrength"),
            gust_angle=dashboard_data.get("GustAngle"),
        )


class NetatmoClient:
    """Async Netatmo API client with authentication and caching."""

    def __init__(self, credentials: NetatmoCredentials | None = None):
        self.credentials = credentials or self._load_credentials_from_env()
        self._client: AsyncAccount | None = None
        self._stations_cache: dict[str, WeatherStation] = {}
        self._data_cache: dict[str, tuple[WeatherData, float]] = {}  # (data, timestamp)
        self._cache_ttl = 300  # 5 minutes

        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 1.0  # 1 second between requests

    def _load_credentials_from_env(self) -> NetatmoCredentials:
        """Load credentials from environment variables."""
        required_vars = ["NETATMO_CLIENT_ID", "NETATMO_CLIENT_SECRET", "NETATMO_USERNAME", "NETATMO_PASSWORD"]

        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ConfigurationError(
                f"Missing required environment variables: {', '.join(missing_vars)}",
                context={"missing_vars": missing_vars},
            )

        return NetatmoCredentials(
            client_id=os.getenv("NETATMO_CLIENT_ID"),
            client_secret=os.getenv("NETATMO_CLIENT_SECRET"),
            username=os.getenv("NETATMO_USERNAME"),
            password=os.getenv("NETATMO_PASSWORD"),
            scope=os.getenv("NETATMO_SCOPE", "read_station"),
        )

    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid authenticated client."""
        if self._client is None:
            try:
                logger.info("Initializing Netatmo OAuth2 client")
                self._client = AsyncAccount(token_updater=None)
                logger.info("Netatmo authentication successful")
            except Exception as e:
                logger.error("Netatmo authentication failed", error=str(e))
                raise AuthenticationError(
                    f"Failed to authenticate with Netatmo: {e!s}", context={"error_type": type(e).__name__}
                ) from e

    async def _rate_limit_wait(self) -> None:
        """Enforce rate limiting between requests."""
        now = time.time()
        time_since_last = now - self._last_request_time

        if time_since_last < self._min_request_interval:
            wait_time = self._min_request_interval - time_since_last
            await asyncio.sleep(wait_time)

        self._last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((NetworkError, RateLimitError)),
    )
    async def _make_request(self, operation: str, *args, **kwargs) -> Any:
        """Make a rate-limited API request with retry logic."""
        await self._ensure_authenticated()
        await self._rate_limit_wait()

        try:
            if hasattr(self._client, operation):
                method = getattr(self._client, operation)
                if asyncio.iscoroutinefunction(method):
                    return await method(*args, **kwargs)
                else:
                    return method(*args, **kwargs)
            else:
                raise NetatmoError(f"Unsupported operation: {operation}")

        except Exception as e:
            error_msg = str(e).lower()
            if "token" in error_msg and ("expired" in error_msg or "invalid" in error_msg):
                logger.warning("Token expired, resetting client")
                self._client = None
                raise TokenExpiredError(context={"original_error": str(e)}) from e
            elif "rate limit" in error_msg or "429" in error_msg:
                raise RateLimitError(context={"original_error": str(e)}) from e
            elif "network" in error_msg or "connection" in error_msg:
                raise NetworkError(f"Network error during {operation}: {e!s}") from e
            else:
                logger.error(f"API request failed: {operation}", error=str(e))
                raise NetatmoError(f"API request failed: {e!s}") from e

    async def get_stations(self) -> list[WeatherStation]:
        """Get all available weather stations."""
        try:
            # Check cache first
            cache_key = "stations_list"
            if cache_key in self._stations_cache:
                cached_data, cache_time = self._stations_cache[cache_key]
                if time.time() - cache_time < self._cache_ttl:
                    return cached_data

            logger.info("Fetching weather stations from Netatmo API")
            data = await self._make_request("get_stations_data")

            stations = []
            for home in data.get("homes", []):
                home_id = home["id"]
                home_name = home["name"]

                for station in home.get("stations", []):
                    station_id = station["id"]
                    station_name = station["name"]
                    reachable = station.get("reachable", False)

                    # Get available data types
                    data_types = []
                    dashboard_data = station.get("dashboard_data", {})
                    if "Temperature" in dashboard_data:
                        data_types.extend(["temperature", "humidity"])
                    if "Pressure" in dashboard_data:
                        data_types.append("pressure")
                    if "CO2" in dashboard_data:
                        data_types.append("co2")
                    if "Noise" in dashboard_data:
                        data_types.append("noise")

                    # Get modules
                    modules = []
                    for module in home.get("modules", []):
                        if module.get("main_device") == station_id:
                            modules.append(
                                {
                                    "id": module["id"],
                                    "name": module["name"],
                                    "type": module["type"],
                                    "reachable": module.get("reachable", False),
                                }
                            )
                            # Add module-specific data types
                            if module["type"] == "NAModule1":  # Outdoor module
                                data_types.extend(["temperature", "humidity"])
                            elif module["type"] == "NAModule2":  # Wind module
                                data_types.extend(["wind_strength", "wind_angle", "gust_strength", "gust_angle"])
                            elif module["type"] == "NAModule3":  # Rain module
                                data_types.append("rain")

                    weather_station = WeatherStation(
                        id=station_id,
                        name=station_name,
                        home_id=home_id,
                        home_name=home_name,
                        reachable=reachable,
                        modules=modules,
                        data_types=list(set(data_types)),  # Remove duplicates
                        last_seen=datetime.fromtimestamp(station.get("last_status_store", time.time())),
                    )
                    stations.append(weather_station)

            # Cache the results
            self._stations_cache[cache_key] = (stations, time.time())
            logger.info(f"Retrieved {len(stations)} weather stations")
            return stations

        except Exception as e:
            logger.error("Failed to get weather stations", error=str(e))
            raise NetatmoError(f"Failed to retrieve weather stations: {e!s}") from e

    async def get_station_data(self, station_id: str) -> WeatherData:
        """Get current weather data for a specific station."""
        try:
            # Check cache first
            cache_key = f"station_data_{station_id}"
            if cache_key in self._data_cache:
                cached_data, cache_time = self._data_cache[cache_key]
                if time.time() - cache_time < self._cache_ttl:
                    return cached_data

            logger.info(f"Fetching weather data for station {station_id}")
            stations = await self.get_stations()

            # Find the station
            station = None
            for s in stations:
                if s.id == station_id:
                    station = s
                    break

            if not station:
                raise DeviceNotFoundError(station_id, "station")

            if not station.reachable:
                raise DataUnavailableError(station_id, "station_offline")

            # Get detailed station data
            data = await self._make_request(
                "get_measure", station.id, ["Temperature", "Humidity", "Pressure", "CO2", "Noise"], timedelta(hours=1)
            )

            if not data or not data.get("body"):
                raise DataUnavailableError(station_id, "current_weather")

            # Convert to WeatherData
            weather_data = WeatherData.from_netatmo_data(data["body"][0])

            # Cache the results
            self._data_cache[cache_key] = (weather_data, time.time())

            return weather_data

        except DeviceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get weather data for station {station_id}", error=str(e))
            raise NetatmoError(f"Failed to retrieve weather data: {e!s}") from e

    async def get_historical_data(
        self, station_id: str, start_date: datetime, end_date: datetime, data_types: list[str] | None = None
    ) -> list[WeatherData]:
        """Get historical weather data for a station."""
        try:
            logger.info(
                f"Fetching historical data for station {station_id}",
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )

            # Default data types if not specified
            if data_types is None:
                data_types = ["Temperature", "Humidity", "Pressure", "CO2", "Noise"]

            # Get historical measurements
            data = await self._make_request("get_measure", station_id, data_types, start_date, end_date)

            if not data or not data.get("body"):
                return []

            weather_data_list = []
            for entry in data["body"]:
                weather_data = WeatherData.from_netatmo_data(entry)
                weather_data_list.append(weather_data)

            logger.info(f"Retrieved {len(weather_data_list)} historical data points")
            return weather_data_list

        except Exception as e:
            logger.error(f"Failed to get historical data for station {station_id}", error=str(e))
            raise NetatmoError(f"Failed to retrieve historical data: {e!s}") from e

    async def get_station_status(self, station_id: str) -> dict[str, Any]:
        """Get detailed status information for a station."""
        try:
            stations = await self.get_stations()

            for station in stations:
                if station.id == station_id:
                    return {
                        "station_id": station.id,
                        "station_name": station.name,
                        "reachable": station.reachable,
                        "last_seen": station.last_seen.isoformat() if station.last_seen else None,
                        "data_types": station.data_types,
                        "modules_count": len(station.modules),
                        "home_id": station.home_id,
                        "home_name": station.home_name,
                    }

            raise DeviceNotFoundError(station_id, "station")

        except DeviceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get status for station {station_id}", error=str(e))
            raise NetatmoError(f"Failed to retrieve station status: {e!s}") from e

    async def health_check(self) -> dict[str, Any]:
        """Perform a health check of the Netatmo connection."""
        try:
            # Try to get stations as a connectivity test
            stations = await self.get_stations()

            return {
                "status": "healthy",
                "stations_count": len(stations),
                "reachable_stations": sum(1 for s in stations if s.reachable),
                "timestamp": datetime.now().isoformat(),
            }

        except AuthenticationError:
            return {"status": "auth_failed", "error": "Authentication failed", "timestamp": datetime.now().isoformat()}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "timestamp": datetime.now().isoformat()}
