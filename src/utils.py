import psycopg2
import pandas as pd
from src.config import *
import math
import folium
import random

def get_data(query, params=None):
    conn = psycopg2.connect(**db_params)
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

def load_plant_data():
    query = "SELECT * FROM dwh.v_plant_dates vpd"
    df = get_data(query)
    df['weather_min_date'] = pd.to_datetime(df['weather_min_date'], format='%Y%m%d')
    df['weather_max_date'] = pd.to_datetime(df['weather_max_date'], format='%Y%m%d')
    return df

def interpolate_color(value, min_value, max_value, start_color, end_color):
    """Interpolate color between start_color and end_color based on a value."""
    ratio = (value - min_value) / (max_value - min_value)
    ratio = max(0, min(ratio, 1))  # Clamp between 0 and 1
    
    def hex_to_rgb(hex_color):
        return tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    
    def rgb_to_hex(rgb_color):
        return '#' + ''.join(f'{int(c):02x}' for c in rgb_color)
    
    start_rgb = hex_to_rgb(start_color)
    end_rgb = hex_to_rgb(end_color)
    
    blended_rgb = tuple(
        start_rgb[i] + ratio * (end_rgb[i] - start_rgb[i])
        for i in range(3)
    )
    
    return rgb_to_hex(blended_rgb)

def get_air_quality_color_gradient(aqi, distance_ratio):
    """Return interpolated color based on AQI ranges and distance."""
    green_color = '#00FF00'
    if aqi <= 50:
        start_color = '#00FF00'  # Green
    elif aqi <= 100:
        start_color = '#FFFF00'  # Yellow
    elif aqi <= 150:
        start_color = '#FFA500'  # Orange
    elif aqi <= 200:
        start_color = '#FF0000'  # Red
    elif aqi <= 300:
        start_color = '#800080'  # Purple
    else:
        start_color = '#A52A2A'  # Brown
    
    return interpolate_color(distance_ratio, 0, 1, start_color, green_color)

def calculate_gaussian_plume(lat, lon, wind_speed, wind_direction, stability_class='D', aqi=100, num_arcs=8):
    wind_rad = math.radians(wind_direction)
    lat_factor = 111320
    lon_factor = 111320 * math.cos(math.radians(lat))

    stability_params = {
        'A': (0.22, 0.20), 'B': (0.16, 0.12), 'C': (0.11, 0.08),
        'D': (0.08, 0.06), 'E': (0.06, 0.03), 'F': (0.04, 0.016)
    }
    a, _ = stability_params.get(stability_class, (0.08, 0.06))

    # Calculate the shifted starting position (2 km upwind)
    shift_distance = -1000  # 2 km in meters (negative to go upwind)
    shifted_lat = lat + (shift_distance / lat_factor) * math.cos(wind_rad)
    shifted_lon = lon + (shift_distance / lon_factor) * math.sin(wind_rad)

    plume_polygons = []
    base_width = wind_speed * 60  # Initial narrow width at the origin

    for i in range(num_arcs):
        # Distance and width calculations
        distance = (i + 1) * wind_speed * 70  # Plume distance increases as the plume moves downwind
        width = base_width * (1 + i)  # Width scales with distance

        # AQI decay over distance
        aqi_at_distance = aqi  * (0.65 ** (i * 1)) * 15

        arc_points = []
        for angle in range(-180, 181, 5):  # Generate an arc spanning -90 to +90 degrees
            if abs(angle) < 100:
                coef = 0.05
            else:
                coef = 1
            angle_rad = math.radians(angle* coef)
            x = distance * coef *2 * math.cos(angle_rad)  # Radial distance adjusted for angle
            y = width * 0.5 * math.sin(angle_rad)  # Lateral spread, proportional to width

            # Adjust position based on wind direction
            offset_lat = shifted_lat + (x / lat_factor) * math.cos(wind_rad) - (y / lat_factor) * math.sin(wind_rad)
            offset_lon = shifted_lon + (x / lon_factor) * math.sin(wind_rad) + (y / lon_factor) * math.cos(wind_rad)

            arc_points.append((offset_lat, offset_lon))

        # Add the shifted starting position to close the polygon
        arc_points.append((shifted_lat, shifted_lon))
        color = get_air_quality_color_gradient(aqi_at_distance, i / num_arcs)
        plume_polygons.append((arc_points, color))

    return plume_polygons




def add_gaussian_plume_to_map(plume_polygons, map_object):
    for arc_points, color in reversed(plume_polygons):
        folium.Polygon(
            locations=arc_points,
            color=color,
            fill=True,
            fill_opacity=0.3,
            fill_color=color,
        ).add_to(map_object)

def fetch_missing_dates(query):
    df = get_data(query)
    if df.empty:
        return df
    df['dateid'] = pd.to_datetime(df['dateid'], format='%Y%m%d')
    return df

def determine_date_range(missing_dates_df, default_min_date, default_max_date):
    if not missing_dates_df.empty:
        min_date = missing_dates_df['dateid'].min()
        max_date = missing_dates_df['dateid'].max()
    else:
        min_date = default_min_date
        max_date = default_max_date
    return min_date, max_date