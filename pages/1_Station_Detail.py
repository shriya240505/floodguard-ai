import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.theme import apply_theme, RISK_COLORS
from src.theme import data_attribution
from models.predict import get_station_forecast, get_shap_explanation

st.set_page_config(page_title="Station Detail - FloodGuard AI", layout="wide", page_icon="🌊")
apply_theme()

st.title("Station Detail")


@st.cache_data
def load_station_list():
    df = pd.read_parquet("data/curated/flood_data_clean.parquet")
    return sorted(df["station"].unique())


station_list = load_station_list()
selected_station = st.selectbox("Select a station", station_list)

if selected_station:
    forecast = get_station_forecast(selected_station)

    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 History", "🔍 Why this forecast?"])

    with tab1:
        col1, col2 = st.columns(2)
        col1.metric("Current Water Level", f"{forecast['current_level']:.2f} m")
        col2.metric("Current Risk", forecast["current_risk"])

        st.markdown("### Forecast")
        fcol1, fcol2, fcol3 = st.columns(3)
        fcol1.metric("1 Hour", f"{forecast['forecasts']['1h']['predicted_level']} m", forecast['forecasts']['1h']['risk'])
        fcol2.metric("3 Hour", f"{forecast['forecasts']['3h']['predicted_level']} m", forecast['forecasts']['3h']['risk'])
        fcol3.metric("6 Hour", f"{forecast['forecasts']['6h']['predicted_level']} m", forecast['forecasts']['6h']['risk'])

    with tab2:
        df = pd.read_parquet("data/curated/flood_data_clean.parquet")
        station_df = df[df["station"] == selected_station].sort_values("Data Acquisition Time")

        st.markdown("### Historical Water Level (Last 30 Days)")

        latest_date = station_df["Data Acquisition Time"].max()
        cutoff_date = latest_date - pd.Timedelta(days=30)
        recent_df = station_df[station_df["Data Acquisition Time"] >= cutoff_date]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=recent_df["Data Acquisition Time"],
            y=recent_df["water_level"],
            mode="lines",
            name="Water Level",
            line=dict(color="#0E7490", width=2)
        ))

        fig.update_layout(
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            font=dict(color="#1F2937"),
            xaxis=dict(gridcolor="#E5E9EF"),
            yaxis=dict(gridcolor="#E5E9EF", title="Water Level (m)"),
            margin=dict(l=20, r=20, t=20, b=20),
            height=400
        )

        st.plotly_chart(fig, width="stretch")

    with tab3:
        st.markdown("#### What's driving the 1-hour forecast?")

        shap_df = get_shap_explanation(selected_station, horizon="1h")

        colors = ["#DC2626" if v > 0 else "#0E7490" for v in shap_df["shap_value"]]

        fig2 = go.Figure(go.Bar(
            x=shap_df["shap_value"],
            y=shap_df["feature"],
            orientation="h",
            marker_color=colors
        ))
        fig2.update_layout(
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            font=dict(color="#1F2937"),
            xaxis=dict(gridcolor="#E5E9EF", title="Impact on predicted change (m)"),
            margin=dict(l=20, r=20, t=20, b=20),
            height=350
        )
        st.plotly_chart(fig2, width="stretch")

        st.caption("🔴 Red = pushes water level up | 🔵 Blue = pushes water level down. This shows feature contribution, not proof of causation.")

data_attribution()