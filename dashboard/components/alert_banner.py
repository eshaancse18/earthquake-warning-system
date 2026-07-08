import streamlit as st

# from components.dashboard_header import DashboardHeader
# from services.crs_service import crs_service

# DashboardHeader.render(
#     mqtt_connected=crs_service.mqtt_connected(),
#     station_count=len(crs_service.get_stations()),
#     event_count=len(crs_service.get_events())
# )

class AlertBanner:

    @staticmethod
    def show(event):

        if event is None:

            st.success("✅ No active earthquake alerts.")

            return

        magnitude = event.get("magnitude", "--")

        confidence = event.get("confidence", "--")

        station = event.get("station_id", "--")

        latitude = event.get("latitude", "--")

        longitude = event.get("longitude", "--")

        st.error(
            f"""
🚨 EARTHQUAKE DETECTED

Magnitude : {magnitude}

Confidence : {confidence}%

Detected By : {station}

Latitude : {latitude}

Longitude : {longitude}
"""
        )

    @staticmethod
    def warning(message):

        st.warning(message)

    @staticmethod
    def info(message):

        st.info(message)

    @staticmethod
    def success(message):

        st.success(message)