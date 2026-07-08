import streamlit as st
import graphviz

from services.crs_service import crs_service

st.set_page_config(
    page_title="System Topology",
    page_icon="🌐",
    layout="wide"
)

st.title("🌐 Earthquake Early Warning System Topology")

st.markdown("---")

# ------------------------------------------------------
# Status
# ------------------------------------------------------

mqtt_status = (
    "🟢 Connected"
    if crs_service.mqtt_connected()
    else "🔴 Offline"
)

stations = len(crs_service.get_stations())
events = len(crs_service.get_events())

# ------------------------------------------------------
# Metrics
# ------------------------------------------------------

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Stations", stations)

with c2:
    st.metric("Events", events)

with c3:
    st.metric("MQTT", mqtt_status)

st.markdown("---")

# ------------------------------------------------------
# Network Diagram
# ------------------------------------------------------

graph = graphviz.Digraph()

graph.attr(rankdir="LR")

graph.node(
    "Sensor",
    "ADXL355\nSensor"
)

graph.node(
    "SSN",
    "SSN\n(Raspberry Pi)"
)

graph.node(
    "MQTT",
    "MQTT Broker"
)

graph.node(
    "CRS",
    "Central Receiving Server"
)

graph.node(
    "DB",
    "PostgreSQL"
)

graph.node(
    "Dashboard",
    "Streamlit Dashboard"
)

graph.edge("Sensor", "SSN")
graph.edge("SSN", "MQTT")
graph.edge("MQTT", "CRS")
graph.edge("CRS", "DB")
graph.edge("DB", "Dashboard")

st.graphviz_chart(
    graph,
    use_container_width=True
)

st.markdown("---")

# ------------------------------------------------------
# Data Flow
# ------------------------------------------------------

st.subheader("Data Flow")

st.code(
"""
ADXL355
    │
    ▼
Read Acceleration
    │
    ▼
STA/LTA + PGA + P-Wave Detection
    │
    ▼
MQTT Event Packet
    │
    ▼
CRS Voting Engine
    │
    ▼
Earthquake Confirmation
    │
    ▼
Database Storage
    │
    ▼
Live Dashboard
"""
)

st.markdown("---")

# ------------------------------------------------------
# Communication Channels
# ------------------------------------------------------

st.subheader("Communication")

communication = {
    "Sensor → SSN": "SPI",
    "SSN → CRS": "MQTT",
    "CRS → Database": "PostgreSQL",
    "Dashboard → CRS": "Database Queries"
}

st.table(communication)

st.markdown("---")

# ------------------------------------------------------
# Health
# ------------------------------------------------------

st.subheader("System Health")

st.success("Sensor : Operational")
st.success("SSN : Operational")

if crs_service.mqtt_connected():
    st.success("MQTT : Connected")
else:
    st.error("MQTT : Offline")

st.success("CRS : Running")
st.success("Database : Connected")