import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.theme import apply_theme
from src.theme import data_attribution
from models.predict import backtest_station

st.set_page_config(page_title="Analytics - FloodGuard AI", layout="wide", page_icon="🌊")
apply_theme()

st.title("Analytics")

st.markdown("### Model Performance Summary")
st.caption("Tested on held-out data from 2024-08-12 onward, using a chronological train/test split.")

summary_data = {
    "Horizon": ["1 Hour", "3 Hour", "6 Hour"],
    "Persistence MAE (m)": [0.0128, 0.0355, 0.0656],
    "XGBoost MAE (m)": [0.0193, 0.0506, 0.0979],
    "XGBoost MAE during significant change (m)": [0.2266, 0.2380, 0.2972],
    "Persistence MAE during significant change (m)": [0.2682, 0.3066, 0.3599],
}
summary_df = pd.DataFrame(summary_data)
st.dataframe(summary_df, width="stretch", hide_index=True)

st.caption(
    "On all test rows, persistence has the lowest MAE and XGBoost the lowest RMSE (fewer large errors). "
    "On rows where the level actually changed by more than 0.1 m, XGBoost's MAE is 15-22% lower than persistence. "
    "That slice is selected using the realised outcome, so it is a retrospective check, not a measure of early-warning performance."
)

st.markdown("### Forecast vs Actual (Backtest)")

@st.cache_data
def load_station_list():
    df = pd.read_parquet("data/curated/flood_data_clean.parquet")
    return sorted(df["station"].unique())

selected_station = st.selectbox("Select a station", load_station_list())

if selected_station:
    backtest_df = backtest_station(selected_station, horizon="1h")
    recent = backtest_df.tail(24 * 14)  # last ~14 din ka data

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=recent["Data Acquisition Time"], y=recent["actual_future"],
        mode="lines", name="Actual", line=dict(color="#1F2937", width=2)
    ))
    fig.add_trace(go.Scatter(
        x=recent["Data Acquisition Time"], y=recent["predicted_future"],
        mode="lines", name="Predicted (1h ahead)", line=dict(color="#DC2626", width=2, dash="dot")
    ))

    fig.update_layout(
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        font=dict(color="#1F2937"),
        xaxis=dict(gridcolor="#E5E9EF"),
        yaxis=dict(gridcolor="#E5E9EF", title="Water Level (m)"),
        margin=dict(l=20, r=20, t=20, b=20), height=400
    )
    st.plotly_chart(fig, width="stretch")

data_attribution()