# pages/analytics.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from src.utils import get_data, load_plant_data

def format_dateid(dateid):
    return pd.to_datetime(str(dateid), format='%Y%m%d')

def get_stat_by_plant_id(plant_id, start_date, end_date=None, record_hour=None):
    query = """
        SELECT * FROM dwh.get_stat_by_plant_id(%s, %s, %s, %s)
    """
    params = (
        int(plant_id), 
        int(start_date.strftime('%Y%m%d')), 
        int(end_date.strftime('%Y%m%d')) if end_date else None, 
        int(record_hour) if record_hour is not None else None
    )
    return get_data(query, params)

st.title("Weather and Air Quality Analysis")

# Load plant data
plant_data = load_plant_data()

# Data filters
st.markdown("### Data Filters")
plant_names = plant_data['plant_name'].tolist()
selected_plant = st.selectbox("Select Power Plant", plant_names, key='data_plant')
plant_info = plant_data[plant_data['plant_name'] == selected_plant].iloc[0]

start_date = st.date_input("Start Date", 
                          plant_info['weather_min_date'],
                          min_value=plant_info['weather_min_date'],
                          max_value=plant_info['weather_max_date'],
                          key='data_start')

end_date = st.date_input("End Date",
                        plant_info['weather_max_date'],
                        min_value=plant_info['weather_min_date'],
                        max_value=plant_info['weather_max_date'],
                        key='data_end')

if st.button("Fetch Data"):
    with st.spinner("Fetching data..."):
        data = get_stat_by_plant_id(plant_info['id'], start_date, end_date)
            
        data['date'] = data['dateid'].apply(format_dateid)
        
        pollutants = ['pm10', 'pm2_5', 'nitrogen_dioxide', 'sulphur_dioxide', 'ozone']
        
        tabs = st.tabs(["Weather", "Air Quality", "Time Analysis", "Wind Analysis", "Correlations"])
        
        with tabs[0]:
            # Temperature trend
            fig_temp = go.Figure()
            fig_temp.add_trace(go.Scatter(
                x=data['date'],
                y=data['temperature_2m'],
                name='Temperature',
                line=dict(color='#FF6B6B', width=2)
            ))
            fig_temp.add_trace(go.Scatter(
                x=data['date'],
                y=data['temperature_2m'].rolling(24).mean(),
                name='24h Average',
                line=dict(color='#4ECDC4', width=2, dash='dash')
            ))
            fig_temp.update_layout(title='Temperature Trends (°C)', height=400)
            st.plotly_chart(fig_temp, use_container_width=True)
            
            # Wind rose
            fig_wind = px.scatter_polar(
                data,
                r='wind_speed_100m',
                theta='wind_direction_100m',
                color='temperature_2m',
                title='Wind Pattern Analysis',
                color_continuous_scale=['#FF6B6B', '#4ECDC4'],
                height=500
            )
            st.plotly_chart(fig_wind, use_container_width=True)
            
            # Precipitation
            fig_precip = px.area(
                data,
                x='date',
                y=['precipitation'],
                title='Precipitation Components',
                labels={'value': 'mm', 'variable': 'Type'},
                color_discrete_sequence=['#45B7D1'],
                height=400
            )
            st.plotly_chart(fig_precip, use_container_width=True)
        
        with tabs[1]:
            # Pollutants trend
            fig_poll = px.line(
                data,
                x='date',
                y=pollutants,
                title='Pollutant Levels Over Time',
                color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD'],
                height=400
            )
            fig_poll.update_layout(
                xaxis=dict(
                    rangeselector=dict(
                        buttons=list([
                            dict(count=1, label="1d", step="day", stepmode="backward"),
                            dict(count=7, label="1w", step="day", stepmode="backward"),
                            dict(count=1, label="1m", step="month", stepmode="backward"),
                            dict(step="all")
                        ])
                    )
                ),
                hovermode='x unified'
            )
            st.plotly_chart(fig_poll, use_container_width=True)
            
            # Daily distributions
            daily_agg = data.groupby('date')[pollutants].mean()
            fig_box = px.box(
                daily_agg.melt(ignore_index=False).reset_index(),
                x='variable',
                y='value',
                color='variable',
                title='Daily Pollutant Distributions',
                color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD'],
                height=400
            )
            st.plotly_chart(fig_box, use_container_width=True)
        
        with tabs[2]:
            # Hourly patterns
            hourly_avg = data.groupby('record_hour')[pollutants].mean()
            fig_hourly = px.line(
                hourly_avg,
                title='Average Daily Patterns',
                color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD'],
                height=400
            )
            st.plotly_chart(fig_hourly, use_container_width=True)
            
            # Weekly averages
            weekly_avg = data.groupby(
                data['date'].dt.isocalendar().week
            )[pollutants].mean()
            fig_weekly = px.line(
                weekly_avg,
                title='Weekly Trends',
                color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD'],
                height=400
            )
            st.plotly_chart(fig_weekly, use_container_width=True)
        
        with tabs[3]:
            # Wind speed distribution
            fig_wind_dist = px.histogram(
                data,
                x='wind_speed_100m',
                nbins=30,
                title='Wind Speed Distribution',
                color_discrete_sequence=['#45B7D1'],
                height=400
            )
            st.plotly_chart(fig_wind_dist, use_container_width=True)
            
            # Wind direction vs speed
            fig_wind_dir = px.scatter_polar(
                data,
                r='wind_speed_100m',
                theta='wind_direction_100m',
                color='wind_speed_100m',
                title='Wind Speed by Direction',
                color_continuous_scale=['#45B7D1', '#FF6B6B'],
                height=500
            )
            st.plotly_chart(fig_wind_dir, use_container_width=True)
        
        with tabs[4]:
            st.header("Pollutant Correlations")
            
            # Correlation matrix
            corr = data[pollutants].corr()
            mask = np.triu(np.ones_like(corr, dtype=bool))
            fig_corr = px.imshow(
                np.ma.masked_array(corr, mask),
                labels=dict(color='Correlation'),
                title='Pollutant Correlations',
                color_continuous_scale=['#FF6B6B', '#FFFFFF', '#4ECDC4'],
                height=400
            )
            st.plotly_chart(fig_corr, use_container_width=True)
            
            # Scatter plots for pairwise correlations
            for i, pol1 in enumerate(pollutants):
                for j, pol2 in enumerate(pollutants):
                    if i < j:  # Only plot upper triangle
                        fig_scatter = px.scatter(
                            data,
                            x=pol1,
                            y=pol2,
                            title=f'{pol1} vs {pol2}',
                            opacity=0.6,
                            color_discrete_sequence=['#FF6B6B']
                        )
                        st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Temperature vs pollutants
            for pollutant in pollutants:
                fig_temp_corr = px.scatter(
                    data,
                    x='temperature_2m',
                    y=pollutant,
                    title=f'Temperature vs {pollutant}',
                    opacity=0.6,
                    color_discrete_sequence=['#FF6B6B']
                )
                st.plotly_chart(fig_temp_corr, use_container_width=True)