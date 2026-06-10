"""
Interactive map generation using Folium.

Color convention:
  - Origin (Colombia)  → green
  - Stopover           → orange
  - Destination (AU)   → red/blue
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import folium
from folium.plugins import AntPath

from src.routes import Airport, Route


_COLORS = {
    "origin": "#27ae60",
    "stopover": "#e67e22",
    "destination": "#2980b9",
}

_RADIUS = {
    "origin": 10,
    "stopover": 8,
    "destination": 10,
}


def _airport_popup(airport: Airport, role: str) -> str:
    role_label = {"origin": "🛫 Origen", "stopover": "🔄 Escala", "destination": "🛬 Destino"}
    tourist = "✅ Sí" if airport.is_tourist_stopover else "—"
    airlines = ", ".join(airport.hub_airlines) if airport.hub_airlines else "N/A"
    return f"""
    <div style="font-family: Arial; min-width:220px">
        <b>{role_label.get(role, role)} — {airport.iata_code}</b><br>
        <b>{airport.name}</b><br>
        🏙️ {airport.city}, {airport.country}<br>
        ✈️ Aerolíneas: {airlines}<br>
        🗺️ Turístico: {tourist}<br>
        <hr style="margin:6px 0">
        <small style="color:#555">⚠️ {airport.visa_notes}</small>
    </div>
    """.strip()


def build_route_map(
    route: Route,
    airports: dict[str, Airport],
    output_path: Optional[Path] = None,
    animated: bool = True,
) -> folium.Map:
    """
    Build a Folium map for a single route.

    Parameters
    ----------
    route:       The route to visualise.
    airports:    Full airport lookup dict.
    output_path: If provided, save the HTML map here.
    animated:    Use AntPath animation for the route line.
    """
    all_codes = route.all_airports
    coords = [
        (airports[c].latitude, airports[c].longitude)
        for c in all_codes
        if c in airports
    ]

    if not coords:
        raise ValueError("No valid airport coordinates found for route.")

    center_lat = sum(c[0] for c in coords) / len(coords)
    center_lon = sum(c[1] for c in coords) / len(coords)

    fmap = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=3,
        tiles="CartoDB positron",
    )

    # Draw route line
    if animated:
        AntPath(
            locations=coords,
            color="#e74c3c",
            weight=3,
            opacity=0.8,
            delay=800,
        ).add_to(fmap)
    else:
        folium.PolyLine(
            locations=coords,
            color="#e74c3c",
            weight=2.5,
            opacity=0.7,
            dash_array="8 4",
        ).add_to(fmap)

    # Add airport markers
    for idx, code in enumerate(all_codes):
        airport = airports.get(code)
        if not airport:
            continue

        if idx == 0:
            role = "origin"
        elif idx == len(all_codes) - 1:
            role = "destination"
        else:
            role = "stopover"

        folium.CircleMarker(
            location=[airport.latitude, airport.longitude],
            radius=_RADIUS[role],
            color=_COLORS[role],
            fill=True,
            fill_color=_COLORS[role],
            fill_opacity=0.85,
            popup=folium.Popup(_airport_popup(airport, role), max_width=300),
            tooltip=f"{airport.iata_code} — {airport.city}",
        ).add_to(fmap)

    # Legend
    legend_html = """
    <div style="position:fixed;bottom:30px;left:30px;z-index:1000;
                background:white;padding:12px 16px;border-radius:8px;
                box-shadow:0 2px 8px rgba(0,0,0,0.2);font-family:Arial;font-size:13px">
        <b>🗺️ Leyenda</b><br>
        <span style="color:#27ae60">●</span> Origen (Colombia)<br>
        <span style="color:#e67e22">●</span> Escala<br>
        <span style="color:#2980b9">●</span> Destino (Australia)
    </div>
    """
    fmap.get_root().html.add_child(folium.Element(legend_html))

    if output_path:
        fmap.save(str(output_path))

    return fmap


def build_overview_map(
    routes: list[Route],
    airports: dict[str, Airport],
    output_path: Optional[Path] = None,
) -> folium.Map:
    """
    Build a single map showing all routes as light lines.
    """
    fmap = folium.Map(location=[20, 100], zoom_start=2, tiles="CartoDB positron")

    colors = [
        "#e74c3c", "#3498db", "#2ecc71", "#9b59b6",
        "#f39c12", "#1abc9c", "#e67e22", "#e91e63",
        "#00bcd4", "#ff5722",
    ]

    for idx, route in enumerate(routes):
        all_codes = route.all_airports
        coords = [
            (airports[c].latitude, airports[c].longitude)
            for c in all_codes if c in airports
        ]
        if len(coords) < 2:
            continue

        color = colors[idx % len(colors)]
        folium.PolyLine(
            locations=coords,
            color=color,
            weight=2,
            opacity=0.6,
            tooltip=route.name,
        ).add_to(fmap)

        # Mark only origin and destination with small dots
        for i, code in enumerate([all_codes[0], all_codes[-1]]):
            airport = airports.get(code)
            if airport:
                folium.CircleMarker(
                    location=[airport.latitude, airport.longitude],
                    radius=5,
                    color=color,
                    fill=True,
                    fill_opacity=0.8,
                    tooltip=f"{airport.iata_code} — {airport.city}",
                ).add_to(fmap)

    if output_path:
        fmap.save(str(output_path))

    return fmap
