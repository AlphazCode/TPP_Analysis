
weather_hourly = ["temperature_2m", "precipitation", "rain", "snowfall",
                      "wind_speed_10m", "wind_speed_100m",
                      "wind_direction_10m", "wind_direction_100m"]

air_quality_hourly = ["pm10", "pm2_5", "carbon_monoxide", "carbon_dioxide",
                      "nitrogen_dioxide", "sulphur_dioxide", "ozone", "dust",
                      "ammonia", "methane", "european_aqi", "european_aqi_pm2_5",
                      "european_aqi_pm10", "european_aqi_nitrogen_dioxide",
                      "european_aqi_ozone", "european_aqi_sulphur_dioxide"]

# config.py
db_params = {
    "database": "tpp_analysis",
    "user": "postgres",
    "password": "postgres", 
    "host": "localhost",
    "port": "5432"
}

# db_params = {
#     'url': 'postgresql://postgres:postgres@localhost:5432/tpp_analysis'
# }


api_config = {
    "weather": {
        "base_url": "https://archive-api.open-meteo.com/v1/archive",
        "params": weather_hourly
    },
    "air_quality": {
        "base_url": "https://air-quality-api.open-meteo.com/v1/air-quality",
        "params": air_quality_hourly
    }
}

