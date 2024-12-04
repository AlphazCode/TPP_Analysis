import math
import streamlit as st
import folium
from streamlit_folium import st_folium

# Interpolating colors based on AQI
def interpolate_color(value, min_value, max_value, start_color, end_color):
    ratio = (value - min_value) / (max_value - min_value)
    ratio = max(0, min(ratio, 1))  # Clamp between 0 and 1

    def hex_to_rgb(hex_color):
        return tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

    def rgb_to_hex(rgb_color):
        return '#' + ''.join(f'{int(c):02x}' for c in rgb_color)

    start_rgb = hex_to_rgb(start_color)
    end_rgb = hex_to_rgb(end_color)
    blended_rgb = tuple(start_rgb[i] + ratio * (end_rgb[i] - start_rgb[i]) for i in range(3))

    return rgb_to_hex(blended_rgb)

# Determine color based on AQI
def get_air_quality_color_gradient(aqi, distance_ratio):
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

# Generate Gaussian plume polygons
def generate_gaussian_plume(lat, lon, wind_speed, wind_direction, stability_class='D', aqi=100, num_arcs=10):
    wind_rad = math.radians(wind_direction)
    lat_factor = 111320
    lon_factor = 111320 * math.cos(math.radians(lat))

    stability_params = {
        'A': (0.22, 0.20), 'B': (0.16, 0.12), 'C': (0.11, 0.08),
        'D': (0.08, 0.06), 'E': (0.06, 0.03), 'F': (0.04, 0.016)
    }
    a, _ = stability_params.get(stability_class, (0.08, 0.06))

    plume_polygons = []
    base_width = wind_speed * 30  # Initial narrow width at the origin

    for i in range(num_arcs):
        # Distance and width calculations
        distance = (i + 1) * wind_speed * 500  # Plume distance increases as the plume moves downwind
        width = base_width * (1 + i*10)  # Width scales with distance

        # AQI decay over distance
        aqi_at_distance = aqi * (0.85 ** i) *1.3

        arc_points = []
        for angle in range(-90, 91, 5):  # Generate an arc spanning -90 to +90 degrees
            angle_rad = math.radians(angle)
            x = distance * math.cos(angle_rad)  # Radial distance adjusted for angle
            y = width * 0.5 * math.sin(angle_rad)  # Lateral spread, proportional to width

            # Adjust position based on wind direction
            offset_lat = lat + (x / lat_factor) * math.cos(wind_rad) - (y / lat_factor) * math.sin(wind_rad)
            offset_lon = lon + (x / lon_factor) * math.sin(wind_rad) + (y / lon_factor) * math.cos(wind_rad)

            arc_points.append((offset_lat, offset_lon))

        # Add the starting position to close the polygon
        arc_points.append((lat, lon))
        color = get_air_quality_color_gradient(aqi_at_distance, i / num_arcs)
        plume_polygons.append((arc_points, color))

    return plume_polygons


# Display plume using Streamlit
def display_gaussian_plume_in_streamlit(plume_polygons, center_lat, center_lon):
    st.title("Gaussian Plume Visualization")

    m = folium.Map(location=[center_lat, center_lon], zoom_start=10)

    # Add marker at starting point
    folium.Marker(
        location=[center_lat, center_lon],
        popup="Starting Point",
        icon=folium.Icon(color='blue', icon='info-sign')
    ).add_to(m)

    # Plot the plume polygons
    for arc_points, color in reversed(plume_polygons):
        folium.Polygon(
            locations=arc_points,
            color=color,
            fill=True,
            fill_opacity=0.3,
            fill_color=color,
        ).add_to(m)

    st_folium(m, width=700, height=500)

# Main logic
if __name__ == "__main__":
    lat, lon = 47.8158, 35.1703  # Example coordinates
    wind_speed = 10  # Example wind speed in m/s
    wind_direction = 170  # Example wind direction in degrees
    stability_class = 'D'  # Neutral stability class
    aqi = 150  # Example AQI value

    # Generate Gaussian plume polygons
    plume_polygons = generate_gaussian_plume(lat, lon, wind_speed, wind_direction, stability_class, aqi)

    # Display plume on the map
    display_gaussian_plume_in_streamlit(plume_polygons, lat, lon)
