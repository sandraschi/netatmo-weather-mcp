"""
Custom exceptions for Netatmo Weather MCP.

Provides comprehensive error handling with context for Netatmo API operations,
authentication issues, and data processing errors.
"""


class NetatmoError(Exception):
    """Base exception for all Netatmo-related errors."""

    def __init__(self, message: str, error_code: str = None, context: dict = None):
        super().__init__(message)
        self.error_code = error_code or "NETATMO_ERROR"
        self.context = context or {}


class AuthenticationError(NetatmoError):
    """Raised when authentication with Netatmo API fails."""

    def __init__(self, message: str = "Netatmo authentication failed", context: dict = None):
        super().__init__(message, "AUTH_ERROR", context)


class TokenExpiredError(AuthenticationError):
    """Raised when the Netatmo access token has expired."""

    def __init__(self, message: str = "Netatmo access token expired", context: dict = None):
        super().__init__(message, "TOKEN_EXPIRED", context)


class DeviceNotFoundError(NetatmoError):
    """Raised when a requested weather station or module is not found."""

    def __init__(self, device_id: str, device_type: str = "station", context: dict = None):
        message = f"Netatmo {device_type} '{device_id}' not found"
        super().__init__(message, "DEVICE_NOT_FOUND", context)
        self.device_id = device_id
        self.device_type = device_type


class DataUnavailableError(NetatmoError):
    """Raised when weather data is temporarily unavailable."""

    def __init__(self, station_id: str, data_type: str = "weather_data", context: dict = None):
        message = f"Weather data type '{data_type}' unavailable for station '{station_id}'"
        super().__init__(message, "DATA_UNAVAILABLE", context)
        self.station_id = station_id
        self.data_type = data_type


class RateLimitError(NetatmoError):
    """Raised when API rate limits are exceeded."""

    def __init__(self, retry_after: int = None, context: dict = None):
        message = "Netatmo API rate limit exceeded"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message, "RATE_LIMIT", context)
        self.retry_after = retry_after


class NetworkError(NetatmoError):
    """Raised when network connectivity issues occur."""

    def __init__(self, message: str = "Network connectivity error", context: dict = None):
        super().__init__(message, "NETWORK_ERROR", context)


class ConfigurationError(NetatmoError):
    """Raised when configuration issues are detected."""

    def __init__(self, message: str, config_key: str = None, context: dict = None):
        super().__init__(message, "CONFIG_ERROR", context)
        self.config_key = config_key


class SamplingError(NetatmoError):
    """Raised when AI sampling operations fail."""

    def __init__(self, message: str, sampling_mode: str = None, context: dict = None):
        super().__init__(message, "SAMPLING_ERROR", context)
        self.sampling_mode = sampling_mode


class PredictionError(NetatmoError):
    """Raised when weather prediction operations fail."""

    def __init__(self, message: str, prediction_type: str = None, context: dict = None):
        super().__init__(message, "PREDICTION_ERROR", context)
        self.prediction_type = prediction_type