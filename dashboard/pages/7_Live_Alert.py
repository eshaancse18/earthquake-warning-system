import streamlit as st
from datetime import datetime

from services.crs_service import crs_service

st.set_page_config(
    page_title="Live Alert",
    page_icon="🚨",
    layout="wide"
)

st.title("🚨 Live Earthquake Alert")

st.markdown("---")

try:
    latest_event = crs_service.get_latest_event()

except Exception as e:
    st.error(e)
    st.stop()

# ----------------------------------------------------
# No Event
# ----------------------------------------------------

if latest_event is None:

    st.success("✅ No active earthquake alerts.")

    st.info("System is continuously monitoring seismic activity.")

    st.stop()

# ----------------------------------------------------
# Alert Banner
# ----------------------------------------------------

st.error(
    "🚨 EARTHQUAKE DETECTED"
)

# ----------------------------------------------------
# Metrics
# ----------------------------------------------------

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Magnitude",
        latest_event.get(
            "magnitude",
            "-"
        )
    )

with c2:
    st.metric(
        "Confidence",
        f"{latest_event.get('confidence','-')}%"
    )

with c3:
    st.metric(
        "Station",
        latest_event.get(
            "station_id",
            "-"
        )
    )

with c4:
    st.metric(
        "Status",
        latest_event.get(
            "status",
            "Confirmed"
        )
    )

st.markdown("---")

# ----------------------------------------------------
# Details
# ----------------------------------------------------

left, right = st.columns(2)

with left:

    st.subheader("📍 Location")

    st.write(
        f"Latitude : {latest_event.get('latitude','-')}"
    )

    st.write(
        f"Longitude : {latest_event.get('longitude','-')}"
    )

with right:

    st.subheader("⏱ Event Information")

    st.write(
        f"Time : {latest_event.get('timestamp','-')}"
    )

    st.write(
        f"Event ID : {latest_event.get('event_id','-')}"
    )

st.markdown("---")

# ----------------------------------------------------
# Raw Packet
# ----------------------------------------------------

st.subheader("Raw Event Packet")

st.json(latest_event)

st.caption(
    f"Last Updated : {datetime.now().strftime('%H:%M:%S')}"
)