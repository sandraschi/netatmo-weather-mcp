# Netatmo Weather MCP - AI-Powered Weather Monitoring

This MCP server provides comprehensive weather monitoring with AI sampling, predictive analytics, and automation capabilities for Netatmo weather stations.

## 🚀 Quick Start

1. **Configure Environment:**
   ```bash
   export NETATMO_CLIENT_ID="your_client_id"
   export NETATMO_CLIENT_SECRET="your_client_secret"
   export NETATMO_USERNAME="your_email"
   export NETATMO_PASSWORD="your_password"
   ```

2. **Discover Stations:**
   Use `weather_station_management` with `operation="list"` to find your weather stations.

3. **Monitor Weather:**
   Use `weather_data_operations` with `operation="current"` for real-time data.

4. **AI Analysis:**
   Try `ai_weather_sampling` with `sampling_mode="iterative"` for intelligent pattern discovery.

## 🎯 Key Features

### AI Sampling & Analysis
- **Iterative Sampling**: AI-guided weather pattern discovery with continuous refinement
- **Predictive Modeling**: Short-term weather forecasting with confidence scoring
- **Anomaly Detection**: Statistical analysis for unusual weather patterns
- **Pattern Recognition**: Automated identification of weather trends and cycles

### Conversational Interface
- **Context-Aware Responses**: Tools provide conversational context and next-step suggestions
- **Workflow Guidance**: AI suggests optimal sequences of operations
- **Error Recovery**: Helpful hints when operations fail
- **Progress Tracking**: Real-time feedback on long-running operations

### Predictive Analytics
- **Weather Forecasting**: AI-powered predictions with confidence intervals
- **Trend Analysis**: Long-term weather pattern analysis
- **Automation Suggestions**: Smart home integration recommendations
- **Alert Generation**: Intelligent weather alert conditions

## 📊 Available Tools

### 1. Weather Station Management
```python
# List all stations
weather_station_management(operation="list")

# Get detailed station info
weather_station_management(operation="get_info", station_id="70:ee:50:12:34:56")

# Check station status
weather_station_management(operation="get_status", station_id="70:ee:50:12:34:56")
```

### 2. Weather Data Operations
```python
# Get current weather
weather_data_operations(operation="current", station_id="70:ee:50:12:34:56")

# Get historical data (last 24 hours)
weather_data_operations(operation="historical", station_id="70:ee:50:12:34:56", timeframe="24h")

# Analyze weather patterns
weather_data_operations(operation="analyze", station_id="70:ee:50:12:34:56")
```

### 3. AI Weather Sampling
```python
# Iterative sampling with AI refinement
ai_weather_sampling(
    sampling_mode="iterative",
    station_id="70:ee:50:12:34:56",
    iterations=5,
    refinement_prompt="focus on temperature patterns"
)

# Predictive sampling for forecasting
ai_weather_sampling(
    sampling_mode="predictive",
    station_id="70:ee:50:12:34:56",
    iterations=3
)

# Anomaly detection
ai_weather_sampling(
    sampling_mode="anomaly",
    station_id="70:ee:50:12:34:56",
    iterations=3
)
```

### 4. Weather Prediction Engine
```python
# Short-term predictions
weather_prediction_engine(
    prediction_type="short_term",
    station_id="70:ee:50:12:34:56",
    forecast_hours=24,
    confidence_threshold=0.8
)

# Trend analysis
weather_prediction_engine(
    prediction_type="trend_analysis",
    station_id="70:ee:50:12:34:56",
    forecast_hours=168  # 1 week
)

# Anomaly prediction
weather_prediction_engine(
    prediction_type="anomaly_detection",
    station_id="70:ee:50:12:34:56",
    forecast_hours=48
)
```

## 🔧 Configuration

### Required Environment Variables
- `NETATMO_CLIENT_ID`: Your Netatmo app client ID
- `NETATMO_CLIENT_SECRET`: Your Netatmo app client secret
- `NETATMO_USERNAME`: Your Netatmo account email
- `NETATMO_PASSWORD`: Your Netatmo account password

### Optional Environment Variables
- `NETATMO_SCOPE`: API permissions (default: "read_station")
- `METRICS_PORT`: Prometheus metrics port (default: 9091)
- `ENABLE_METRICS`: Enable Prometheus metrics (default: true)
- `LOG_LEVEL`: Logging level (default: INFO)

## 🤖 AI Workflow Examples

### Complete Weather Analysis
1. Discover and verify station connectivity
2. Retrieve current and historical weather data
3. Run AI sampling for pattern discovery
4. Generate predictions and automation suggestions
5. Set up monitoring alerts

### Smart Home Integration
1. Analyze weather patterns and predictions
2. Generate automation suggestions based on AI insights
3. Set up weather-based triggers for HVAC, irrigation, etc.
4. Monitor system performance and adjust as needed

### Research & Analysis
1. Perform iterative sampling for comprehensive data collection
2. Use predictive analytics for weather forecasting
3. Analyze long-term trends and patterns
4. Generate reports and visualizations

## 📈 Monitoring & Metrics

The server provides comprehensive monitoring:
- **Prometheus Metrics**: Performance and usage statistics
- **Structured Logging**: Detailed operation logs with context
- **Health Checks**: System status and connectivity monitoring
- **Performance Tracking**: Response times and error rates

## 🔒 Security & Privacy

- Secure OAuth2 authentication with Netatmo
- No data storage outside your local environment
- Encrypted API communications
- Configurable access controls

## 🚀 Getting Started

1. **Install**: `pip install netatmo-weather-mcp`
2. **Configure**: Set required environment variables
3. **Run**: `netatmo-weather-mcp`
4. **Connect**: Configure your MCP client to use the server

For detailed setup instructions, see the main README.md file.