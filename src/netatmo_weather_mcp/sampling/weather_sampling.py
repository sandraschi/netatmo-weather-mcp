"""
Weather sampling manager for AI workflows.

Provides iterative sampling, pattern analysis, and predictive sampling
capabilities for weather data with FastMCP 2.14.3 sampling method support.
"""

import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import structlog
from sklearn.linear_model import LinearRegression

from ..core.exceptions import SamplingError
from ..core.netatmo_client import NetatmoClient, WeatherData

logger = structlog.get_logger(__name__)


@dataclass
class SamplingIteration:
    """Result of a single sampling iteration."""

    iteration: int
    timestamp: datetime
    data: dict[str, Any]
    quality_score: float
    refinement_applied: str


@dataclass
class SamplingResult:
    """Complete sampling workflow result."""

    mode: str
    station_id: str
    iterations: list[SamplingIteration]
    final_quality_score: float
    pattern_detected: str | None = None
    predictive_accuracy: float | None = None


class WeatherSamplingManager:
    """Manages AI-powered weather data sampling for iterative workflows."""

    def __init__(self):
        self._sampling_history: dict[str, list[SamplingResult]] = {}
        self._pattern_cache: dict[str, dict[str, Any]] = {}

    async def perform_iterative_sampling(
        self, client: NetatmoClient, station_id: str, iterations: int, refinement_prompt: str
    ) -> SamplingResult:
        """
        Perform iterative sampling with AI-guided refinement.

        Args:
            client: Netatmo client instance
            station_id: Weather station ID
            iterations: Number of sampling iterations
            refinement_prompt: AI refinement instructions

        Returns:
            SamplingResult with iterative sampling data
        """
        try:
            iterations_data = []

            # Get baseline data
            baseline_data = await client.get_station_data(station_id)

            for i in range(iterations):
                iteration_data = await self._single_sampling_iteration(
                    client, station_id, baseline_data, i + 1, refinement_prompt
                )
                iterations_data.append(iteration_data)

                # Adaptive refinement based on previous results
                if i > 0:
                    refinement_prompt = await self._adapt_refinement_prompt(
                        refinement_prompt, iterations_data[-2], iteration_data
                    )

            # Calculate final quality score
            quality_scores = [it.quality_score for it in iterations_data]
            final_quality = statistics.mean(quality_scores) if quality_scores else 0.0

            result = SamplingResult(
                mode="iterative", station_id=station_id, iterations=iterations_data, final_quality_score=final_quality
            )

            # Store in history
            if station_id not in self._sampling_history:
                self._sampling_history[station_id] = []
            self._sampling_history[station_id].append(result)

            return result

        except Exception as e:
            logger.error("Iterative sampling failed", station_id=station_id, iterations=iterations, error=str(e))
            raise SamplingError(f"Iterative sampling failed: {e!s}") from e

    async def perform_predictive_sampling(
        self, client: NetatmoClient, station_id: str, iterations: int, forecast_hours: int = 24
    ) -> SamplingResult:
        """
        Perform predictive sampling for weather forecasting.

        Args:
            client: Netatmo client instance
            station_id: Weather station ID
            iterations: Number of sampling iterations
            forecast_hours: Hours to forecast

        Returns:
            SamplingResult with predictive sampling data
        """
        try:
            # Get historical data for training
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)  # Use 7 days of history

            historical_data = await client.get_historical_data(station_id, start_date, end_date)

            if len(historical_data) < 24:  # Need at least 24 hours of data
                raise SamplingError("Insufficient historical data for predictive sampling")

            iterations_data = []

            for i in range(iterations):
                iteration_data = await self._predictive_iteration(historical_data, i + 1, forecast_hours)
                iterations_data.append(iteration_data)

            # Calculate predictive accuracy
            accuracies = [it.quality_score for it in iterations_data if it.quality_score > 0]
            predictive_accuracy = statistics.mean(accuracies) if accuracies else 0.0

            result = SamplingResult(
                mode="predictive",
                station_id=station_id,
                iterations=iterations_data,
                final_quality_score=predictive_accuracy,
                predictive_accuracy=predictive_accuracy,
            )

            return result

        except Exception as e:
            logger.error("Predictive sampling failed", station_id=station_id, error=str(e))
            raise SamplingError(f"Predictive sampling failed: {e!s}") from e

    async def perform_anomaly_detection_sampling(
        self, client: NetatmoClient, station_id: str, iterations: int
    ) -> SamplingResult:
        """
        Perform anomaly detection sampling to identify unusual weather patterns.

        Args:
            client: Netatmo client instance
            station_id: Weather station ID
            iterations: Number of sampling iterations

        Returns:
            SamplingResult with anomaly detection results
        """
        try:
            # Get recent data for anomaly detection
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)  # Use 30 days for baseline

            historical_data = await client.get_historical_data(station_id, start_date, end_date)

            if len(historical_data) < 168:  # Need at least a week of data
                raise SamplingError("Insufficient data for anomaly detection")

            iterations_data = []

            for i in range(iterations):
                iteration_data = await self._anomaly_detection_iteration(historical_data, i + 1)
                iterations_data.append(iteration_data)

            # Detect overall pattern
            anomaly_scores = [it.quality_score for it in iterations_data]
            pattern_detected = self._analyze_anomaly_pattern(anomaly_scores)

            result = SamplingResult(
                mode="anomaly_detection",
                station_id=station_id,
                iterations=iterations_data,
                final_quality_score=statistics.mean(anomaly_scores) if anomaly_scores else 0.0,
                pattern_detected=pattern_detected,
            )

            return result

        except Exception as e:
            logger.error("Anomaly detection sampling failed", station_id=station_id, error=str(e))
            raise SamplingError(f"Anomaly detection sampling failed: {e!s}") from e

    async def _single_sampling_iteration(
        self, client: NetatmoClient, station_id: str, baseline_data: WeatherData, iteration: int, refinement_prompt: str
    ) -> SamplingIteration:
        """Perform a single sampling iteration."""
        # Simulate AI-guided refinement based on prompt
        refinement_type = "temperature_focus" if "temperature" in refinement_prompt.lower() else "general"

        # Generate refined sample
        sample_data = self._generate_refined_sample(baseline_data, refinement_type, iteration)

        # Calculate quality score based on data completeness and variation
        quality_score = self._calculate_sample_quality(sample_data)

        return SamplingIteration(
            iteration=iteration,
            timestamp=datetime.now(),
            data=sample_data,
            quality_score=quality_score,
            refinement_applied=refinement_type,
        )

    async def _predictive_iteration(
        self, historical_data: list[WeatherData], iteration: int, forecast_hours: int
    ) -> SamplingIteration:
        """Perform a single predictive sampling iteration."""
        try:
            # Simple linear regression for temperature prediction
            df = pd.DataFrame(
                [
                    {
                        "timestamp": (d.timestamp - historical_data[0].timestamp).total_seconds() / 3600,
                        "temperature": d.temperature,
                        "humidity": d.humidity,
                        "pressure": d.pressure,
                    }
                    for d in historical_data
                    if d.temperature is not None
                ]
            )

            if len(df) < 10:
                return SamplingIteration(
                    iteration=iteration,
                    timestamp=datetime.now(),
                    data={"error": "insufficient_data"},
                    quality_score=0.0,
                    refinement_applied="insufficient_data",
                )

            # Fit linear model for temperature
            X = df[["timestamp"]].values
            y = df["temperature"].values

            model = LinearRegression()
            model.fit(X, y)

            # Generate predictions
            future_times = np.array([[len(df) + i] for i in range(forecast_hours)])
            predictions = model.predict(future_times)

            # Calculate prediction confidence (simplified)
            confidence = min(0.95, max(0.1, 1.0 - (np.std(y) / np.mean(np.abs(y)))))

            prediction_data = {
                "forecast_hours": forecast_hours,
                "predictions": [
                    {"hour": i + 1, "temperature": float(pred), "confidence": confidence}
                    for i, pred in enumerate(predictions[:forecast_hours])
                ],
                "model_accuracy": confidence,
                "trend": "increasing" if predictions[-1] > predictions[0] else "decreasing",
            }

            return SamplingIteration(
                iteration=iteration,
                timestamp=datetime.now(),
                data=prediction_data,
                quality_score=confidence,
                refinement_applied="linear_regression",
            )

        except Exception as e:
            logger.warning(f"Predictive iteration {iteration} failed", error=str(e))
            return SamplingIteration(
                iteration=iteration,
                timestamp=datetime.now(),
                data={"error": str(e)},
                quality_score=0.0,
                refinement_applied="error_recovery",
            )

    async def _anomaly_detection_iteration(
        self, historical_data: list[WeatherData], iteration: int
    ) -> SamplingIteration:
        """Perform a single anomaly detection iteration."""
        try:
            # Extract temperature data
            temperatures = [d.temperature for d in historical_data if d.temperature is not None]

            if len(temperatures) < 50:
                return SamplingIteration(
                    iteration=iteration,
                    timestamp=datetime.now(),
                    data={"error": "insufficient_data"},
                    quality_score=0.0,
                    refinement_applied="insufficient_data",
                )

            # Calculate rolling statistics
            temp_series = pd.Series(temperatures)
            rolling_mean = temp_series.rolling(window=24).mean()
            rolling_std = temp_series.rolling(window=24).std()

            # Detect anomalies (values > 2 standard deviations from rolling mean)
            anomalies = []
            for i, (temp, mean, std) in enumerate(zip(temperatures, rolling_mean, rolling_std, strict=False)):
                if mean is not None and std is not None and std > 0:
                    z_score = abs(temp - mean) / std
                    if z_score > 2.0:
                        anomalies.append(
                            {
                                "index": i,
                                "temperature": temp,
                                "expected_range": [mean - 2 * std, mean + 2 * std],
                                "z_score": z_score,
                                "severity": "high" if z_score > 3.0 else "moderate",
                            }
                        )

            anomaly_data = {
                "total_points": len(temperatures),
                "anomalies_detected": len(anomalies),
                "anomaly_rate": len(anomalies) / len(temperatures),
                "anomalies": anomalies[:10],  # Limit to top 10
                "temperature_stats": {
                    "mean": statistics.mean(temperatures),
                    "std": statistics.stdev(temperatures),
                    "min": min(temperatures),
                    "max": max(temperatures),
                },
            }

            # Quality score based on anomaly detection confidence
            quality_score = min(1.0, len(anomalies) / max(1, len(temperatures) * 0.1))

            return SamplingIteration(
                iteration=iteration,
                timestamp=datetime.now(),
                data=anomaly_data,
                quality_score=quality_score,
                refinement_applied="statistical_anomaly_detection",
            )

        except Exception as e:
            logger.warning(f"Anomaly detection iteration {iteration} failed", error=str(e))
            return SamplingIteration(
                iteration=iteration,
                timestamp=datetime.now(),
                data={"error": str(e)},
                quality_score=0.0,
                refinement_applied="error_recovery",
            )

    def _generate_refined_sample(self, baseline: WeatherData, refinement_type: str, iteration: int) -> dict[str, Any]:
        """Generate a refined sample based on the refinement type."""
        # Add some controlled variation
        variation_factor = (iteration - 3) * 0.1  # Center around iteration 3

        sample = {
            "temperature": baseline.temperature,
            "humidity": baseline.humidity,
            "pressure": baseline.pressure,
            "co2": baseline.co2,
            "noise": baseline.noise,
            "sample_iteration": iteration,
            "refinement_type": refinement_type,
        }

        if refinement_type == "temperature_focus":
            if sample["temperature"] is not None:
                sample["temperature"] += variation_factor * 2
        elif refinement_type == "humidity_focus":
            if sample["humidity"] is not None:
                sample["humidity"] = min(100, max(0, sample["humidity"] + variation_factor * 5))
        # Add more refinement types as needed

        return sample

    def _calculate_sample_quality(self, sample_data: dict[str, Any]) -> float:
        """Calculate quality score for a sample."""
        completeness = sum(1 for v in sample_data.values() if v is not None) / len(sample_data)
        variation = abs(hash(str(sample_data)) % 100) / 100.0  # Simple variation proxy
        return (completeness + variation) / 2.0

    async def _adapt_refinement_prompt(
        self, current_prompt: str, previous_iteration: SamplingIteration, current_iteration: SamplingIteration
    ) -> str:
        """Adapt refinement prompt based on iteration results."""
        prev_quality = previous_iteration.quality_score
        curr_quality = current_iteration.quality_score

        if curr_quality > prev_quality:
            return current_prompt + " (improving, continue refinement)"
        elif curr_quality < prev_quality:
            return current_prompt + " (quality decreased, try different approach)"
        else:
            return current_prompt + " (stable, explore new variations)"

    def _analyze_anomaly_pattern(self, anomaly_scores: list[float]) -> str:
        """Analyze anomaly pattern from scores."""
        if not anomaly_scores:
            return "no_pattern"

        avg_score = statistics.mean(anomaly_scores)
        if avg_score > 0.7:
            return "high_anomaly_rate"
        elif avg_score > 0.3:
            return "moderate_anomaly_rate"
        else:
            return "low_anomaly_rate"
