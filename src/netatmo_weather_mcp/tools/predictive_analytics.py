"""
Predictive analytics tools for weather forecasting and automation.

Provides advanced weather prediction capabilities with AI-driven insights,
trend analysis, and automated decision-making suggestions.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import statistics

import structlog

from ..core.netatmo_client import NetatmoClient
from ..sampling.weather_sampling import WeatherSamplingManager

logger = structlog.get_logger(__name__)


class PredictiveAnalyticsTools:
    """AI-powered predictive analytics for weather patterns and automation."""

    def __init__(self):
        self._sampling_manager = WeatherSamplingManager()
        self._client: Optional[NetatmoClient] = None

    async def _get_client(self) -> NetatmoClient:
        """Lazy initialization of Netatmo client."""
        if self._client is None:
            self._client = NetatmoClient()
        return self._client

    async def generate_predictions(
        self,
        prediction_type: str,
        station_id: str,
        forecast_hours: int,
        confidence_threshold: float
    ) -> Dict[str, Any]:
        """
        Generate weather predictions using AI and statistical methods.

        Args:
            prediction_type: Type of prediction ('short_term', 'trend_analysis', 'anomaly_detection')
            station_id: Weather station ID
            forecast_hours: Hours to forecast ahead
            confidence_threshold: Minimum confidence for predictions

        Returns:
            Dict with predictions and automation suggestions
        """
        try:
            client = await self._get_client()

            if prediction_type == "short_term":
                result = await self._generate_short_term_predictions(
                    client, station_id, forecast_hours, confidence_threshold
                )
            elif prediction_type == "trend_analysis":
                result = await self._generate_trend_analysis(
                    client, station_id, forecast_hours
                )
            elif prediction_type == "anomaly_detection":
                result = await self._generate_anomaly_predictions(
                    client, station_id, forecast_hours
                )
            else:
                raise ValueError(f"Unsupported prediction type: {prediction_type}")

            # Add automation suggestions based on predictions
            automation_suggestions = await self._generate_automation_suggestions(
                result, prediction_type
            )

            # Add alert conditions
            alert_conditions = await self._generate_alert_conditions(
                result, prediction_type, confidence_threshold
            )

            response = {
                "success": True,
                "prediction_type": prediction_type,
                "station_id": station_id,
                "forecast_hours": forecast_hours,
                "predictions": result["predictions"],
                "average_confidence": result["average_confidence"],
                "automation_suggestions": automation_suggestions,
                "alert_conditions": alert_conditions,
                "ai_generated": True,
                "model_used": result.get("model_used", "statistical_baseline")
            }

            return response

        except Exception as e:
            logger.error("Prediction generation failed",
                        prediction_type=prediction_type, station_id=station_id, error=str(e))
            return {
                "success": False,
                "prediction_type": prediction_type,
                "station_id": station_id,
                "error": str(e),
                "error_type": type(e).__name__
            }

    async def _generate_short_term_predictions(
        self,
        client: NetatmoClient,
        station_id: str,
        forecast_hours: int,
        confidence_threshold: float
    ) -> Dict[str, Any]:
        """Generate short-term weather predictions."""
        # Get recent historical data (last 24 hours)
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=24)

        historical_data = await client.get_historical_data(
            station_id, start_date, end_date
        )

        if len(historical_data) < 6:  # Need at least 6 hours of data
            return {
                "predictions": [],
                "average_confidence": 0.0,
                "model_used": "insufficient_data"
            }

        predictions = []
        total_confidence = 0.0

        # Simple trend-based prediction
        temperatures = [d.temperature for d in historical_data if d.temperature is not None]
        humidities = [d.humidity for d in historical_data if d.humidity is not None]

        if temperatures:
            # Calculate temperature trend
            temp_trend = self._calculate_trend(temperatures)
            temp_baseline = temperatures[-1]  # Most recent temperature

            # Generate predictions
            for hour in range(1, forecast_hours + 1):
                predicted_temp = temp_baseline + (temp_trend * hour * 0.1)  # Dampened trend

                # Calculate confidence based on data consistency
                temp_std = statistics.stdev(temperatures) if len(temperatures) > 1 else 0
                confidence = max(0.1, min(0.95, 1.0 - (temp_std / max(abs(temp_baseline), 1))))

                if confidence >= confidence_threshold:
                    predictions.append({
                        "hour": hour,
                        "timestamp": (end_date + timedelta(hours=hour)).isoformat(),
                        "temperature": round(predicted_temp, 1),
                        "confidence": round(confidence, 2),
                        "trend": "rising" if temp_trend > 0 else "falling" if temp_trend < 0 else "stable"
                    })
                    total_confidence += confidence

        avg_confidence = total_confidence / max(len(predictions), 1)

        return {
            "predictions": predictions,
            "average_confidence": round(avg_confidence, 2),
            "model_used": "trend_based_prediction",
            "data_points_used": len(historical_data),
            "prediction_horizon": f"{forecast_hours}_hours"
        }

    async def _generate_trend_analysis(
        self,
        client: NetatmoClient,
        station_id: str,
        analysis_hours: int
    ) -> Dict[str, Any]:
        """Generate comprehensive trend analysis."""
        # Get longer historical data (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=analysis_hours)

        historical_data = await client.get_historical_data(
            station_id, start_date, end_date
        )

        if len(historical_data) < 24:  # Need at least 24 hours
            return {
                "predictions": [{"type": "trend_analysis", "result": "insufficient_data"}],
                "average_confidence": 0.0,
                "model_used": "insufficient_data"
            }

        # Analyze trends for each metric
        trends = {}

        metrics = {
            'temperature': [d.temperature for d in historical_data if d.temperature is not None],
            'humidity': [d.humidity for d in historical_data if d.humidity is not None],
            'pressure': [d.pressure for d in historical_data if d.pressure is not None]
        }

        for metric_name, values in metrics.items():
            if len(values) >= 3:
                trend = self._calculate_trend(values)
                trend_strength = abs(trend) / statistics.stdev(values) if statistics.stdev(values) > 0 else 0

                trends[metric_name] = {
                    "direction": "increasing" if trend > 0 else "decreasing" if trend < 0 else "stable",
                    "strength": round(trend_strength, 2),
                    "confidence": min(0.95, trend_strength),
                    "data_points": len(values),
                    "change_rate": round(trend, 3)
                }

        # Generate future predictions based on trends
        predictions = []
        current_data = historical_data[-1] if historical_data else None

        if current_data:
            for hour in range(1, min(25, analysis_hours + 1)):  # Up to 24 hours
                prediction = {
                    "hour": hour,
                    "timestamp": (end_date + timedelta(hours=hour)).isoformat(),
                    "type": "trend_based_forecast"
                }

                # Apply trends to each metric
                for metric_name, trend_info in trends.items():
                    current_value = getattr(current_data, metric_name)
                    if current_value is not None:
                        trend_rate = trend_info["change_rate"]
                        predicted_value = current_value + (trend_rate * hour)
                        prediction[metric_name] = round(predicted_value, 1)
                        prediction[f"{metric_name}_confidence"] = trend_info["confidence"]

                predictions.append(prediction)

        return {
            "predictions": predictions,
            "trends": trends,
            "average_confidence": statistics.mean([t["confidence"] for t in trends.values()]) if trends else 0.0,
            "model_used": "comprehensive_trend_analysis",
            "analysis_period_hours": analysis_hours,
            "metrics_analyzed": list(trends.keys())
        }

    async def _generate_anomaly_predictions(
        self,
        client: NetatmoClient,
        station_id: str,
        detection_hours: int
    ) -> Dict[str, Any]:
        """Generate anomaly detection predictions."""
        # Use sampling manager for anomaly detection
        result = await self._sampling_manager.perform_anomaly_detection_sampling(
            client, station_id, iterations=3
        )

        # Convert to prediction format
        predictions = []

        for iteration in result.iterations:
            anomaly_data = iteration.data

            if "anomalies" in anomaly_data and anomaly_data["anomalies"]:
                for anomaly in anomaly_data["anomalies"][:3]:  # Top 3 anomalies
                    predictions.append({
                        "hour": anomaly.get("index", 0) % 24,  # Convert to hour
                        "timestamp": (datetime.now() + timedelta(hours=anomaly.get("index", 0) % 24)).isoformat(),
                        "type": "anomaly_prediction",
                        "anomaly_type": "statistical_outlier",
                        "severity": anomaly.get("severity", "moderate"),
                        "confidence": min(0.9, anomaly.get("z_score", 2.0) / 4.0),
                        "description": f"Temperature anomaly detected with z-score {anomaly.get('z_score', 0):.1f}"
                    })

        return {
            "predictions": predictions,
            "average_confidence": result.final_quality_score,
            "model_used": "anomaly_detection_model",
            "anomalies_detected": len(predictions),
            "detection_period_hours": detection_hours
        }

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate linear trend slope for a series of values."""
        if len(values) < 2:
            return 0.0

        # Simple linear regression slope
        n = len(values)
        x = list(range(n))
        y = values

        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_xx = sum(xi * xi for xi in x)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
        return slope

    async def _generate_automation_suggestions(
        self,
        prediction_result: Dict[str, Any],
        prediction_type: str
    ) -> List[Dict[str, Any]]:
        """Generate automation suggestions based on predictions."""
        suggestions = []

        predictions = prediction_result.get("predictions", [])

        if prediction_type == "short_term":
            # Temperature-based automation
            temp_predictions = [p for p in predictions if "temperature" in p]
            if temp_predictions:
                high_temp_predictions = [p for p in temp_predictions if p.get("temperature", 0) > 25]
                low_temp_predictions = [p for p in temp_predictions if p.get("temperature", 0) < 10]

                if high_temp_predictions:
                    suggestions.append({
                        "automation_type": "hvac_cooling",
                        "description": "Activate cooling system for predicted high temperatures",
                        "trigger_condition": "temperature > 25°C",
                        "confidence": statistics.mean([p["confidence"] for p in high_temp_predictions]),
                        "priority": "medium"
                    })

                if low_temp_predictions:
                    suggestions.append({
                        "automation_type": "hvac_heating",
                        "description": "Activate heating system for predicted low temperatures",
                        "trigger_condition": "temperature < 10°C",
                        "confidence": statistics.mean([p["confidence"] for p in low_temp_predictions]),
                        "priority": "medium"
                    })

        elif prediction_type == "trend_analysis":
            trends = prediction_result.get("trends", {})

            # Pressure trend automation (potential weather changes)
            if "pressure" in trends:
                pressure_trend = trends["pressure"]
                if pressure_trend["direction"] == "decreasing" and pressure_trend["strength"] > 0.5:
                    suggestions.append({
                        "automation_type": "weather_preparation",
                        "description": "Prepare for potential weather changes (falling pressure)",
                        "trigger_condition": "pressure_trend_decreasing",
                        "confidence": pressure_trend["confidence"],
                        "priority": "low"
                    })

        return suggestions

    async def _generate_alert_conditions(
        self,
        prediction_result: Dict[str, Any],
        prediction_type: str,
        confidence_threshold: float
    ) -> List[Dict[str, Any]]:
        """Generate alert conditions based on predictions."""
        alerts = []

        if prediction_type == "anomaly_detection":
            predictions = prediction_result.get("predictions", [])
            high_confidence_anomalies = [
                p for p in predictions
                if p.get("confidence", 0) >= confidence_threshold and p.get("severity") == "high"
            ]

            if high_confidence_anomalies:
                alerts.append({
                    "alert_type": "weather_anomaly",
                    "condition": "high_severity_anomaly_detected",
                    "description": f"{len(high_confidence_anomalies)} high-severity weather anomalies predicted",
                    "severity": "high",
                    "recommended_action": "Review weather station and prepare for unusual conditions"
                })

        elif prediction_type == "short_term":
            predictions = prediction_result.get("predictions", [])

            # Extreme temperature alerts
            extreme_temps = [
                p for p in predictions
                if p.get("confidence", 0) >= confidence_threshold and
                (p.get("temperature", 20) > 35 or p.get("temperature", 20) < 0)
            ]

            if extreme_temps:
                alerts.append({
                    "alert_type": "extreme_temperature",
                    "condition": "extreme_temperature_predicted",
                    "description": "Extreme temperatures predicted in forecast period",
                    "severity": "medium",
                    "recommended_action": "Take protective measures for extreme weather"
                })

        return alerts