import streamlit as st
import pandas as pd
from datetime import datetime

from utils.live_data import live_data

st.set_page_config(
    page_title="Live Stations",
    layout="wide"
)

st.title("📡 Live Sensor Stations")

st.markdown("---")

# ---------------------------------------------------
# Start Live Data Service
# ---------------------------------------------------

live_data.start()

# ---------------------------------------------------
# Get Latest Health Data
# ---------------------------------------------------

health = live_data.get_station_health()

stations = []

for station_id, data in health.items():

    stations.append({

        "Station ID": station_id,

        "Status": "🟢 Online",

        "Latitude": data.get("latitude", "--"),

        "Longitude": data.get("longitude", "--"),

        "CPU (%)": data.get("cpu", "--"),

        "RAM (%)": data.get("ram", "--"),

        "Temperature (°C)": data.get("temperature", "--"),

        "Last Heartbeat": data.get(
            "timestamp",
            datetime.now().strftime("%H:%M:%S")
        )
    })

df = pd.DataFrame(stations)

# ---------------------------------------------------
# Metrics
# ---------------------------------------------------

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Stations",
        len(df)
    )

with c2:
    st.metric(
        "Online",
        len(df)
    )

with c3:
    st.metric(
        "Offline",
        0
    )

with c4:
    st.metric(
        "Updated",
        datetime.now().strftime("%H:%M:%S")
    )

st.markdown("---")

# ---------------------------------------------------
# Station Table
# ---------------------------------------------------

if len(df) > 0:

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )

else:

    st.warning(
        "Waiting for station heartbeat..."
    )

# ---------------------------------------------------
# Auto Refresh
# ---------------------------------------------------

st.rerun()