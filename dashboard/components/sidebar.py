import streamlit as st
from datetime import datetime


def render_sidebar():
    with st.sidebar:
        st.title("🌍 Earthquake EEWS")

        st.markdown("---")

        st.subheader("System")

        st.success("🟢 CRS Online")
        st.success("🟢 MQTT Connected")
        st.success("🟢 PostgreSQL Connected")

        st.markdown("---")

        st.subheader("Navigation")

        st.page_link("app.py", label="🏠 Home")
        st.page_link("pages/1_Live_Stations.py", label="📡 Live Stations")
        st.page_link("pages/2_Real_Time_Waveforms.py", label="📈 Waveforms")
        st.page_link("pages/3_Earthquake_Map.py", label="🌍 Earthquake Map")
        st.page_link("pages/4_Event_History.py", label="📜 Event History")
        st.page_link("pages/5_MQTT_Log.py", label="📡 MQTT Log")
        st.page_link("pages/6_System_Health.py", label="❤️ System Health")

        st.markdown("---")

        st.subheader("Dashboard Info")

        st.write(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        st.caption("Earthquake Early Warning System")
        st.caption("Version 1.0")

        st.markdown("---")

        st.info(
            """
            **Monitoring**
            - Sensor Stations
            - MQTT Messages
            - Earthquake Events
            - CRS Health
            """
        )