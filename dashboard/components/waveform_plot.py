import numpy as np
import matplotlib.pyplot as plt
import streamlit as st


class WaveformPlot:
    """
    Reusable waveform plotting component.

    Supports:
    - X-axis waveform
    - Y-axis waveform
    - Z-axis waveform
    - Single combined waveform

    Later this will directly display ADXL355 data
    received from the CRS.
    """

    def __init__(self):
        self.placeholder = st.empty()

    def _plot(self, x, y, title, color):

        fig, ax = plt.subplots(figsize=(12, 3.5))

        ax.plot(
            x,
            y,
            color=color,
            linewidth=1.2,
        )

        ax.set_title(title)
        ax.set_xlabel("Samples")
        ax.set_ylabel("Acceleration (g)")

        ax.grid(True)

        self.placeholder.pyplot(fig)

        plt.close(fig)

    # --------------------------------------------------
    # Plot single waveform
    # --------------------------------------------------

    def plot_single(
        self,
        samples,
        title="Seismic Waveform",
        color="blue",
    ):

        x = np.arange(len(samples))

        self._plot(
            x,
            samples,
            title,
            color,
        )

    # --------------------------------------------------
    # Plot X Axis
    # --------------------------------------------------

    def plot_x(self, samples):

        self.plot_single(
            samples,
            title="X-Axis Waveform",
            color="blue",
        )

    # --------------------------------------------------
    # Plot Y Axis
    # --------------------------------------------------

    def plot_y(self, samples):

        self.plot_single(
            samples,
            title="Y-Axis Waveform",
            color="green",
        )

    # --------------------------------------------------
    # Plot Z Axis
    # --------------------------------------------------

    def plot_z(self, samples):

        self.plot_single(
            samples,
            title="Z-Axis Waveform",
            color="red",
        )

    # --------------------------------------------------
    # Plot All Three Axes
    # --------------------------------------------------

    def plot_xyz(
        self,
        x_samples,
        y_samples,
        z_samples,
    ):

        samples = np.arange(len(x_samples))

        fig, axes = plt.subplots(
            3,
            1,
            figsize=(12, 8),
            sharex=True,
        )

        axes[0].plot(samples, x_samples, color="blue")
        axes[0].set_title("X-Axis")

        axes[1].plot(samples, y_samples, color="green")
        axes[1].set_title("Y-Axis")

        axes[2].plot(samples, z_samples, color="red")
        axes[2].set_title("Z-Axis")

        for ax in axes:
            ax.grid(True)
            ax.set_ylabel("g")

        axes[-1].set_xlabel("Samples")

        plt.tight_layout()

        self.placeholder.pyplot(fig)

        plt.close(fig)

    # --------------------------------------------------
    # Demo waveform (for testing)
    # --------------------------------------------------

    def demo(self):

        samples = np.arange(300)

        waveform = (
            np.sin(samples / 12)
            + np.random.normal(0, 0.15, 300)
        )

        self.plot_single(
            waveform,
            title="Demo Seismic Signal",
            color="blue",
        )