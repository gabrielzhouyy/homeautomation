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
from shapely.geometry import MultiPolygon, shape
from streamlit_folium import st_folium

GEOJSON_URL = (
    "https://raw.githubusercontent.com/cheeaun/singapore-boundary"
    "/master/singapore.geojson"
)


@st.cache_data(show_spinner="Loading Singapore boundary…")
def fetch_sg_geometry():
    """Fetch and simplify the Singapore GeoJSON boundary."""
    resp = requests.get(GEOJSON_URL, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if data["type"] == "FeatureCollection":
        geom_dict = data["features"][0]["geometry"]
    elif data["type"] == "Feature":
        geom_dict = data["geometry"]
    else:
        geom_dict = data
    sg_shape = shape(geom_dict)
    return sg_shape.simplify(0.001, preserve_topology=True)


def geocode_city(city_name: str):
    """Return (lat, lon) for *city_name*, or None if not found."""
    geolocator = Nominatim(user_agent="sg_scale_map_v1")
    location = geolocator.geocode(city_name, timeout=10)
    if location:
        return location.latitude, location.longitude
    return None


def transform_geometry(sg_geom, sg_center_latlon, target_latlon, rotation_deg, scale_factor):
    """
    Translate, scale, and rotate Singapore geometry onto *target_latlon*.

    Coordinate system note: shapely uses (x=lon, y=lat).

    Latitude correction scales the longitude span so 1 degree of longitude
    at the target latitude represents the same physical distance as it did
    at Singapore's latitude (Mercator-consistent overlay).
    """
    sg_lat, sg_lon = sg_center_latlon
    tgt_lat, tgt_lon = target_latlon

    # Guard against poles (cos → 0)
    cos_sg = math.cos(math.radians(sg_lat))
    cos_tgt = math.cos(math.radians(max(-89.9, min(89.9, tgt_lat))))
    lat_correction = cos_sg / cos_tgt if cos_tgt != 0 else 1.0

    # 1. Center at origin
    centered = translate(sg_geom, xoff=-sg_lon, yoff=-sg_lat)

    # 2. Scale (and correct longitude span for target latitude)
    scaled = scale(
        centered,
        xfact=scale_factor * lat_correction,
        yfact=scale_factor,
        origin=(0, 0),
    )

    # 3. Rotate around origin
    rotated = rotate(scaled, rotation_deg, origin=(0, 0), use_radians=False)

    # 4. Translate to target
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
            tooltip="Singapore (to scale)",
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

    city_input = st.text_input("Target city", value="London", key="city_input")

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
    rotation = st.slider("Rotation (°)", min_value=-180, max_value=180, value=0, step=1)
    scale_factor = st.slider("Scale", min_value=0.5, max_value=8.0, value=1.0, step=0.1,
                             help="1× = true size. Increase to exaggerate for comparison.")

    if "target_coords" in st.session_state:
        tgt_lat, tgt_lon = st.session_state["target_coords"]
        st.markdown("---")
        st.caption(
            f"**{st.session_state.get('target_label', 'Target')}**  \n"
            f"{tgt_lat:.4f}°N, {tgt_lon:.4f}°E  \n"
            f"Rotation: {rotation}° | Scale: {scale_factor}×"
        )

with map_col:
    if "target_coords" not in st.session_state:
        st.info("Enter a city name and click **Geocode & Center** to begin.")
    else:
        tgt_lat, tgt_lon = st.session_state["target_coords"]

        sg_geom = fetch_sg_geometry()
        centroid = sg_geom.centroid
        sg_center = (centroid.y, centroid.x)  # (lat, lon)

        transformed = transform_geometry(
            sg_geom, sg_center, (tgt_lat, tgt_lon), rotation, scale_factor
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

        st_folium(m, width=None, height=550, returned_objects=[])
