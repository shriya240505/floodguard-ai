import streamlit as st
import pandas as pd
import numpy as np
from src.theme import apply_theme, RISK_COLORS
from src.theme import data_attribution
from models.predict import get_all_stations_status

st.set_page_config(page_title="FloodGuard AI", layout="wide", page_icon="🌊")
apply_theme()

st.title("FloodGuard AI")
st.write("Flood intelligence for the Narmada Basin")
from src.theme import tricolor_strip
tricolor_strip()


@st.cache_data(ttl=300)
def load_dashboard_data():
    return get_all_stations_status()


with st.spinner("Loading station data..."):
    all_status = load_dashboard_data()

# KPI counts nikalo
risk_counts = {"Normal": 0, "Watch": 0, "Warning": 0, "Danger": 0}
for station_data in all_status:
    risk = station_data["current_risk"]
    if risk in risk_counts:
        risk_counts[risk] += 1

st.markdown("### Basin Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Normal", risk_counts["Normal"])
col2.metric("Watch", risk_counts["Watch"])
col3.metric("Warning", risk_counts["Warning"])
col4.metric("Danger", risk_counts["Danger"])

st.markdown("### Station Status")


import datetime

# Poore dataset ka sabse latest timestamp nikalo (ye hamara "reference now" hoga)
all_times = [s["current_time"] for s in all_status]

dataset_latest_time = pd.Series(all_times).median()

table_data = []
for station_data in all_status:
    days_old = (dataset_latest_time - station_data["current_time"]).days
    data_freshness = "⚠️ Stale" if days_old > 45 else "✅ Fresh"

    table_data.append({
        "Station": station_data["station"],
        "Current Level (m)": round(station_data["current_level"], 2),
        "Current Risk": station_data["current_risk"],
        "1h Forecast": station_data["forecasts"]["1h"]["risk"],
        "3h Forecast": station_data["forecasts"]["3h"]["risk"],
        "6h Forecast": station_data["forecasts"]["6h"]["risk"],
        "Data Status": data_freshness,
    })
status_df = pd.DataFrame(table_data)
st.dataframe(status_df, use_container_width=True, height=500)

data_attribution()