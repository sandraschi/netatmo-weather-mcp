"""
Unit tests for Netatmo API client.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from netatmo_weather_mcp.core.netatmo_client import NetatmoClient, WeatherStation, WeatherData
from netatmo_weather_mcp.core.exceptions import (
    AuthenticationError, DeviceNotFoundError, DataUnavailableError
)


class TestNetatmoClient:
    """Test Netatmo client functionality."""

    @pytest.mark.asyncio
    async def test_get_stations_success(self, mock_env_vars, sample_api_response):
        """Test successful station retrieval."""
        with patch('pyatmo.NetatmoOAuth2') as mock_oauth:
            mock_client = MagicMock()
            mock_oauth.return_value = mock_client
            mock_client.get_stations_data = MagicMock(return_value=sample_api_response)

            client = NetatmoClient()
            stations = await client.get_stations()

            assert len(stations) == 1
            station = stations[0]
            assert station.id == "70:ee:50:12:34:56"
            assert station.name == "Test Station"
            assert station.reachable is True
            assert len(station.modules) == 1

    @pytest.mark.asyncio
    async def test_get_stations_authentication_error(self, mock_env_vars):
        """Test authentication error handling."""
        with patch('pyatmo.NetatmoOAuth2') as mock_oauth:
            mock_oauth.side_effect = Exception("Invalid credentials")

            client = NetatmoClient()

            with pytest.raises(AuthenticationError):
                await client.get_stations()

    @pytest.mark.asyncio
    async def test_get_station_data_success(self, mock_env_vars, sample_weather_station):
        """Test successful weather data retrieval."""
        with patch('pyatmo.NetatmoOAuth2') as mock_oauth, \
             patch.object(NetatmoClient, 'get_stations', new_callable=AsyncMock) as mock_get_stations:

            mock_get_stations.return_value = [sample_weather_station]

            mock_client = MagicMock()
            mock_oauth.return_value = mock_client
            mock_client.get_measure = MagicMock(return_value={
                'body': [{
                    'time_utc': int(datetime.now().timestamp()),
                    'dashboard_data': {
                        'Temperature': 22.5,
                        'Humidity': 65,
                        'Pressure': 1013.2
                    }
                }]
            })

            client = NetatmoClient()
            data = await client.get_station_data("70:ee:50:12:34:56")

            assert data.temperature == 22.5
            assert data.humidity == 65
            assert data.pressure == 1013.2

    @pytest.mark.asyncio
    async def test_get_station_data_not_found(self, mock_env_vars):
        """Test station not found error."""
        with patch('pyatmo.NetatmoOAuth2') as mock_oauth, \
             patch.object(NetatmoClient, 'get_stations', new_callable=AsyncMock) as mock_get_stations:

            mock_get_stations.return_value = []  # No stations found
            mock_oauth.return_value = MagicMock()

            client = NetatmoClient()

            with pytest.raises(DeviceNotFoundError):
                await client.get_station_data("nonexistent")

    @pytest.mark.asyncio
    async def test_get_historical_data_success(self, mock_env_vars, sample_historical_data):
        """Test successful historical data retrieval."""
        with patch('pyatmo.NetatmoOAuth2') as mock_oauth:
            mock_client = MagicMock()
            mock_oauth.return_value = mock_client
            mock_client.get_measure = MagicMock(return_value={'body': sample_historical_data})

            client = NetatmoClient()
            start_date = datetime.now() - timedelta(hours=24)
            end_date = datetime.now()

            data = await client.get_historical_data("station_id", start_date, end_date)

            assert len(data) == 24
            assert all(isinstance(d, WeatherData) for d in data)
            assert all(d.temperature is not None for d in data)

    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_env_vars):
        """Test successful health check."""
        with patch.object(NetatmoClient, 'get_stations', new_callable=AsyncMock) as mock_get_stations:
            mock_get_stations.return_value = [MagicMock(reachable=True)]

            client = NetatmoClient()
            health = await client.health_check()

            assert health["status"] == "healthy"
            assert health["stations_count"] == 1
            assert health["reachable_stations"] == 1

    @pytest.mark.asyncio
    async def test_health_check_failure(self, mock_env_vars):
        """Test health check failure."""
        with patch.object(NetatmoClient, 'get_stations', new_callable=AsyncMock) as mock_get_stations:
            mock_get_stations.side_effect = AuthenticationError("Auth failed")

            client = NetatmoClient()
            health = await client.health_check()

            assert health["status"] == "auth_failed"
            assert "Auth failed" in health["error"]

    @pytest.mark.asyncio
    async def test_rate_limiting(self, mock_env_vars):
        """Test rate limiting functionality."""
        with patch('pyatmo.NetatmoOAuth2') as mock_oauth, \
             patch('asyncio.sleep') as mock_sleep:

            mock_client = MagicMock()
            mock_oauth.return_value = mock_client
            mock_client.get_stations_data = MagicMock(return_value={"homes": []})

            client = NetatmoClient()

            # Make multiple rapid requests
            await client.get_stations()
            await client.get_stations()

            # Verify sleep was called for rate limiting
            mock_sleep.assert_called()

    def test_credentials_from_env(self, mock_env_vars, test_credentials):
        """Test loading credentials from environment."""
        client = NetatmoClient()

        # Check that credentials were loaded correctly
        assert client.credentials.client_id == test_credentials["client_id"]
        assert client.credentials.client_secret == test_credentials["client_secret"]
        assert client.credentials.username == test_credentials["username"]
        assert client.credentials.password == test_credentials["password"]

    def test_missing_credentials_error(self):
        """Test error when required credentials are missing."""
        # Clear environment
        original_env = dict(os.environ)
        required_vars = ['NETATMO_CLIENT_ID', 'NETATMO_CLIENT_SECRET',
                        'NETATMO_USERNAME', 'NETATMO_PASSWORD']

        for var in required_vars:
            os.environ.pop(var, None)

        try:
            with pytest.raises(Exception):  # ConfigurationError
                NetatmoClient()
        finally:
            # Restore environment
            os.environ.update(original_env)