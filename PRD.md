# Netatmo Weather MCP — Product Requirements

## Purpose

Provide AI assistants with real-time weather monitoring, historical data analysis, and predictive analytics from Netatmo weather stations. The server bridges Netatmo's cloud API to the MCP ecosystem with four portmanteau tools covering station management, data operations, AI sampling, and prediction.

## Architecture

- **MCP layer**: FastMCP 3.4+ server with dual transport (stdio/HTTP)
- **API layer**: pyatmo client with OAuth2 authentication, caching, rate limiting
- **Webapp layer**: FastAPI REST backend + React/Vite frontend
- **Desktop layer**: Tauri 2.0 NSIS installer with embedded PyInstaller backend

## Shipped Features

- Station discovery and status monitoring
- Current and historical weather data retrieval
- AI-guided iterative sampling with adaptive refinement
- Statistical anomaly detection (2-sigma threshold)
- Linear regression-based temperature forecasting
- Trend analysis (temperature, humidity, pressure)
- Prometheus metrics (request count, latency, active connections)
- Structured JSON logging via structlog
- React dashboard with onboarding flow, station list, settings
- Tauri 2.0 desktop wrapper with NSIS installer
- CUA-NSIS smoke test suite

## Scope (future)

- Extended ML models (scikit-learn time series)
- Weather alert automation
- Multi-station comparison dashboards
- Grafana integration
