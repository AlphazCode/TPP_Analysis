# pages/data_loader.py
import streamlit as st
import pandas as pd
from src.update_db import WeatherFetcher, insert_weather_data, insert_air_quality_data
from src.config import db_params
from src.utils import load_plant_data, get_data, fetch_missing_dates, determine_date_range
import psycopg2
from datetime import datetime, timedelta

st.title("Load Historical Data")

# Load plant data
plant_data = load_plant_data()

# Plant selection
plant_names = plant_data['plant_name'].tolist()
selected_plant_name = st.selectbox("Select Power Plant", plant_names)

# Check if the selected plant exists in the DataFrame
if selected_plant_name in plant_names:
    plant_info = plant_data[plant_data['plant_name'] == selected_plant_name].iloc[0]
else:
    st.error("Selected plant not found in the data.")
    st.stop()

# Set default values for weather_min_date and weather_max_date if they are NULL
if pd.isnull(plant_info['weather_min_date']):
    plant_info['weather_min_date'] = pd.to_datetime('20200101', format='%Y%m%d')
if pd.isnull(plant_info['weather_max_date']):
    plant_info['weather_max_date'] = datetime.now()

# Fetch missing dates for the selected power plant


missing_weather_dates_query = f"SELECT dateid FROM dwh.get_missing_weather_dates({plant_info['id']})"
missing_weather_dates_df = fetch_missing_dates(missing_weather_dates_query)

missing_airq_dates_query = f"SELECT dateid FROM dwh.get_missing_airq_dates({plant_info['id']})"
missing_airq_dates_df = fetch_missing_dates(missing_airq_dates_query)

# Determine min and max dates for data


min_date_weather, max_date_weather = determine_date_range(missing_weather_dates_df, plant_info['weather_min_date'], plant_info['weather_max_date'])
min_date_airq, max_date_airq = determine_date_range(missing_airq_dates_df, plant_info['weather_min_date'], plant_info['weather_max_date'])

# Generic function to load data
def load_data(data_type, start_date, end_date, plant_info, insert_function):
    with st.spinner(f"Fetching and loading {data_type} data..."):
        try:
            fetcher = WeatherFetcher()
            
            # Fetch data
            data_df = fetcher.fetch_data(
                data_type,
                plant_info['latitude'],
                plant_info['longitude'],
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            st.write(f"{data_type.capitalize()} Data:", data_df.head())
            print(data_df.head())  # Debugging statement
            # Insert into database
            conn = psycopg2.connect(**db_params)
            insert_function(conn, data_df, plant_info['id'])
            conn.close()
            
            st.success(f"Successfully loaded {data_type} data for {selected_plant_name}")
            
        except Exception as e:
            st.error(f"Error loading {data_type} data: {str(e)}")

# Generic function to load all missing data for all power plants
def load_all_missing_data(data_type, fetch_missing_dates_query, insert_function):
    with st.spinner(f"Fetching and loading all missing {data_type} data for all power plants..."):
        try:
            fetcher = WeatherFetcher()
            conn = psycopg2.connect(**db_params)
            
            for _, plant in plant_data.iterrows():
                # Fetch missing dates
                missing_dates_query = fetch_missing_dates_query.format(plant['id'])
                missing_dates_df = fetch_missing_dates(missing_dates_query)
                if missing_dates_df.empty:
                    st.write(f"No missing {data_type} dates for {plant['plant_name']}. Skipping...")
                    continue
                
                st.write(f"Missing {data_type.capitalize()} Dates for {plant['plant_name']}:", missing_dates_df.head())  # Debugging statement
                
                min_date, max_date = determine_date_range(missing_dates_df, pd.to_datetime('20200101', format='%Y%m%d'), datetime.now())
                
                # Fetch data
                data_df = fetcher.fetch_data(
                    data_type,
                    plant['latitude'],
                    plant['longitude'],
                    min_date.strftime('%Y-%m-%d'),
                    max_date.strftime('%Y-%m-%d')
                )
                st.write(f"{data_type.capitalize()} Data for {plant['plant_name']}:", data_df.head())  # Debugging statement
                
                # Insert into database
                insert_function(conn, data_df, plant['id'])
            
            conn.close()
            st.success(f"Successfully loaded all missing {data_type} data for all power plants")
            
        except Exception as e:
            st.error(f"Error loading all missing {data_type} data for all power plants: {str(e)}")

# Create tabs for weather and air quality data loading
tabs = st.tabs(["Weather Data", "Air Quality Data"])

with tabs[0]:
    st.subheader("Load Weather Data")
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date_weather = st.date_input("Start Date", min_date_weather, min_value=min_date_weather, max_value=max_date_weather, key='start_date_weather')
    with col2:
        end_date_weather = st.date_input("End Date", max_date_weather, min_value=min_date_weather, max_value=max_date_weather, key='end_date_weather')
    
    if st.button("Load Weather Data"):
        load_data('weather', start_date_weather, end_date_weather, plant_info, insert_weather_data)
    
    if st.button("Load All Missing Weather Data"):
        load_data('weather', min_date_weather, max_date_weather, plant_info, insert_weather_data)
    
    if st.button("Load All Missing Weather Data for All Power Plants"):
        load_all_missing_data('weather', "SELECT dateid FROM dwh.get_missing_weather_dates({})", insert_weather_data)

with tabs[1]:
    st.subheader("Load Air Quality Data")
    
    # Date range selection
    col1, col2 = st.columns(2)
    with col1:
        start_date_air_quality = st.date_input("Start Date", min_date_airq, min_value=min_date_airq, max_value=max_date_airq, key='start_date_air_quality')
    with col2:
        end_date_air_quality = st.date_input("End Date", max_date_airq, min_value=min_date_airq, max_value=max_date_airq, key='end_date_air_quality')
    
    if st.button("Load Air Quality Data"):
        load_data('air_quality', start_date_air_quality, end_date_air_quality, plant_info, insert_air_quality_data)
    
    if st.button("Load All Missing Air Quality Data"):
        load_data('air_quality', min_date_airq, max_date_airq, plant_info, insert_air_quality_data)
    
    if st.button("Load All Missing Air Quality Data for All Power Plants"):
        load_all_missing_data('air_quality', "SELECT dateid FROM dwh.get_missing_airq_dates({})", insert_air_quality_data)