import streamlit as st
import pandas as pd



class EventTable:
    """
    Reusable Event History Table Component

    Supports:
    - Search by Event ID
    - Status filter
    - Magnitude filter
    - Sort by newest first
    """

    def __init__(self):
        pass

    def render(self, events):

        if not events:
            st.info("No earthquake events available.")
            return

        df = pd.DataFrame(events)

        st.subheader("📜 Earthquake Events")

        # -----------------------------
        # Filters
        # -----------------------------

        col1, col2, col3 = st.columns(3)

        with col1:
            search = st.text_input(
                "Search Event ID",
                placeholder="EQ0001"
            )

        with col2:

            status_options = ["All"]

            if "status" in df.columns:
                status_options.extend(
                    sorted(df["status"].dropna().unique().tolist())
                )

            status = st.selectbox(
                "Status",
                status_options
            )

        with col3:

            if "magnitude" in df.columns:

                min_mag = float(df["magnitude"].min())
                max_mag = float(df["magnitude"].max())

                magnitude = st.slider(
                    "Minimum Magnitude",
                    min_mag,
                    max_mag,
                    min_mag,
                    step=0.1,
                )
            else:
                magnitude = None

        # -----------------------------
        # Apply Filters
        # -----------------------------

        filtered = df.copy()

        if search and "event_id" in filtered.columns:
            filtered = filtered[
                filtered["event_id"]
                .astype(str)
                .str.contains(search, case=False)
            ]

        if (
            status != "All"
            and "status" in filtered.columns
        ):
            filtered = filtered[
                filtered["status"] == status
            ]

        if (
            magnitude is not None
            and "magnitude" in filtered.columns
        ):
            filtered = filtered[
                filtered["magnitude"] >= magnitude
            ]

        # -----------------------------
        # Sort
        # -----------------------------

        if "event_time" in filtered.columns:
            filtered = filtered.sort_values(
                by="event_time",
                ascending=False,
            )

        # -----------------------------
        # Metrics
        # -----------------------------

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric(
                "Total Events",
                len(filtered),
            )

        with c2:
            if "magnitude" in filtered.columns:
                st.metric(
                    "Largest Magnitude",
                    round(
                        filtered["magnitude"].max(),
                        2,
                    ),
                )

        with c3:
            if "confidence" in filtered.columns:
                st.metric(
                    "Highest Confidence",
                    f"{int(filtered['confidence'].max())}%"
                )

        with c4:
            if "status" in filtered.columns:
                confirmed = (
                    filtered["status"]
                    .astype(str)
                    .str.lower()
                    .eq("confirmed")
                    .sum()
                )

                st.metric(
                    "Confirmed",
                    confirmed,
                )

        st.markdown("---")

        # -----------------------------
        # Display Table
        # -----------------------------

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
        )

    # ---------------------------------
    # Helper Method
    # ---------------------------------

    @staticmethod
    def render_empty():
        st.warning("No earthquake events found.")