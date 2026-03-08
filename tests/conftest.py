"""
Pytest configuration and shared fixtures for Netatmo Weather MCP tests.
"""

import asyncio
import os
import pytest
from typing import Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock

from netatmo_weather_mcp.core.netatmo_client import NetatmoClient, WeatherStation, WeatherData
from netatmo_weather_mcp.core.exceptions import NetatmoError


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_weather_station() -> WeatherStation:
    """Sample weather station for testing."""
    return WeatherStation(
        id="70:ee:50:12:34:56",
        name="Test Station",
        home_id="home123",
        home_name="Test Home",
        reachable=True,
        modules=[
            {
                "id": "02:00:00:12:34:57",
                "name": "Outdoor Module",
                "type": "NAModule1",
                "reachable": True
            }
        ],
        data_types=["temperature", "humidity", "pressure"],
        last_seen=None
    )


@pytest.fixture
def sample_weather_data() -> WeatherData:
    """Sample weather data for testing."""
    from datetime import datetime
    return WeatherData(
        timestamp=datetime.now(),
        temperature=22.5,
        humidity=65,
        pressure=1013.2,
        co2=450,
        noise=35,
        rain=0.0,
        wind_strength=5.2,
        wind_angle=180,
        gust_strength=8.1,
        gust_angle=190
    )


@pytest.fixture
def mock_netatmo_client(sample_weather_station, sample_weather_data):
    """Mock Netatmo client for testing."""
    client = MagicMock(spec=NetatmoClient)

    # Mock async methods
    client.get_stations = AsyncMock(return_value=[sample_weather_station])
    client.get_station_data = AsyncMock(return_value=sample_weather_data)
    client.get_historical_data = AsyncMock(return_value=[sample_weather_data])
    client.get_station_status = AsyncMock(return_value={
        "station_id": sample_weather_station.id,
        "reachable": True,
        "data_types": sample_weather_station.data_types
    })
    client.health_check = AsyncMock(return_value={
        "status": "healthy",
        "stations_count": 1,
        "reachable_stations": 1
    })

    return client


@pytest.fixture
def test_credentials() -> Dict[str, str]:
    """Test Netatmo credentials."""
    return {
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "username": "test@example.com",
        "password": "test_password",
        "scope": "read_station"
    }


@pytest.fixture
def mock_env_vars(test_credentials):
    """Set up mock environment variables for testing."""
    original_env = dict(os.environ)

    # Set test environment variables
    os.environ.update({
        "NETATMO_CLIENT_ID": test_credentials["client_id"],
        "NETATMO_CLIENT_SECRET": test_credentials["client_secret"],
        "NETATMO_USERNAME": test_credentials["username"],
        "NETATMO_PASSWORD": test_credentials["password"],
        "NETATMO_SCOPE": test_credentials["scope"],
        "ENABLE_METRICS": "false",  # Disable metrics in tests
        "LOG_LEVEL": "WARNING"  # Reduce log noise in tests
    })

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_api_response() -> Dict[str, Any]:
    """Sample Netatmo API response for testing."""
    return {
        "homes": [
            {
                "id": "home123",
                "name": "Test Home",
                "stations": [
                    {
                        "id": "70:ee:50:12:34:56",
                        "name": "Test Station",
                        "reachable": True,
                        "dashboard_data": {
                            "Temperature": 22.5,
                            "Humidity": 65,
                            "Pressure": 1013.2,
                            "CO2": 450,
                            "Noise": 35
                        },
                        "last_status_store": 1640995200
                    }
                ],
                "modules": [
                    {
                        "id": "02:00:00:12:34:57",
                        "name": "Outdoor Module",
                        "type": "NAModule1",
                        "reachable": True
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_historical_data() -> list:
    """Sample historical weather data for testing."""
    from datetime import datetime, timedelta
    base_time = datetime.now()

    return [
        {
            "time_utc": int((base_time - timedelta(hours=i)).timestamp()),
            "dashboard_data": {
                "Temperature": 22.5 + (i * 0.1),  # Slight temperature variation
                "Humidity": 65 - (i * 0.5),      # Humidity decrease over time
                "Pressure": 1013.2 + (i * 0.2)   # Pressure increase
            }
        }
        for i in range(24)  # 24 hours of data
    ]


@pytest.fixture
def mock_httpx_client(sample_api_response):
    """Mock httpx client for API testing."""
    import httpx

    # Create a mock response
    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value=sample_api_response)
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    # Mock the httpx client
    with pytest.mock.patch('httpx.AsyncClient') as mock_client:
        mock_instance = AsyncMock()
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_client.return_value.__aexit__ = AsyncMock()

        yield mock_instance


@pytest.fixture(scope="session")
def anyio_backend():
    """Specify the async backend for anyio tests."""
    return "asyncio"


# Test configuration
@pytest.fixture(scope="session", autouse=True)
def configure_test_logging():
    """Configure logging for tests."""
    import logging
    logging.getLogger().setLevel(logging.WARNING)

    # Suppress noisy loggers during tests
    for logger_name in ['httpx', 'pyatmo', 'fastmcp']:
        logging.getLogger(logger_name).setLevel(logging.ERROR)


# Custom test markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "ai: Tests for AI functionality")
    config.addinivalue_line("markers", "sampling: Tests for sampling algorithms")
    config.addinivalue_line("markers", "external: Tests requiring external services")
    config.addinivalue_line("markers", "slow: Slow-running tests")


# Test utilities
class AsyncMockHelper:
    """Helper for creating async mocks."""

    @staticmethod
    def create_async_mock(return_value=None, side_effect=None):
        """Create an async mock function."""
        async def mock_coro(*args, **kwargs):
            if side_effect:
                if callable(side_effect):
                    return side_effect(*args, **kwargs)
                else:
                    raise side_effect
            return return_value

        return mock_coro


# Export helper
async_mock_helper = AsyncMockHelper()