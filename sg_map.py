#!/usr/bin/env python3
"""SGMap page — overlay Singapore's outline on any city to compare physical scale."""

from __future__ import annotations

import math

import folium
import requests
import streamlit as st
from folium.plugins import Geocoder
from geopy.geocoders import Nominatim
from shapely.affinity import rotate, scale, translate
from shapely.geometry import MultiPolygon, Polygon, shape
from streamlit_folium import st_folium

GEOJSON_URLS = [
    "https://raw.githubusercontent.com/cheeaun/singapore-boundary/master/singapore.geojson",
    "https://raw.githubusercontent.com/cheeaun/singapore-boundary/main/singapore.geojson",
    "https://raw.githubusercontent.com/yinshanyang/singapore/master/maps/0-country.geojson",
]


@st.cache_data(show_spinner="Loading Singapore boundary…")
def fetch_sg_geometry():
    """Fetch and simplify the Singapore GeoJSON boundary, trying fallback URLs."""
    last_err = None
    for url in GEOJSON_URLS:
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if data["type"] == "FeatureCollection":
                geom_dict = data["features"][0]["geometry"]
            elif data["type"] == "Feature":
                geom_dict = data["geometry"]
            else:
                geom_dict = data
            sg_shape = shape(geom_dict)
            simplified = sg_shape.simplify(0.001, preserve_topology=True)
            if isinstance(simplified, MultiPolygon):
                simplified = max(simplified.geoms, key=lambda p: p.area)
            return simplified
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"Could not fetch Singapore boundary from any source. Last error: {last_err}")


def geocode_city(city_name: str):
    """Return (lat, lon) for *city_name*, or None if not found."""
    geolocator = Nominatim(user_agent="sg_scale_map_v1")
    location = geolocator.geocode(city_name, timeout=10)
    if location:
        return location.latitude, location.longitude
    return None


def transform_geometry(sg_geom, sg_center_latlon, target_latlon, rotation_deg):
    sg_lat, sg_lon = sg_center_latlon
    tgt_lat, tgt_lon = target_latlon

    cos_sg = math.cos(math.radians(sg_lat))
    cos_tgt = math.cos(math.radians(max(-89.9, min(89.9, tgt_lat))))
    lat_correction = cos_sg / cos_tgt if cos_tgt != 0 else 1.0

    centered = translate(sg_geom, xoff=-sg_lon, yoff=-sg_lat)
    corrected = scale(centered, xfact=lat_correction, yfact=1.0, origin=(0, 0))
    rotated = rotate(corrected, rotation_deg, origin=(0, 0), use_radians=False)
    return translate(rotated, xoff=tgt_lon, yoff=tgt_lat)


def add_geom_to_map(geom, folium_map, color="#EF4444", fill_opacity=0.35):
    """Add a shapely Polygon or MultiPolygon to a folium map."""
    polys = list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]
    for poly in polys:
        # shapely coords are (lon, lat); folium needs (lat, lon)
        exterior = [(lat, lon) for lon, lat in poly.exterior.coords]
        folium.Polygon(
            locations=exterior,
            color=color,
            weight=2,
            fill=True,
            fill_color=color,
            fill_opacity=fill_opacity,
            tooltip=None,
        ).add_to(folium_map)


# ── Page content ──────────────────────────────────────────────────────────────

st.title("SGMap — Singapore at Scale")
st.markdown(
    "See how big Singapore really is by overlaying its outline on any city in the world."
)

st.divider()

ctrl_col, map_col = st.columns([1, 2], gap="large")

with ctrl_col:
    st.subheader("Controls")

    if "target_coords" not in st.session_state:
        st.session_state["target_coords"] = (37.5483, -121.9886)
        st.session_state["target_label"] = "Fremont"

    city_input = st.text_input("Target city", value="Fremont", key="city_input")

    if st.button("Geocode & Center", type="primary"):
        with st.spinner(f"Looking up {city_input}…"):
            result = geocode_city(city_input)
        if result is None:
            st.error(f"Could not find **{city_input}**. Try a more specific name.")
        else:
            st.session_state["target_coords"] = result
            st.session_state["target_label"] = city_input
            st.success(f"Found: {result[0]:.4f}°, {result[1]:.4f}°")

    st.markdown("---")
    rot_col, btn_col = st.columns([3, 1])
    with rot_col:
        rotation = st.slider("Rotation (°)", min_value=-180, max_value=180, value=0, step=1, key="rotation_slider")
    with btn_col:
        st.markdown("<div style='padding-top:28px'>", unsafe_allow_html=True)
        st.button("↺ 0°", on_click=lambda: st.session_state.pop("rotation_slider", None))
        st.markdown("</div>", unsafe_allow_html=True)

    if "target_coords" in st.session_state:
        tgt_lat, tgt_lon = st.session_state["target_coords"]
        st.markdown("---")
        st.caption(
            f"**{st.session_state.get('target_label', 'Target')}**  \n"
            f"{tgt_lat:.4f}°N, {tgt_lon:.4f}°E  \n"
            f"Rotation: {rotation}°"
        )

with map_col:
    if "target_coords" not in st.session_state:
        st.info("Enter a city name and click **Geocode & Center** to begin.")
    else:
        tgt_lat, tgt_lon = st.session_state["target_coords"]

        try:
            sg_geom = fetch_sg_geometry()
        except RuntimeError as e:
            st.error(str(e))
            st.stop()
        centroid = sg_geom.centroid
        sg_center = (centroid.y, centroid.x)  # (lat, lon)

        transformed = transform_geometry(
            sg_geom, sg_center, (tgt_lat, tgt_lon), rotation
        )

        m = folium.Map(
            location=[tgt_lat, tgt_lon],
            zoom_start=10,
            tiles="CartoDB positron",
        )
        Geocoder(collapsed=False, position="topright").add_to(m)
        add_geom_to_map(transformed, m)
        folium.Marker(
            location=[tgt_lat, tgt_lon],
            popup=st.session_state.get("target_label", "Target"),
            icon=folium.Icon(color="red", icon="map-marker", prefix="fa"),
        ).add_to(m)

        map_data = st_folium(m, width=None, height=550, returned_objects=["last_clicked"])

        if map_data and map_data.get("last_clicked"):
            click = map_data["last_clicked"]
            new_coords = (click["lat"], click["lng"])
            if new_coords != st.session_state.get("target_coords"):
                st.session_state["target_coords"] = new_coords
                st.session_state["target_label"] = f"{click['lat']:.4f}°, {click['lng']:.4f}°"
                st.rerun()
