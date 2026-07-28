# Per-repo fleet start config for netatmo-weather-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'netatmo-weather-mcp'
    BackendPort  = 10823
    FrontendPort = 10822
    HealthPath   = '/health'
    WebRoot      = 'D:\Dev\repos\netatmo-weather-mcp\web_sota'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'netatmo_weather_mcp.web_app:app'
        SyncExtras    = @('dev')
        Env           = @{ WEB_PORT = '10823' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
