import folium
from streamlit_folium import st_folium


def render_map(stations, event=None):
    """
    Render an interactive earthquake monitoring map.

    Parameters
    ----------
    stations : list
        Example:
        [
            {
                "station_id": "SSN_001",
                "latitude": 28.6139,
                "longitude": 77.2090,
                "status": "Online"
            }
        ]

    event : dict | None
        Example:
        {
            "latitude": 28.6200,
            "longitude": 77.2150,
            "magnitude": 4.6,
            "confidence": 97
        }
    """

    # ---------------------------------------------------------
    # Default map center
    # ---------------------------------------------------------

    if stations:
        center_lat = stations[0]["latitude"]
        center_lon = stations[0]["longitude"]
    else:
        center_lat = 28.6139
        center_lon = 77.2090

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        control_scale=True,
    )

    # ---------------------------------------------------------
    # Station Markers
    # ---------------------------------------------------------

    for station in stations:

        status = station.get("status", "Offline")

        color = "green" if status == "Online" else "red"

        popup = f"""
        <b>{station['station_id']}</b><br>
        Status: {status}<br>
        Latitude: {station['latitude']}<br>
        Longitude: {station['longitude']}
        """

        folium.Marker(
            location=[
                station["latitude"],
                station["longitude"],
            ],
            tooltip=station["station_id"],
            popup=popup,
            icon=folium.Icon(
                color=color,
                icon="signal",
                prefix="fa",
            ),
        ).add_to(m)

    # ---------------------------------------------------------
    # Earthquake Event
    # ---------------------------------------------------------

    if event is not None:

        magnitude = event.get("magnitude", 0)
        confidence = event.get("confidence", 0)

        popup = f"""
        <b>Earthquake Detected</b><br>
        Magnitude: {magnitude}<br>
        Confidence: {confidence}%<br>
        """

        folium.Marker(
            location=[
                event["latitude"],
                event["longitude"],
            ],
            tooltip="Earthquake",
            popup=popup,
            icon=folium.Icon(
                color="red",
                icon="warning-sign",
            ),
        ).add_to(m)

        # Detection Radius
        folium.Circle(
            location=[
                event["latitude"],
                event["longitude"],
            ],
            radius=2000,
            color="red",
            fill=True,
            fill_color="red",
            fill_opacity=0.25,
            weight=2,
        ).add_to(m)

    # ---------------------------------------------------------
    # Display
    # ---------------------------------------------------------

    st_folium(
        m,
        width=None,
        height=650,
        returned_objects=[],
    )