"""
AI sampling tools for weather pattern analysis.

Provides FastMCP 2.14.3 sampling method support for iterative weather
data sampling, pattern recognition, and AI workflow refinement.
"""

from typing import Any

import structlog

from ..core.netatmo_client import NetatmoClient
from ..sampling.weather_sampling import SamplingResult, WeatherSamplingManager

logger = structlog.get_logger(__name__)


class AISamplingTools:
    """AI-powered sampling tools for weather pattern analysis."""

    def __init__(self):
        self._sampling_manager = WeatherSamplingManager()
        self._client: NetatmoClient | None = None

    async def _get_client(self) -> NetatmoClient:
        """Lazy initialization of Netatmo client."""
        if self._client is None:
            self._client = NetatmoClient()
        return self._client

    async def perform_sampling(
        self, sampling_mode: str, station_id: str, iterations: int, refinement_prompt: str
    ) -> dict[str, Any]:
        """
        Perform AI-powered weather sampling with iterative refinement.

        Args:
            sampling_mode: Type of sampling ('iterative', 'predictive', 'anomaly')
            station_id: Weather station ID
            iterations: Number of sampling iterations
            refinement_prompt: AI refinement instructions

        Returns:
            Dict with sampling results and AI workflow insights
        """
        try:
            client = await self._get_client()

            if sampling_mode == "iterative":
                result = await self._sampling_manager.perform_iterative_sampling(
                    client, station_id, iterations, refinement_prompt
                )
            elif sampling_mode == "predictive":
                result = await self._sampling_manager.perform_predictive_sampling(client, station_id, iterations)
            elif sampling_mode == "anomaly":
                result = await self._sampling_manager.perform_anomaly_detection_sampling(client, station_id, iterations)
            else:
                raise ValueError(f"Unsupported sampling mode: {sampling_mode}")

            # Convert to response format
            iterations_data = [
                {
                    "iteration": it.iteration,
                    "timestamp": it.timestamp.isoformat(),
                    "data": it.data,
                    "quality_score": it.quality_score,
                    "refinement_applied": it.refinement_applied,
                }
                for it in result.iterations
            ]

            response = {
                "success": True,
                "sampling_mode": sampling_mode,
                "station_id": station_id,
                "iterations_completed": len(result.iterations),
                "iterations": iterations_data,
                "final_quality_score": result.final_quality_score,
                "ai_workflow_status": "completed",
                "model_training_ready": len(result.iterations) > 3,
                "pattern_recognition_enabled": True,
            }

            if result.pattern_detected:
                response["pattern_detected"] = result.pattern_detected
            if result.predictive_accuracy is not None:
                response["predictive_accuracy"] = result.predictive_accuracy

            return response

        except Exception as e:
            logger.error("AI sampling failed", sampling_mode=sampling_mode, station_id=station_id, error=str(e))
            return {
                "success": False,
                "sampling_mode": sampling_mode,
                "station_id": station_id,
                "error": str(e),
                "ai_workflow_status": "failed",
                "error_type": type(e).__name__,
            }

    async def analyze_sampling_patterns(self, station_id: str, analysis_type: str = "trend_analysis") -> dict[str, Any]:
        """
        Analyze patterns from previous sampling sessions.

        Args:
            station_id: Weather station ID
            analysis_type: Type of analysis ('trend_analysis', 'quality_improvement', 'predictive_accuracy')

        Returns:
            Dict with pattern analysis results
        """
        try:
            # Get sampling history for this station
            history = self._sampling_manager._sampling_history.get(station_id, [])

            if not history:
                return {
                    "success": True,
                    "station_id": station_id,
                    "analysis_type": analysis_type,
                    "result": "no_sampling_history",
                    "message": "No previous sampling sessions found for analysis",
                }

            if analysis_type == "trend_analysis":
                result = await self._analyze_trend_patterns(history)
            elif analysis_type == "quality_improvement":
                result = await self._analyze_quality_improvement(history)
            elif analysis_type == "predictive_accuracy":
                result = await self._analyze_predictive_accuracy(history)
            else:
                raise ValueError(f"Unsupported analysis type: {analysis_type}")

            return {
                "success": True,
                "station_id": station_id,
                "analysis_type": analysis_type,
                "result": result,
                "sessions_analyzed": len(history),
                "ai_insights_generated": True,
            }

        except Exception as e:
            logger.error("Pattern analysis failed", station_id=station_id, analysis_type=analysis_type, error=str(e))
            return {
                "success": False,
                "station_id": station_id,
                "analysis_type": analysis_type,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    async def generate_sampling_insights(
        self, station_id: str, insight_type: str = "optimization_suggestions"
    ) -> dict[str, Any]:
        """
        Generate AI insights from sampling data.

        Args:
            station_id: Weather station ID
            insight_type: Type of insights ('optimization_suggestions', 'automation_opportunities', 'anomaly_alerts')

        Returns:
            Dict with AI-generated insights
        """
        try:
            client = await self._get_client()

            # Get current station status
            stations = await client.get_stations()
            station = next((s for s in stations if s.id == station_id), None)

            if not station:
                raise ValueError(f"Station {station_id} not found")

            # Get recent sampling history
            history = self._sampling_manager._sampling_history.get(station_id, [])
            recent_session = history[-1] if history else None

            insights = await self._generate_insights(station, recent_session, insight_type)

            return {
                "success": True,
                "station_id": station_id,
                "insight_type": insight_type,
                "insights": insights,
                "station_status": "online" if station.reachable else "offline",
                "ai_generated": True,
                "confidence_level": "high" if recent_session else "medium",
            }

        except Exception as e:
            logger.error("Insight generation failed", station_id=station_id, insight_type=insight_type, error=str(e))
            return {
                "success": False,
                "station_id": station_id,
                "insight_type": insight_type,
                "error": str(e),
                "error_type": type(e).__name__,
            }

    async def _analyze_trend_patterns(self, history: list[SamplingResult]) -> dict[str, Any]:
        """Analyze trend patterns from sampling history."""
        if not history:
            return {"pattern": "no_data"}

        # Analyze quality score trends
        quality_scores = [h.final_quality_score for h in history]

        trend = "stable"
        if len(quality_scores) > 1:
            if quality_scores[-1] > quality_scores[0]:
                trend = "improving"
            elif quality_scores[-1] < quality_scores[0]:
                trend = "declining"

        return {
            "pattern": "quality_trend",
            "trend_direction": trend,
            "average_quality": sum(quality_scores) / len(quality_scores),
            "best_session": max(quality_scores),
            "worst_session": min(quality_scores),
            "consistency_score": 1.0 - (max(quality_scores) - min(quality_scores)),
        }

    async def _analyze_quality_improvement(self, history: list[SamplingResult]) -> dict[str, Any]:
        """Analyze quality improvement over sampling sessions."""
        if len(history) < 2:
            return {"improvement": "insufficient_data"}

        # Compare first and last sessions
        first_quality = history[0].final_quality_score
        last_quality = history[-1].final_quality_score

        improvement = last_quality - first_quality
        improvement_rate = improvement / max(abs(first_quality), 0.01)

        return {
            "improvement": "positive" if improvement > 0 else "negative" if improvement < 0 else "stable",
            "absolute_change": improvement,
            "relative_change": improvement_rate,
            "sessions_for_improvement": len(history),
            "learning_efficiency": improvement_rate / len(history),
        }

    async def _analyze_predictive_accuracy(self, history: list[SamplingResult]) -> dict[str, Any]:
        """Analyze predictive accuracy from sampling history."""
        predictive_sessions = [h for h in history if h.predictive_accuracy is not None]

        if not predictive_sessions:
            return {"accuracy": "no_predictive_data"}

        accuracies = [h.predictive_accuracy for h in predictive_sessions]

        return {
            "average_accuracy": sum(accuracies) / len(accuracies),
            "best_accuracy": max(accuracies),
            "worst_accuracy": min(accuracies),
            "predictive_sessions": len(predictive_sessions),
            "accuracy_stability": 1.0 - (max(accuracies) - min(accuracies)),
            "forecasting_reliability": "high" if sum(accuracies) / len(accuracies) > 0.8 else "moderate",
        }

    async def _generate_insights(
        self, station: Any, recent_session: SamplingResult | None, insight_type: str
    ) -> dict[str, Any]:
        """Generate specific insights based on type."""

        if insight_type == "optimization_suggestions":
            suggestions = []

            if not station.reachable:
                suggestions.append(
                    {
                        "priority": "high",
                        "suggestion": "Check station connectivity and network status",
                        "impact": "high",
                        "effort": "medium",
                    }
                )

            if recent_session and recent_session.final_quality_score < 0.7:
                suggestions.append(
                    {
                        "priority": "medium",
                        "suggestion": "Improve sampling parameters for better data quality",
                        "impact": "medium",
                        "effort": "low",
                    }
                )

            if len(station.data_types) < 3:
                suggestions.append(
                    {
                        "priority": "low",
                        "suggestion": "Consider adding more sensor modules for comprehensive monitoring",
                        "impact": "low",
                        "effort": "high",
                    }
                )

            return {"optimization_suggestions": suggestions}

        elif insight_type == "automation_opportunities":
            opportunities = []

            if station.reachable and "temperature" in station.data_types:
                opportunities.append(
                    {
                        "automation_type": "climate_control",
                        "description": "Temperature-based HVAC automation",
                        "confidence": 0.85,
                        "implementation_complexity": "medium",
                    }
                )

            if "rain" in station.data_types:
                opportunities.append(
                    {
                        "automation_type": "irrigation_control",
                        "description": "Weather-based irrigation system control",
                        "confidence": 0.75,
                        "implementation_complexity": "low",
                    }
                )

            return {"automation_opportunities": opportunities}

        elif insight_type == "anomaly_alerts":
            alerts = []

            if recent_session and recent_session.pattern_detected == "high_anomaly_rate":
                alerts.append(
                    {
                        "alert_type": "weather_anomaly",
                        "severity": "high",
                        "description": "Unusual weather patterns detected",
                        "recommended_action": "Review recent weather data and consider protective measures",
                    }
                )

            return {"anomaly_alerts": alerts}

        return {"insights": "no_specific_insights_available"}
