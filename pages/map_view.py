import streamlit as st
import folium
from streamlit_folium import folium_static
import time
from src.utils import get_data, calculate_gaussian_plume, add_gaussian_plume_to_map
import pandas as pd
from datetime import datetime

@st.cache_data
def load_data(plant_info, selected_date):
    query = f"""
        SELECT * FROM dwh.get_stat_by_plant_id({plant_info['id']}, {selected_date.strftime('%Y%m%d')})
    """
    data = get_data(query)
    return data

@st.cache_data
def load_plant_data():
    query = "SELECT * FROM dwh.v_plant_dates"
    data = get_data(query)
    return data

def show_map_view_page():
    st.title("Map View of Air Quality Data")

    # Load plant data
    plant_data = load_plant_data()

    # Filters
    st.markdown("### Map Filters")
    
    # Select Power Plant
    plant_names = plant_data['plant_name'].tolist()
    selected_plant = st.selectbox("Select Power Plant", plant_names, key='map_plant')
    plant_info = plant_data[plant_data['plant_name'] == selected_plant].iloc[0]

    # Set default values for air_min_date and air_max_date if they are NULL
    if pd.isnull(plant_info['air_min_date']):
        plant_info['air_min_date'] = pd.to_datetime('20200101', format='%Y%m%d')
    if pd.isnull(plant_info['air_max_date']):
        plant_info['air_max_date'] = datetime.now()

    min_date_airq = pd.to_datetime(plant_info['air_min_date'], format='%Y%m%d')
    max_date_airq = pd.to_datetime(plant_info['air_max_date'], format='%Y%m%d')

    # Date handling
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = max_date_airq

    # Ensure the default value is within the allowed range
    default_date = min(max_date_airq, max(min_date_airq, st.session_state.selected_date))

    # Date selection
    selected_date = st.date_input("Select Date",
                                  value=default_date,
                                  min_value=min_date_airq,
                                  max_value=max_date_airq,
                                  key='map_date')

    # Hour selection
    if 'selected_hour' not in st.session_state:
        st.session_state.selected_hour = 0

    selected_hour = st.slider("Select Hour", 0, 23, st.session_state.selected_hour, key='map_hour')

    # Animate button
    animate_button_text = "Animate" if not st.session_state.get('animate', False) else "Stop"
    if st.button(animate_button_text):
        st.session_state.animate = not st.session_state.get('animate', False)

    # Load data
    data = load_data(plant_info, selected_date)

    def update_map(hour):
        df = data[data['record_hour'] == hour]

        if not df.empty:
            view_lat = float(df['latitude'].iloc[0])
            view_lon = float(df['longitude'].iloc[0])
            wind_speed = df['wind_speed_100m'].iloc[0] if df['wind_speed_100m'].iloc[0] is not None else 0
            wind_direction = df['wind_direction_100m'].iloc[0] if df['wind_direction_100m'].iloc[0] is not None else 0
            aqi = df['european_aqi'].iloc[0] if df['european_aqi'].iloc[0] is not None else 0

            # Skip if wind_speed is zero to avoid division by zero
            if wind_speed == 0:
                st.warning("Wind speed is zero, skipping this hour.")
                return

            # Create map
            m = folium.Map(location=[view_lat, view_lon], zoom_start=12)

            # Add plant marker
            folium.Marker(
                location=[view_lat, view_lon],
                popup=f"Power Plant: {selected_plant}<br>Hour: {hour}<br>Wind Speed: {wind_speed:.1f} m/s<br>Wind Direction: {wind_direction:.0f}°",
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)

            plume_points = calculate_gaussian_plume(plant_info['id'], wind_speed, wind_direction, aqi=aqi*5)
            # for dat in plume_points:
            #     print(dat)
            #     print(f"City: {dat['city']} - AQI: {dat['aqi']}")
            #     coords, aqi_value, city = dat
            add_gaussian_plume_to_map(plume_points, m)

            # Display wind information and map on the same line
            col1, col2, col3 = st.columns([1,1, 3])
            with col1:
                inf = f"### Wind Information\n**Wind Speed:** {wind_speed:.1f} m/s\n**Wind Direction:** {wind_direction:.0f}°\n"
                st.markdown(inf)
            with col1:
                inf = f"### Wind Information\n**Wind Speed:** {wind_speed:.1f} m/s\n**Wind Direction:** {wind_direction:.0f}°\n"
                st.markdown(inf)
            with col2:
                folium_static(m, width=700, height=500)
        else:
            st.warning("No data available for selected date and hour")

    # Initial map update
    update_map(selected_hour)

    if st.session_state.get('animate', False):
        current_hour = st.session_state.selected_hour
        current_date = st.session_state.selected_date

        while st.session_state.get('animate', False):
            update_map(current_hour)
            time.sleep(4)

            if current_hour < 23:
                current_hour += 1
            else:
                current_hour = 0
                current_date += pd.Timedelta(days=1)

            st.session_state.selected_hour = current_hour
            st.session_state.selected_date = current_date

# Call the function to show the map view page
show_map_view_page()