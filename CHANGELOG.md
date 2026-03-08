# Changelog

All notable changes to the Netatmo Weather MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Webapp backend (FastAPI):** `web_app.py` exposes REST API for the React frontend: `GET /api/health`, `GET /api/stations`, `GET /api/stations/{id}`, `GET /api/stations/{id}/status`, `GET /api/weather/current?station_id=...`, `GET /api/config/credentials`, `POST /api/config/credentials`.
- **Credentials in Settings:** Netatmo client ID, client secret, username, and password can be entered and saved in the webapp Settings page; stored in backend memory for the session (alternatively use env vars).
- **Webapp UI:** Dashboard (health, station count, current weather from API), Stations page (list and current readings), Trends placeholder, Chat placeholder, Settings (backend URL and Netatmo credentials).
- **Onboarding page:** Get started flow at `/onboarding` (and sidebar link) with steps: create app at dev.netatmo.com, enter credentials in Settings, then use Dashboard. Dashboard error banner links to onboarding when backend or credentials fail.

### Changed
- **Webapp overhaul:** Removed robotics/control/visualizer content; webapp is Netatmo-only and wired to the FastAPI backend. Sidebar branding set to "Netatmo Weather".
- **start.ps1:** Backend runs with `uv run --project $ProjectRoot uvicorn netatmo_weather_mcp.web_app:app` (CWD = web_sota), aligned with fleet backend start pattern. Ports: frontend 10822, backend 10823.
- **WeatherMonitoringTools:** Optional `credentials` argument so the web backend can pass UI-provided credentials instead of env only.

### Fixed
- Webapp had no backend connection and showed placeholder robotics UI; backend and frontend are now connected with a proper API client and error messaging when the backend is down.
- **ConfigurationError:** `netatmo_client.py` now imports `ConfigurationError` from `.exceptions` so missing-credentials errors return a proper message instead of "name 'ConfigurationError' is not defined" (502).

### Documentation
- README: Webapp section (start, onboarding, pages, stations-from-cloud, backend API). Architecture tree updated with `web_app.py` and `web_sota/`. Config table extended with `WEBAPP_ORIGIN` and `VITE_API_URL`. Credentials documented for both env and Settings UI.
- CHANGELOG: Onboarding page, ConfigurationError fix, and doc updates recorded.

---

## [1.0.0] - 2026-01-21

### 🎉 Initial Release

**FastMCP 2.14.3 Compliant AI-Powered Weather Monitoring Server**

#### ✨ Added
- **Complete FastMCP 2.14.3 Implementation**
  - Conversational tool returns with contextual guidance
  - Sampling method support for AI workflows
  - Enhanced response patterns for rich AI dialogue
  - Server lifespan management with proper resource handling

- **Core Weather Monitoring Tools**
  - `weather_station_management`: Portmanteau tool for station discovery, info, and status
  - `weather_data_operations`: Comprehensive weather data retrieval and analysis
  - `ai_weather_sampling`: AI-powered iterative sampling with pattern recognition
  - `weather_prediction_engine`: Advanced predictive analytics and automation suggestions

- **AI Sampling & Analytics**
  - Iterative sampling with AI-guided refinement
  - Predictive sampling for weather forecasting
  - Anomaly detection with statistical analysis
  - Pattern recognition and trend identification
  - Confidence scoring for all predictions

- **Netatmo API Integration**
  - Complete OAuth2 authentication flow
  - Multi-station support with module detection
  - Historical data retrieval with flexible timeframes
  - Real-time data streaming capabilities
  - Comprehensive error handling and rate limiting

- **Monitoring & Observability**
  - Prometheus metrics integration
  - Structured JSON logging with correlation IDs
  - Health check endpoints
  - Performance monitoring and alerting
  - Grafana dashboard configurations

- **MCPB Packaging**
  - Complete MCPB manifest with AI feature declarations
  - Comprehensive prompt templates for AI workflows
  - Docker and cloud-native deployment support
  - Extensive configuration management

#### 🏗️ Architecture
- Modular design with clear separation of concerns
- Async/await patterns throughout for performance
- Comprehensive type hints and documentation
- Extensive error handling with custom exceptions
- Configurable caching and rate limiting

#### 📊 Data Processing
- Real-time weather data processing
- Historical data analysis and aggregation
- AI-powered pattern recognition
- Statistical trend analysis
- Predictive modeling with scikit-learn integration

#### 🔧 Developer Experience
- Comprehensive test suite with pytest
- Code formatting with ruff
- Type checking with mypy
- Development scripts and automation
- Extensive documentation and examples

#### 🚀 Deployment
- Docker containerization
- Kubernetes-ready configurations
- CI/CD pipeline with GitHub Actions
- Environment-based configuration
- Production monitoring stack

---

## Types of Changes

- `🎉 Added` for new features
- `🔧 Changed` for changes in existing functionality
- `🚨 Deprecated` for soon-to-be removed features
- `✂️ Removed` for now removed features
- `🐛 Fixed` for any bug fixes
- `🔒 Security` in case of vulnerabilities

---

## Development Roadmap

### Planned for v1.1.0
- [x] Web dashboard integration (web_sota + FastAPI backend)
- [ ] Additional weather APIs (OpenWeatherMap, Weather Underground)
- [ ] Machine learning model improvements
- [ ] Advanced anomaly detection algorithms
- [ ] Weather-based automation templates

### Planned for v1.2.0
- [ ] Multi-station correlation analysis
- [ ] Weather pattern classification
- [ ] Integration with smart home platforms
- [ ] Mobile app companion
- [ ] Advanced visualization features

---

## Migration Guide

### From v0.x (if applicable)
No migration needed - this is the initial release.

---

## Acknowledgments

Special thanks to:
- The FastMCP team for the excellent MCP framework
- Netatmo for their comprehensive weather API
- The MCP community for standards and best practices
- All contributors and early adopters

---

*For the latest updates, see the [GitHub repository](https://github.com/sandra/netatmo-weather-mcp).*"