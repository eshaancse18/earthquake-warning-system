import streamlit as st
import pandas as pd

from services.crs_service import crs_service

st.set_page_config(
    page_title="Earthquake Event History",
    layout="wide"
)

st.title("📜 Earthquake Event History")

st.markdown("---")

# --------------------------------------------------
# Fetch Events from CRS
# --------------------------------------------------

try:
    events = crs_service.get_events()
except Exception as e:
    st.error(f"Database Error: {e}")
    st.stop()

# --------------------------------------------------
# No Events
# --------------------------------------------------

if not events:
    st.warning("No earthquake events found.")
    st.stop()

# --------------------------------------------------
# DataFrame
# --------------------------------------------------

df = pd.DataFrame(events)

# --------------------------------------------------
# Metrics
# --------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Events",
        len(df)
    )

with col2:

    if "magnitude" in df.columns:

        st.metric(
            "Maximum Magnitude",
            round(
                df["magnitude"].max(),
                2
            )
        )

with col3:

    if "confidence" in df.columns:

        st.metric(
            "Highest Confidence",
            f"{int(df['confidence'].max())}%"
        )

with col4:

    if "status" in df.columns:

        confirmed = (
            df["status"]
            .astype(str)
            .str.lower()
            .eq("confirmed")
            .sum()
        )

        st.metric(
            "Confirmed",
            confirmed
        )

st.markdown("---")

# --------------------------------------------------
# Search
# --------------------------------------------------

search = st.text_input(
    "🔍 Search Event ID"
)

if search and "event_id" in df.columns:

    df = df[
        df["event_id"]
        .astype(str)
        .str.contains(
            search,
            case=False
        )
    ]

# --------------------------------------------------
# Sort
# --------------------------------------------------

if "event_time" in df.columns:

    df = df.sort_values(
        by="event_time",
        ascending=False
    )

# --------------------------------------------------
# Table
# --------------------------------------------------

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)