import streamlit as st
import pandas as pd
from datetime import datetime

from services.crs_service import crs_service

st.set_page_config(
    page_title="MQTT Monitor",
    layout="wide"
)

st.title("📡 Live MQTT Message Monitor")

st.markdown("---")

# -------------------------------------------------------
# Get Messages
# -------------------------------------------------------

try:
    messages = crs_service.get_mqtt_logs()

except Exception as e:

    st.error(f"MQTT Error : {e}")

    st.stop()

# -------------------------------------------------------
# No Messages
# -------------------------------------------------------

if len(messages) == 0:

    st.info("Waiting for MQTT messages...")

    st.stop()

# -------------------------------------------------------
# Convert for Display
# -------------------------------------------------------

rows = []

for message in messages:

    payload = message.get("payload", {})

    rows.append({

        "Time": datetime.now().strftime("%H:%M:%S"),

        "Topic": message.get(
            "topic",
            "-"
        ),

        "Station": payload.get(
            "station_id",
            "-"
        ),

        "Packet Type": payload.get(
            "packet_type",
            "-"
        ),

        "Packet ID": payload.get(
            "packet_id",
            "-"
        )
    })

df = pd.DataFrame(rows)

# -------------------------------------------------------
# Dashboard Metrics
# -------------------------------------------------------

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "Messages",
        len(df)
    )

with c2:

    st.metric(
        "Broker",
        "Connected"
        if crs_service.mqtt_connected()
        else "Offline"
    )

with c3:

    st.metric(
        "Topics",
        df["Topic"].nunique()
    )

with c4:

    st.metric(
        "Stations",
        df["Station"].nunique()
    )

st.markdown("---")

# -------------------------------------------------------
# Filter
# -------------------------------------------------------

topics = ["All"]

topics.extend(
    sorted(
        df["Topic"].unique().tolist()
    )
)

selected = st.selectbox(
    "Topic Filter",
    topics
)

if selected != "All":

    df = df[
        df["Topic"] == selected
    ]

# -------------------------------------------------------
# MQTT Table
# -------------------------------------------------------

st.dataframe(

    df,

    use_container_width=True,

    hide_index=True

)

# -------------------------------------------------------
# Latest Packet
# -------------------------------------------------------

st.markdown("---")

st.subheader("Latest MQTT Packet")

latest = messages[0]

st.json(latest["payload"])