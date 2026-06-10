"""
Colombia → Australia Travel Planner — Streamlit Web App
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow imports from project root when running via `streamlit run app/streamlit_app.py`
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

from src.routes import load_airports, load_routes, filter_routes, get_routes_dataframe, get_season_recommendation
from src.scoring import rank_routes, score_route
from src.map_builder import build_route_map, build_overview_map


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Colombia → Australia Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Data loading (cached) ─────────────────────────────────────────────────────
@st.cache_data
def get_data():
    airports = load_airports()
    routes = load_routes()
    return airports, routes


airports, routes = get_data()

COLOMBIA_ORIGINS = {"BOG": "Bogotá (BOG)", "MDE": "Medellín (MDE)", "CLO": "Cali (CLO)"}
AUSTRALIA_DESTINATIONS = {
    "BNE": "Brisbane (BNE)",
    "SYD": "Sídney (SYD)",
    "MEL": "Melbourne (MEL)",
    "PER": "Perth (PER)",
}
MONTH_NAMES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://flagcdn.com/w80/co.png", width=40)
    st.title("✈️ Filtros de búsqueda")

    origin = st.selectbox("🛫 Ciudad de salida (Colombia)", options=list(COLOMBIA_ORIGINS.keys()),
                          format_func=lambda x: COLOMBIA_ORIGINS[x])

    destination = st.selectbox("🛬 Ciudad de llegada (Australia)", options=list(AUSTRALIA_DESTINATIONS.keys()),
                                format_func=lambda x: AUSTRALIA_DESTINATIONS[x])

    max_stops = st.slider("Máximo de escalas", min_value=1, max_value=3, value=2)

    visa_filter = st.multiselect(
        "Complejidad de visa",
        options=["low", "medium", "high"],
        default=["low", "medium"],
        format_func=lambda x: {"low": "Fácil", "medium": "Media", "high": "Compleja"}[x],
    )

    tourist_filter = st.multiselect(
        "Potencial turístico",
        options=["low", "medium", "high"],
        default=["medium", "high"],
        format_func=lambda x: {"low": "Bajo", "medium": "Medio", "high": "Alto"}[x],
    )

    departure_month = st.selectbox(
        "🗓️ Mes de salida",
        options=list(MONTH_NAMES.keys()),
        format_func=lambda x: MONTH_NAMES[x],
        index=2,
    )

    st.markdown("---")
    st.caption("⚠️ **Disclaimer:** La información sobre visas es orientativa. Siempre verifica con fuentes oficiales antes de comprar tus tiquetes.")


# ── Main content ──────────────────────────────────────────────────────────────
st.title("🌏 Colombia → Australia Travel Planner")
st.markdown(
    "Explora rutas de vuelo inteligentes desde Colombia hacia Australia, "
    "con información sobre escalas, visas y recomendaciones por temporada."
)
st.warning(
    "⚠️ **Disclaimer migratorio:** Este proyecto es una herramienta de exploración y orientación. "
    "La información sobre visas y requisitos de tránsito puede cambiar en cualquier momento. "
    "**Siempre consulta fuentes oficiales** (embajadas, consulados, aerolíneas y portales de inmigración) "
    "antes de comprar tus tiquetes de viaje.",
    icon="🛂",
)

# ── Filter routes ─────────────────────────────────────────────────────────────
filtered = filter_routes(
    routes,
    origin=origin,
    destination=destination,
    max_stops=max_stops,
    visa_complexity=visa_filter if visa_filter else None,
    tourist_potential=tourist_filter if tourist_filter else None,
)
ranked = rank_routes(filtered, airports, departure_month)

# ── Metrics row ───────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Rutas encontradas", len(ranked))
col2.metric("Mejor puntaje", f"{ranked[0][1].total:.0f}/100" if ranked else "—")
col3.metric("Min. escalas", min(r.total_stops for r, _ in ranked) if ranked else "—")
col4.metric("Aeropuertos cubiertos", len(airports))

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_routes, tab_map, tab_compare, tab_airports = st.tabs(
    ["📋 Rutas", "🗺️ Mapa", "📊 Comparar", "🏢 Aeropuertos"]
)

# ────────────────────────────────────────────────────────────────── Tab: Rutas
with tab_routes:
    if not ranked:
        st.info("No se encontraron rutas con los filtros actuales. Prueba ajustando los filtros.")
    else:
        for route, breakdown in ranked:
            season_msg = get_season_recommendation(route, departure_month)
            with st.expander(
                f"{'⭐' if breakdown.total >= 85 else '✈️'} {route.name}  —  "
                f"Score: {breakdown.total:.0f}/100 ({breakdown.label})",
                expanded=(ranked.index((route, breakdown)) == 0),
            ):
                c1, c2, c3 = st.columns(3)
                c1.metric("Duración aprox.", f"{route.approximate_duration_hours}h")
                c2.metric("Escalas", route.total_stops)
                c3.metric("Potencial turístico", route.tourist_potential.capitalize())

                st.markdown(f"**Aerolíneas de ejemplo:** {', '.join(route.airlines_example)}")
                st.markdown(f"**Ruta completa:** {' → '.join(route.all_airports)}")
                st.markdown(f"**Temporada:** {season_msg}")
                st.markdown(f"**Notas de visa:** {route.visa_notes}")

                st.markdown("**Highlights:**")
                for h in route.highlights:
                    st.markdown(f"- {h}")

                # Score breakdown
                with st.container():
                    st.markdown("**Desglose del score:**")
                    bd = breakdown.as_dict()
                    cols = st.columns(len(bd))
                    for col, (k, v) in zip(cols, bd.items()):
                        col.metric(k, v)

# ─────────────────────────────────────────────────────────────────── Tab: Mapa
with tab_map:
    map_mode = st.radio("Tipo de mapa", ["Ruta específica", "Todas las rutas"], horizontal=True)

    if map_mode == "Ruta específica" and ranked:
        route_names = [r.name for r, _ in ranked]
        selected_name = st.selectbox("Selecciona una ruta", route_names)
        selected_route = next(r for r, _ in ranked if r.name == selected_name)

        fmap = build_route_map(selected_route, airports, animated=True)
        map_html = fmap._repr_html_()
        components.html(map_html, height=520, scrolling=False)

        st.markdown(f"**Ruta:** {selected_route.name}")
        st.markdown(f"**Escalas:** {' → '.join(selected_route.stopovers) if selected_route.stopovers else 'Ninguna'}")
    elif map_mode == "Todas las rutas":
        all_routes_to_show = [r for r, _ in ranked] if ranked else routes
        fmap = build_overview_map(all_routes_to_show, airports)
        map_html = fmap._repr_html_()
        components.html(map_html, height=520, scrolling=False)
    else:
        st.info("No hay rutas para mostrar con los filtros actuales.")

# ──────────────────────────────────────────────────────────────── Tab: Comparar
with tab_compare:
    if not ranked:
        st.info("No hay rutas para comparar.")
    else:
        df = get_routes_dataframe([r for r, _ in ranked])
        df.insert(0, "score_calculado", [round(b.total, 1) for _, b in ranked])
        df.insert(1, "calificacion", [b.label for _, b in ranked])

        column_rename = {
            "id": "ID", "name": "Ruta", "origin": "Origen", "destination": "Destino",
            "stopovers": "Escalas", "total_stops": "Nº Escalas",
            "duration_hours": "Duración (h)", "tourist_potential": "Turismo",
            "visa_complexity": "Visa", "score": "Score Base",
            "airlines": "Aerolíneas", "score_calculado": "Score", "calificacion": "Calificación",
        }
        df.rename(columns=column_rename, inplace=True)

        st.dataframe(
            df[["Score", "Calificación", "Ruta", "Nº Escalas", "Duración (h)", "Turismo", "Visa", "Aerolíneas"]],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### Distribución de scores")
        chart_data = pd.DataFrame({"Ruta": df["Ruta"], "Score": df["Score"]}).set_index("Ruta")
        st.bar_chart(chart_data)

# ─────────────────────────────────────────────────────────────── Tab: Aeropuertos
with tab_airports:
    st.markdown("### Base de datos de aeropuertos")
    airport_data = []
    for code, ap in airports.items():
        airport_data.append({
            "IATA": code,
            "Nombre": ap.name,
            "Ciudad": ap.city,
            "País": ap.country,
            "Turístico": "✅" if ap.is_tourist_stopover else "—",
            "Aerolíneas": ", ".join(ap.hub_airlines),
            "Notas visa": ap.visa_notes[:80] + "..." if len(ap.visa_notes) > 80 else ap.visa_notes,
        })
    st.dataframe(pd.DataFrame(airport_data), use_container_width=True, hide_index=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "colombia-australia-travel-planner v1.0 · "
    "Datos orientativos, no consejo migratorio oficial · "
    "Verifica siempre con fuentes oficiales antes de viajar."
)
