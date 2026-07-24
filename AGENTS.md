# netatmo-weather-mcp Agent Context

FastMCP 3.4+ server for Netatmo weather stations: monitoring, AI sampling, predictive analytics.

## Quick Ref

```powershell
uv run ruff check src/
uv run pytest tests/ -q
uv run python -m netatmo_weather_mcp.server --http --port 10823
.\start.ps1
```

## Ports

| Port | Service |
|------|---------|
| 10822 | Webapp frontend (Vite) |
| 10823 | Webapp backend (FastAPI + MCP HTTP) |

## Tool Patterns

All tools use the portmanteau pattern with an `operation` discriminator:

- `weather_station_management(list|get_info|get_status)`
- `weather_data_operations(current|historical|sample|analyze)`
- `ai_weather_sampling(iterative|predictive|anomaly)`
- `weather_prediction_engine(short_term|trend_analysis|anomaly_detection)`

## Key Files

| File | Purpose |
|------|---------|
| `src/netatmo_weather_mcp/server.py` | FastMCP server, tool registration, main entry |
| `src/netatmo_weather_mcp/transport.py` | Dual transport (stdio/http) with CORS |
| `src/netatmo_weather_mcp/web_app.py` | FastAPI REST backend for webapp |
| `src/netatmo_weather_mcp/core/netatmo_client.py` | Netatmo API client with auth and caching |
| `src/netatmo_weather_mcp/tools/weather_monitoring.py` | Station management + data operations |
| `src/netatmo_weather_mcp/tools/ai_sampling.py` | AI sampling tools |
| `src/netatmo_weather_mcp/tools/predictive_analytics.py` | Prediction engine |
