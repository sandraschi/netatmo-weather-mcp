"""
FastMCP 3.1 server for Netatmo Weather MCP.

This module provides a FastMCP server implementation for Netatmo weather stations
with composition and sampling capabilities using FastMCP 3.1 patterns.

Features:
- Conversational tool returns for rich AI dialogue
- Sampling methods for AI workflow refinement
- Portmanteau tool patterns for consolidated functionality
- Prometheus metrics and structured logging
- Comprehensive error handling with context
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastmcp import FastMCP
from prometheus_client import Counter, Gauge, Histogram, start_http_server
from pydantic import BaseModel, Field

from .sampling.weather_sampling import WeatherSamplingManager
from .tools.ai_sampling import AISamplingTools
from .tools.predictive_analytics import PredictiveAnalyticsTools
from .tools.weather_monitoring import WeatherMonitoringTools
from .transport import run_server

_READ_ONLY = {"readonly": True}

# Configure structured logging
logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter("netatmo_requests_total", "Total number of Netatmo API requests", ["method", "endpoint"])
REQUEST_LATENCY = Histogram("netatmo_request_duration_seconds", "Request latency in seconds", ["method", "endpoint"])
ACTIVE_CONNECTIONS = Gauge("netatmo_active_connections", "Number of active Netatmo connections")
WEATHER_SAMPLES = Counter(
    "netatmo_weather_samples_total", "Total number of weather samples processed", ["station_id", "data_type"]
)


class WeatherStationInfo(BaseModel):
    """Information about a Netatmo weather station."""

    station_id: str = Field(..., description="Unique identifier for the weather station")
    station_name: str = Field(..., description="Human-readable name of the station")
    home_id: str = Field(..., description="Home identifier the station belongs to")
    home_name: str = Field(..., description="Name of the home")
    modules: list[dict[str, Any]] = Field(default_factory=list, description="Connected modules")
    reachable: bool = Field(True, description="Whether the station is currently reachable")


class WeatherData(BaseModel):
    """Weather measurement data from Netatmo station."""

    timestamp: int = Field(..., description="Unix timestamp of the measurement")
    temperature: float | None = Field(None, description="Temperature in Celsius")
    humidity: int | None = Field(None, description="Humidity percentage")
    pressure: float | None = Field(None, description="Atmospheric pressure in mbar")
    co2: int | None = Field(None, description="CO2 level in ppm")
    noise: int | None = Field(None, description="Noise level in dB")
    rain: float | None = Field(None, description="Rainfall in mm")
    wind_strength: float | None = Field(None, description="Wind strength in kph")
    wind_angle: int | None = Field(None, description="Wind direction in degrees")
    gust_strength: float | None = Field(None, description="Wind gust strength in kph")
    gust_angle: int | None = Field(None, description="Wind gust direction in degrees")


@asynccontextmanager
async def lifespan(server: FastMCP):
    """Manage server lifespan with proper resource initialization and cleanup."""
    # Startup
    logger.info("Starting Netatmo Weather MCP Server")

    # Start Prometheus metrics server if configured
    metrics_port = os.getenv("METRICS_PORT", "9091")
    if os.getenv("ENABLE_METRICS", "true").lower() == "true":
        try:
            start_http_server(int(metrics_port))
            logger.info(f"Prometheus metrics server started on port {metrics_port}")
        except Exception as e:
            logger.warning(f"Failed to start metrics server: {e}")

    # Initialize sampling manager
    sampling_manager = WeatherSamplingManager()

    # Store in server state for access by tools
    server.state.sampling_manager = sampling_manager
    server.state.netatmo_client = None  # Will be initialized on first use

    ACTIVE_CONNECTIONS.set(1)
    logger.info("Netatmo Weather MCP Server startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Netatmo Weather MCP Server")
    ACTIVE_CONNECTIONS.set(0)


def create_server() -> FastMCP:
    """Create and configure the FastMCP server instance."""

    server = FastMCP(name="netatmo-weather-mcp", version="1.0.0", lifespan=lifespan)

    # Initialize tool managers
    weather_tools = WeatherMonitoringTools()
    ai_sampling_tools = AISamplingTools()
    predictive_tools = PredictiveAnalyticsTools()

    # Register portmanteau weather monitoring tools
    @server.tool(annotations=_READ_ONLY)
    async def weather_station_management(
        ctx,
        operation: str = Field(..., description="Operation to perform: 'list', 'get_info', 'get_status'"),
        station_id: str | None = Field(None, description="Station ID for specific operations"),
    ) -> dict[str, Any]:
        """
        PORTMANTEAU PATTERN RATIONALE:
        Consolidates station discovery, status monitoring, and configuration into single interface.
        Prevents tool explosion while maintaining full weather station management capabilities.
        Follows FastMCP 2.14.3 best practices for conversational AI workflows.

        Comprehensive weather station management with conversational returns.

        Args:
            operation: Operation to perform ('list', 'get_info', 'get_status')
            station_id: Station ID for specific operations

        Returns:
            Dict containing operation results with conversational context and next action suggestions
        """
        try:
            async with REQUEST_LATENCY.time():
                REQUEST_COUNT.labels(method="tool", endpoint="weather_station_management").inc()

                result = await weather_tools.manage_stations(operation, station_id)

                # Add conversational context
                if operation == "list":
                    result["conversation_context"] = {
                        "message": f"Found {len(result.get('stations', []))} weather stations. "
                        f"Use 'get_info' with a station_id to explore specific stations.",
                        "suggested_actions": ["get_info", "get_status"],
                        "data_quality": "high" if result.get("stations") else "none",
                    }
                elif operation == "get_info":
                    modules = result.get("station", {}).get("modules", [])
                    result["conversation_context"] = {
                        "message": f"Station '{result.get('station', {}).get('station_name', 'Unknown')}' "
                        f"has {len(modules)} connected modules. Ready for weather monitoring.",
                        "suggested_actions": ["get_status", "sample_weather_data"],
                        "data_quality": "high",
                    }
                elif operation == "get_status":
                    reachable = result.get("status", {}).get("reachable", False)
                    status_msg = "online and collecting data" if reachable else "currently unreachable"
                    result["conversation_context"] = {
                        "message": f"Weather station is {status_msg}. "
                        f"{'Data collection active.' if reachable else 'Check network connectivity.'}",
                        "suggested_actions": ["sample_weather_data"] if reachable else ["get_status"],
                        "data_quality": "high" if reachable else "offline",
                    }

                return result

        except Exception as e:
            logger.error("Weather station management failed", operation=operation, station_id=station_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "conversation_context": {
                    "message": f"Operation '{operation}' failed. Please check your Netatmo connection and try again.",
                    "suggested_actions": ["get_status"],
                    "error_type": type(e).__name__,
                },
            }

    @server.tool(annotations=_READ_ONLY)
    async def weather_data_operations(
        ctx,
        operation: str = Field(..., description="Operation: 'current', 'historical', 'sample', 'analyze'"),
        station_id: str = Field(..., description="Weather station ID"),
        timeframe: str | None = Field("1h", description="Timeframe for historical data (e.g., '1h', '24h', '7d')"),
        data_types: list[str] | None = Field(None, description="Specific data types to retrieve"),
    ) -> dict[str, Any]:
        """
        PORTMANTEAU PATTERN RATIONALE:
        Consolidates current weather retrieval, historical data access, and sampling operations.
        Prevents tool explosion while enabling comprehensive weather data workflows.
        Optimized for AI sampling and predictive analytics patterns.

        Advanced weather data operations with AI sampling support.

        Args:
            operation: Operation type ('current', 'historical', 'sample', 'analyze')
            station_id: Weather station identifier
            timeframe: Timeframe for historical operations
            data_types: Specific data types to focus on

        Returns:
            Dict with weather data and AI workflow suggestions
        """
        try:
            async with REQUEST_LATENCY.time():
                REQUEST_COUNT.labels(method="tool", endpoint="weather_data_operations").inc()

                result = await weather_tools.process_weather_data(operation, station_id, timeframe, data_types)

                # Add AI workflow context
                if operation == "current":
                    data_points = len(result.get("data", {}))
                    result["ai_workflow_context"] = {
                        "message": f"Retrieved {data_points} current weather measurements. "
                        f"Ready for analysis or sampling workflows.",
                        "suggested_operations": ["analyze", "sample"],
                        "sampling_ready": data_points > 0,
                        "predictive_potential": "high" if data_points >= 3 else "low",
                    }
                elif operation == "historical":
                    records = len(result.get("historical_data", []))
                    result["ai_workflow_context"] = {
                        "message": f"Retrieved {records} historical records over {timeframe}. "
                        f"Excellent for pattern analysis and predictions.",
                        "suggested_operations": ["analyze", "predict_patterns"],
                        "analysis_ready": records > 10,
                        "trend_analysis": "available" if records > 24 else "insufficient_data",
                    }
                elif operation == "sample":
                    samples = len(result.get("samples", []))
                    result["ai_workflow_context"] = {
                        "message": f"Generated {samples} weather data samples. "
                        f"Ready for AI model training or pattern recognition.",
                        "suggested_operations": ["analyze_samples", "predict_trends"],
                        "model_training_ready": samples > 50,
                        "pattern_recognition": "enabled",
                    }

                # Track weather samples for metrics
                if operation == "sample":
                    WEATHER_SAMPLES.labels(station_id=station_id, data_type="sampled").inc(
                        len(result.get("samples", []))
                    )

                return result

        except Exception as e:
            logger.error("Weather data operation failed", operation=operation, station_id=station_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "ai_workflow_context": {
                    "message": f"Weather data {operation} failed. Check station connectivity.",
                    "suggested_operations": ["get_status"],
                    "error_recovery": "retry_with_different_station",
                },
            }

    @server.tool(annotations=_READ_ONLY)
    async def ai_weather_sampling(
        ctx,
        sampling_mode: str = Field(..., description="Sampling mode: 'iterative', 'predictive', 'anomaly'"),
        station_id: str = Field(..., description="Weather station ID"),
        iterations: int = Field(5, description="Number of sampling iterations"),
        refinement_prompt: str = Field("", description="AI refinement instructions"),
    ) -> dict[str, Any]:
        """
        PORTMANTEAU PATTERN RATIONALE:
        Consolidates AI-driven weather sampling, iterative refinement, and predictive workflows.
        Enables true AI-weather station interaction with sampling-based learning.
        Implements FastMCP 2.14.3 sampling method support for creative AI applications.

        AI-powered weather sampling with iterative refinement and predictive analytics.

        Args:
            sampling_mode: Type of sampling ('iterative', 'predictive', 'anomaly')
            station_id: Weather station identifier
            iterations: Number of sampling iterations for refinement
            refinement_prompt: AI instructions for sampling refinement

        Returns:
            Dict with sampling results and AI workflow continuation suggestions
        """
        try:
            async with REQUEST_LATENCY.time():
                REQUEST_COUNT.labels(method="tool", endpoint="ai_weather_sampling").inc()

                result = await ai_sampling_tools.perform_sampling(
                    sampling_mode, station_id, iterations, refinement_prompt
                )

                # Add advanced AI workflow context
                completed_iterations = len(result.get("iterations", []))
                result["ai_advanced_context"] = {
                    "message": f"Completed {completed_iterations}/{iterations} AI sampling iterations. "
                    f"Sampling mode: {sampling_mode}",
                    "workflow_status": "completed" if completed_iterations >= iterations else "in_progress",
                    "suggested_next": ["predict_patterns", "analyze_anomalies", "generate_insights"],
                    "model_readiness": "high" if completed_iterations > 3 else "developing",
                    "sampling_quality": result.get("quality_score", 0),
                    "predictive_accuracy": result.get("accuracy_score", 0),
                }

                return result

        except Exception as e:
            logger.error("AI weather sampling failed", sampling_mode=sampling_mode, station_id=station_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "ai_advanced_context": {
                    "message": f"AI sampling failed for mode '{sampling_mode}'. "
                    f"Try different parameters or check data availability.",
                    "recovery_suggestions": ["reduce_iterations", "simplify_mode", "check_data_quality"],
                    "error_type": type(e).__name__,
                },
            }

    @server.tool(annotations=_READ_ONLY)
    async def weather_prediction_engine(
        ctx,
        prediction_type: str = Field(..., description="Type: 'short_term', 'trend_analysis', 'anomaly_detection'"),
        station_id: str = Field(..., description="Weather station ID"),
        forecast_hours: int = Field(24, description="Hours to forecast"),
        confidence_threshold: float = Field(0.8, description="Prediction confidence threshold"),
    ) -> dict[str, Any]:
        """
        PORTMANTEAU PATTERN RATIONALE:
        Consolidates weather prediction, trend analysis, and anomaly detection.
        Provides comprehensive predictive analytics for weather patterns and automation.
        Enables AI-driven weather forecasting with confidence scoring.

        Advanced weather prediction engine with trend analysis and anomaly detection.

        Args:
            prediction_type: Type of prediction to generate
            station_id: Weather station identifier
            forecast_hours: Hours to forecast ahead
            confidence_threshold: Minimum confidence for predictions

        Returns:
            Dict with predictions, confidence scores, and automation suggestions
        """
        try:
            async with REQUEST_LATENCY.time():
                REQUEST_COUNT.labels(method="tool", endpoint="weather_prediction_engine").inc()

                result = await predictive_tools.generate_predictions(
                    prediction_type, station_id, forecast_hours, confidence_threshold
                )

                # Add predictive AI context
                predictions = len(result.get("predictions", []))
                avg_confidence = result.get("average_confidence", 0)

                result["predictive_context"] = {
                    "message": f"Generated {predictions} predictions with {avg_confidence:.1%} average confidence. "
                    f"Forecast type: {prediction_type}",
                    "automation_opportunities": result.get("automation_suggestions", []),
                    "alert_recommendations": result.get("alert_conditions", []),
                    "model_performance": (
                        "excellent" if avg_confidence > 0.9 else "good" if avg_confidence > 0.7 else "developing"
                    ),
                    "next_best_action": (
                        "deploy_automation" if avg_confidence > confidence_threshold else "gather_more_data"
                    ),
                }

                return result

        except Exception as e:
            logger.error(
                "Weather prediction failed", prediction_type=prediction_type, station_id=station_id, error=str(e)
            )
            return {
                "success": False,
                "error": str(e),
                "predictive_context": {
                    "message": f"Prediction generation failed for type '{prediction_type}'. "
                    f"Insufficient historical data or model training required.",
                    "recovery_actions": ["collect_more_data", "reduce_forecast_hours", "simplify_prediction_type"],
                    "error_type": type(e).__name__,
                },
            }

    return server


def main():
    """Main entry point for the Netatmo Weather MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="Netatmo Weather MCP Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=3000, help="Port to bind to")
    parser.add_argument("--log-level", default="INFO", help="Logging level")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    server = create_server()

    # Run the server using FastMCP 3.1 stdio mode
    asyncio.run(run_server(server, server_name="netatmo-weather-mcp"))


if __name__ == "__main__":
    main()
