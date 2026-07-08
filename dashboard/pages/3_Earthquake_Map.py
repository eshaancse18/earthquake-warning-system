import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Earthquake Map",
    layout="wide"
)

st.title("🌍 Earthquake Monitoring Map")

st.markdown("---")

# -------------------------------------------------
# Station data (temporary)
# Later this will come from PostgreSQL
# -------------------------------------------------

stations = [
    {
        "id": "SSN_001",
        "lat": 28.6139,
        "lon": 77.2090,
        "status": "Online"
    }
]

# -------------------------------------------------
# Demo earthquake event
# Later this comes from CRS
# -------------------------------------------------

event = {
    "lat": 28.6200,
    "lon": 77.2150,
    "magnitude": 4.6
}

# -------------------------------------------------
# Create Map
# -------------------------------------------------

m = folium.Map(
    location=[28.615, 77.210],
    zoom_start=12
)

# -------------------------------------------------
# Add station markers
# -------------------------------------------------

for station in stations:

    color = "green" if station["status"] == "Online" else "red"

    folium.Marker(
        location=[station["lat"], station["lon"]],
        popup=f"""
        <b>{station['id']}</b><br>
        Status: {station['status']}
        """,
        tooltip=station["id"],
        icon=folium.Icon(color=color, icon="signal", prefix="fa")
    ).add_to(m)

# -------------------------------------------------
# Earthquake epicenter
# -------------------------------------------------

folium.Marker(
    location=[event["lat"], event["lon"]],
    popup=f"Magnitude {event['magnitude']}",
    tooltip="Earthquake",
    icon=folium.Icon(color="red", icon="warning-sign")
).add_to(m)

# -------------------------------------------------
# Detection radius
# -------------------------------------------------

folium.Circle(
    location=[event["lat"], event["lon"]],
    radius=2000,
    color="red",
    fill=True,
    fill_opacity=0.2
).add_to(m)

# -------------------------------------------------
# Display
# -------------------------------------------------

st_folium(
    m,
    width=None,
    height=650
)