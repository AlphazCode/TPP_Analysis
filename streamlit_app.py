# index.py
import streamlit as st
from streamlit.elements.image import MAXIMUM_CONTENT_WIDTH

# Configure pages
analytics       = st.Page("pages/analytics.py", title="Data Analysis")
map_view        = st.Page("pages/map_view.py", title="Map View")
data_loader     = st.Page("pages/data_loader.py", title="Load Data")
index           = st.Page("pages/index.py", title="Home",default=True )

# Setup navigation
navigation = st.navigation([index, analytics, map_view, data_loader])

# Page config
st.set_page_config(
    page_title="Power Plant Analysis",
    layout="wide",
)


# Run navigation system
navigation.run()