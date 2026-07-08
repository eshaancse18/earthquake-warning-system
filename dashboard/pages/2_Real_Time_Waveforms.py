import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time

st.set_page_config(
    page_title="Real-Time Waveforms",
    layout="wide"
)

st.title("📈 Real-Time Seismic Waveforms")

st.markdown("---")

st.write("Live waveform from seismic station.")

# Placeholder for updating plot
chart = st.empty()

# X-axis (last 10 seconds at 100 samples)
x = np.arange(100)

while True:

    # Simulated seismic signal
    y = (
        np.sin(x / 8)
        + np.random.normal(0, 0.15, 100)
    )

    fig, ax = plt.subplots(figsize=(12,4))

    ax.plot(x, y)

    ax.set_xlabel("Samples")
    ax.set_ylabel("Acceleration")
    ax.set_title("Station SSN_001")

    ax.grid(True)

    chart.pyplot(fig)

    plt.close(fig)

    time.sleep(0.2)