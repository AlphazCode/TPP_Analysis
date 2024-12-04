# src/update_db.py
import pandas as pd
import requests
from datetime import datetime
from typing import Dict, List, Union
import psycopg2
from src.config import db_params, api_config

class WeatherFetcher:
    def __init__(self):
        pass

    def _format_dataframe(self, data: Dict) -> pd.DataFrame:
        df = pd.DataFrame(data['hourly'])
        df['time'] = pd.to_datetime(df['time'])
        df = df.set_index('time')
        
        df.attrs['latitude'] = data['latitude']
        df.attrs['longitude'] = data['longitude']
        df.attrs['elevation'] = data.get('elevation')
        return df

    def fetch_data(self, data_type: str, latitude: float, longitude: float, 
                   start_date: str, end_date: str) -> pd.DataFrame:
        base_url = api_config[data_type]['base_url']
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ','.join(api_config[data_type]['params']),
            "start_date": start_date,
            "end_date": end_date
        }
        
        response = requests.get(base_url, params=params)
        print(response.url)
        if response.ok:
            return self._format_dataframe(response.json())
        else:
            raise Exception(f"API request failed: {response.status_code}")

def insert_weather_data(conn, df, power_plant_id):
    cursor = conn.cursor()
    for idx, row in df.iterrows():
        dateid = int(idx.strftime('%Y%m%d'))
        hour = int(idx.hour)
        
        sql = """
        SELECT dwh.insert_weather_measurements(
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        values = (
            int(power_plant_id), 
            int(dateid), 
            int(hour), 
            float(row['temperature_2m']) if pd.notna(row['temperature_2m']) else None,
            float(row['precipitation']) if pd.notna(row['precipitation']) else None,
            float(row['rain']) if pd.notna(row['rain']) else None,
            float(row['snowfall']) if pd.notna(row['snowfall']) else None,
            float(row['wind_speed_10m']) if pd.notna(row['wind_speed_10m']) else None,
            float(row['wind_speed_100m']) if pd.notna(row['wind_speed_100m']) else None,
            int(row['wind_direction_10m']) if pd.notna(row['wind_direction_10m']) else None,
            int(row['wind_direction_100m']) if pd.notna(row['wind_direction_100m']) else None
        )
        
        cursor.execute(sql, values)
    
    conn.commit()
    cursor.close()

def insert_air_quality_data(conn, df, power_plant_id):
    cursor = conn.cursor()
    for idx, row in df.iterrows():
        dateid = int(idx.strftime('%Y%m%d'))
        hour = int(idx.hour)
        
        sql = """
        SELECT dwh.insert_air_quality_measurements(
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        values = (
            int(power_plant_id), 
            int(dateid), 
            int(hour), 
            float(row['pm10']) if pd.notna(row['pm10']) else None,
            float(row['pm2_5']) if pd.notna(row['pm2_5']) else None,
            float(row['carbon_monoxide']) if pd.notna(row['carbon_monoxide']) else None,
            float(row['carbon_dioxide']) if pd.notna(row['carbon_dioxide']) else None,
            float(row['nitrogen_dioxide']) if pd.notna(row['nitrogen_dioxide']) else None,
            float(row['sulphur_dioxide']) if pd.notna(row['sulphur_dioxide']) else None,
            float(row['ozone']) if pd.notna(row['ozone']) else None,
            float(row['dust']) if pd.notna(row['dust']) else None,
            float(row['ammonia']) if pd.notna(row['ammonia']) else None,
            float(row['methane']) if pd.notna(row['methane']) else None,
            float(row['european_aqi']) if pd.notna(row['european_aqi']) else None,
            float(row['european_aqi_pm2_5']) if pd.notna(row['european_aqi_pm2_5']) else None,
            float(row['european_aqi_pm10']) if pd.notna(row['european_aqi_pm10']) else None,
            float(row['european_aqi_nitrogen_dioxide']) if pd.notna(row['european_aqi_nitrogen_dioxide']) else None,
            float(row['european_aqi_ozone']) if pd.notna(row['european_aqi_ozone']) else None,
            float(row['european_aqi_sulphur_dioxide']) if pd.notna(row['european_aqi_sulphur_dioxide']) else None
        )
        
        cursor.execute(sql, values)
    
    conn.commit()
    cursor.close()