import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from src.theme import apply_theme, RISK_COLORS
from src.theme import data_attribution
from models.predict import get_all_stations_status

st.set_page_config(page_title="Map Explorer - FloodGuard AI", layout="wide", page_icon="🌊")
apply_theme()

st.title("Map Explorer")


@st.cache_data(ttl=300)
def load_map_data():
    
    station_coords = pd.read_csv("data/curated/station_coords.csv")

    all_status = get_all_stations_status()
    status_df = pd.DataFrame([
        {"station": s["station"], "risk": s["current_risk"], "level": s["current_level"]}
        for s in all_status
    ])

    return station_coords.merge(status_df, on="station", how="inner")

map_data = load_map_data()

# Narmada basin ke center pe map shuru karo
center_lat = map_data["Latitude"].mean()
center_lon = map_data["Longitude"].mean()

m = folium.Map(location=[center_lat, center_lon], zoom_start=7, tiles="OpenStreetMap")

for _, row in map_data.iterrows():
    color = RISK_COLORS.get(row["risk"], "#6B7280")

    folium.CircleMarker(
        location=[row["Latitude"], row["Longitude"]],
        radius=8,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.8,
        popup=f"<b>{row['station']}</b><br>Level: {row['level']:.2f} m<br>Risk: {row['risk']}",
        tooltip=row["station"]
    ).add_to(m)

st_folium(m, width=1400, height=600)

st.markdown("##### Legend")
legend_cols = st.columns(4)
for i, (risk, color) in enumerate(RISK_COLORS.items()):
    if risk == "Unknown":
        continue
    legend_cols[i].markdown(f"<span style='color:{color}; font-size:20px;'>●</span> {risk}", unsafe_allow_html=True)

data_attribution()