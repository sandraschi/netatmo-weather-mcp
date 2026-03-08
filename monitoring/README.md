# Netatmo Weather MCP Monitoring

This directory contains monitoring and observability configurations for the Netatmo Weather MCP server.

## 📊 Monitoring Stack

The Netatmo Weather MCP includes comprehensive monitoring capabilities:

- **Prometheus Metrics**: Performance metrics, API call statistics, and health indicators
- **Structured Logging**: JSON-formatted logs with context and correlation IDs
- **Health Checks**: System status monitoring and connectivity validation
- **Performance Tracking**: Response times, error rates, and resource usage

## 🔧 Configuration Files

### Prometheus Metrics (`prometheus.yml`)
Main Prometheus configuration for scraping metrics from the MCP server.

### Loki + Promtail (`promtail/`)
- `promtail-config.yml`: Log aggregation configuration for Loki

### Grafana Dashboards
Pre-configured dashboards for visualizing weather data and system metrics.

## 📈 Available Metrics

### HTTP/API Metrics
- `netatmo_requests_total`: Total number of API requests by method and endpoint
- `netatmo_request_duration_seconds`: Request latency histograms
- `netatmo_active_connections`: Number of active connections

### Weather Data Metrics
- `netatmo_weather_samples_total`: Total weather samples processed
- `netatmo_sampling_quality_score`: AI sampling quality scores
- `netatmo_prediction_accuracy`: Weather prediction accuracy metrics

### System Health Metrics
- Connection status and health checks
- Error rates and failure patterns
- Resource usage (memory, CPU when available)

## 🚀 Quick Start

### Local Development
```bash
# Start Prometheus
docker run -p 9090:9090 -v $(pwd)/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus

# Start Grafana
docker run -p 3000:3000 grafana/grafana

# Start Loki
docker run -p 3100:3100 grafana/loki

# Start Promtail
docker run -v $(pwd)/monitoring/promtail:/mnt/config grafana/promtail --config.file=/mnt/config/promtail-config.yml
```

### Production Setup
Use the provided Docker Compose configuration in the root directory for a complete monitoring stack.

## 📋 Dashboards

### Weather Station Dashboard
- Real-time weather metrics from all stations
- Historical trends and patterns
- AI sampling results and quality scores
- Prediction accuracy over time

### System Performance Dashboard
- API response times and error rates
- Active connections and throughput
- Resource usage and system health
- Sampling and prediction performance

### AI Workflow Dashboard
- Sampling iteration success rates
- Prediction accuracy trends
- Automation suggestion effectiveness
- AI model performance metrics

## 🔍 Log Aggregation

All logs are structured JSON with the following fields:
- `timestamp`: ISO 8601 timestamp
- `level`: Log level (INFO, WARNING, ERROR)
- `logger`: Logger name
- `message`: Human-readable message
- `context`: Additional context data
- `correlation_id`: Request correlation ID
- `station_id`: Weather station identifier (when applicable)
- `operation`: Operation being performed
- `duration_ms`: Operation duration in milliseconds
- `error_type`: Error classification (when applicable)

## 🎯 Health Checks

The server provides health check endpoints:
- `/health`: Basic health status
- `/health/detailed`: Comprehensive system health with metrics
- `/metrics`: Prometheus metrics endpoint

## 🚨 Alerting

Configure alerts for:
- High error rates (>5% in 5 minutes)
- Station connectivity issues
- Low prediction accuracy (<70%)
- High latency (>2 seconds average)
- AI sampling failures

## 📊 Metrics Collection

Metrics are automatically collected for:
- All API calls to Netatmo
- Tool executions and their performance
- AI sampling operations and quality scores
- Weather data processing and analysis
- Prediction generation and accuracy tracking

## 🔧 Troubleshooting

### Common Issues

1. **Metrics not appearing in Prometheus**
   - Check that `ENABLE_METRICS=true` (default)
   - Verify metrics port is accessible (default: 9091)
   - Check Prometheus scrape configuration

2. **Logs not appearing in Loki**
   - Verify Promtail configuration
   - Check log file paths and permissions
   - Ensure Loki is running and accessible

3. **High error rates**
   - Check Netatmo API connectivity
   - Review authentication configuration
   - Monitor rate limiting and backoff logic

4. **Poor prediction accuracy**
   - Ensure sufficient historical data (>24 hours)
   - Check data quality and completeness
   - Review AI model parameters and training data

## 📈 Scaling and Performance

For high-volume deployments:
- Increase Prometheus retention period
- Configure log rotation for Loki
- Set up horizontal scaling for Grafana
- Monitor resource usage and adjust limits accordingly