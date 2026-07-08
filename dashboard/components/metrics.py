import streamlit as st


def show_system_metrics(
    total_stations,
    online_stations,
    active_events,
    mqtt_messages,
):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📡 Stations",
            value=total_stations,
        )

    with col2:
        st.metric(
            label="🟢 Online",
            value=online_stations,
        )

    with col3:
        st.metric(
            label="🌍 Active Events",
            value=active_events,
        )

    with col4:
        st.metric(
            label="📨 MQTT Messages",
            value=mqtt_messages,
        )


def show_station_metrics(cpu, ram, temperature, disk):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="CPU Usage",
            value=f"{cpu:.1f}%"
        )

    with col2:
        st.metric(
            label="RAM Usage",
            value=f"{ram:.1f}%"
        )

    with col3:
        st.metric(
            label="Temperature",
            value=f"{temperature:.1f} °C"
        )

    with col4:
        st.metric(
            label="Disk Usage",
            value=f"{disk:.1f}%"
        )


def show_event_metrics(
    magnitude,
    confidence,
    stations_triggered,
    status,
):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Magnitude",
            value=f"{magnitude:.1f}"
        )

    with col2:
        st.metric(
            label="Confidence",
            value=f"{confidence}%"
        )

    with col3:
        st.metric(
            label="Triggered Stations",
            value=stations_triggered
        )

    with col4:
        st.metric(
            label="Status",
            value=status
        )


def show_health_progress(cpu, ram, disk):
    st.subheader("Resource Utilization")

    st.write("CPU")
    st.progress(min(cpu / 100, 1.0))

    st.write("RAM")
    st.progress(min(ram / 100, 1.0))

    st.write("Disk")
    st.progress(min(disk / 100, 1.0))


def show_connection_status(
    mqtt_connected,
    database_connected,
    crs_running,
):
    st.subheader("System Status")

    mqtt = "🟢 Connected" if mqtt_connected else "🔴 Disconnected"
    db = "🟢 Connected" if database_connected else "🔴 Disconnected"
    crs = "🟢 Running" if crs_running else "🔴 Offline"

    col1, col2, col3 = st.columns(3)

    with col1:
        st.success(mqtt)

    with col2:
        st.success(db)

    with col3:
        st.success(crs)