import streamlit as st
import pandas as pd
import plotly.express as px

from services.crs_service import crs_service

st.set_page_config(
    page_title="Analytics",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Earthquake Analytics Dashboard")

st.markdown("---")

# -------------------------------------------------------
# Load Data
# -------------------------------------------------------

try:

    events = crs_service.get_events()

    stations = crs_service.get_stations()

    health = crs_service.get_station_health()

except Exception as e:

    st.error(e)

    st.stop()

if len(events) == 0:

    st.warning("No earthquake events available.")

    st.stop()

df = pd.DataFrame(events)

# -------------------------------------------------------
# Summary Metrics
# -------------------------------------------------------

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "Total Events",
        len(df)
    )

with c2:

    st.metric(
        "Stations",
        len(stations)
    )

with c3:

    if "magnitude" in df.columns:

        st.metric(
            "Largest Magnitude",
            round(
                df["magnitude"].max(),
                2
            )
        )

with c4:

    if "confidence" in df.columns:

        st.metric(
            "Average Confidence",
            f"{round(df['confidence'].mean(),1)}%"
        )

st.markdown("---")

# -------------------------------------------------------
# Magnitude Distribution
# -------------------------------------------------------

if "magnitude" in df.columns:

    st.subheader("Magnitude Distribution")

    fig = px.histogram(

        df,

        x="magnitude",

        nbins=10,

        title="Earthquake Magnitude Distribution"

    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# -------------------------------------------------------
# Confidence Distribution
# -------------------------------------------------------

if "confidence" in df.columns:

    st.subheader("Detection Confidence")

    fig = px.box(

        df,

        y="confidence",

        title="Confidence Distribution"

    )

    st.plotly_chart(

        fig,

        use_container_width=True

    )

# -------------------------------------------------------
# Magnitude Trend
# -------------------------------------------------------

if (
    "event_time" in df.columns
    and
    "magnitude" in df.columns
):

    st.subheader("Magnitude Trend")

    fig = px.line(

        df.sort_values("event_time"),

        x="event_time",

        y="magnitude",

        markers=True

    )

    st.plotly_chart(

        fig,

        use_container_width=True

    )

# -------------------------------------------------------
# Station Event Count
# -------------------------------------------------------

if "station_id" in df.columns:

    st.subheader("Events per Station")

    station_count = (

        df.groupby("station_id")

        .size()

        .reset_index(name="Events")

    )

    fig = px.bar(

        station_count,

        x="station_id",

        y="Events"

    )

    st.plotly_chart(

        fig,

        use_container_width=True

    )

# -------------------------------------------------------
# Raw Dataset
# -------------------------------------------------------

st.markdown("---")

st.subheader("Raw Event Data")

st.dataframe(

    df,

    use_container_width=True,

    hide_index=True

)