import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="System Health",
    layout="wide"
)

st.title("❤️ System Health")

st.markdown("---")

# ---------------------------------------------------
# Temporary Health Data
# Later this comes from CRS / PostgreSQL
# ---------------------------------------------------

health = {
    "Station": "SSN_001",
    "CPU": 23,
    "RAM": 41,
    "Temperature": 47,
    "Disk": 36,
    "MQTT": "Connected",
    "Database": "Connected",
    "CRS": "Running",
    "Uptime": "02:14:36"
}

# ---------------------------------------------------
# Top Metrics
# ---------------------------------------------------

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("CPU Usage", f"{health['CPU']}%")

with c2:
    st.metric("RAM Usage", f"{health['RAM']}%")

with c3:
    st.metric("Temperature", f"{health['Temperature']} °C")

with c4:
    st.metric("Disk Usage", f"{health['Disk']}%")

st.markdown("---")

# ---------------------------------------------------
# Progress Bars
# ---------------------------------------------------

st.subheader("Resource Utilization")

st.write("CPU")
st.progress(health["CPU"] / 100)

st.write("RAM")
st.progress(health["RAM"] / 100)

st.write("Disk")
st.progress(health["Disk"] / 100)

st.markdown("---")

# ---------------------------------------------------
# Service Status
# ---------------------------------------------------

status = pd.DataFrame({
    "Service": [
        "MQTT Broker",
        "CRS",
        "PostgreSQL"
    ],
    "Status": [
        health["MQTT"],
        health["CRS"],
        health["Database"]
    ]
})

st.subheader("Service Status")

st.dataframe(
    status,
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

st.subheader("Station Information")

info = pd.DataFrame({
    "Property": [
        "Station ID",
        "Uptime"
    ],
    "Value": [
        health["Station"],
        health["Uptime"]
    ]
})

st.dataframe(
    info,
    use_container_width=True,
    hide_index=True
)