import streamlit as st
from datetime import datetime
from components.alert_banner import AlertBanner

from services.crs_service import crs_service

st.set_page_config(
    page_title="Earthquake Early Warning System",
    page_icon="🌍",
    layout="wide",
)

st.title("🌍 Earthquake Early Warning System")

st.caption("Central Receiving Server Dashboard")

st.markdown("---")

# ---------------------------------------------------------
# Fetch Backend Data
# ---------------------------------------------------------

try:

    stations = crs_service.get_stations()

    events = crs_service.get_events()

    health = crs_service.get_station_health()

    mqtt_logs = crs_service.get_mqtt_logs()

    latest_event = crs_service.get_latest_event()
    AlertBanner.show(latest_event)

except Exception as e:

    st.error(str(e))

    st.stop()

# ---------------------------------------------------------
# Dashboard Metrics
# ---------------------------------------------------------

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "Stations",
        len(stations)
    )

with c2:

    st.metric(
        "Events",
        len(events)
    )

with c3:

    st.metric(
        "MQTT Messages",
        len(mqtt_logs)
    )

with c4:

    st.metric(
        "Broker",
        "🟢 Online"
        if crs_service.mqtt_connected()
        else "🔴 Offline"
    )

st.markdown("---")

# ---------------------------------------------------------
# Latest Event
# ---------------------------------------------------------

st.subheader("Latest Earthquake")

if latest_event is None:

    st.info("No earthquake detected.")

else:

    col1, col2 = st.columns(2)

    with col1:

        st.write(
            f"**Magnitude:** "
            f"{latest_event.get('magnitude','-')}"
        )

        st.write(
            f"**Confidence:** "
            f"{latest_event.get('confidence','-')}%"
        )

        st.write(
            f"**Station:** "
            f"{latest_event.get('station_id','-')}"
        )

    with col2:

        st.write(
            f"**Latitude:** "
            f"{latest_event.get('latitude','-')}"
        )

        st.write(
            f"**Longitude:** "
            f"{latest_event.get('longitude','-')}"
        )

        st.write(
            f"**Time:** "
            f"{latest_event.get('timestamp','-')}"
        )

st.markdown("---")

# ---------------------------------------------------------
# Connected Stations
# ---------------------------------------------------------

st.subheader("Connected Stations")

if len(health) == 0:

    st.warning("No station health reports received.")

else:

    for station in health:

        cpu = station.get("cpu", "-")
        ram = station.get("ram", "-")
        temp = station.get("temperature", "-")

        with st.expander(
            station.get(
                "station_id",
                "Unknown"
            )
        ):

            st.write(f"CPU : {cpu}%")
            st.write(f"RAM : {ram}%")
            st.write(f"Temperature : {temp} °C")

st.markdown("---")

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------

st.caption(
    f"Last Updated : "
    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)