import sys
import os

# src folder ka path add karo taaki risk_engine.py import ho sake
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

import pandas as pd
import joblib
from risk_engine import classify_risk

from risk_engine import classify_risk
from database import get_all_thresholds

# Models aur encoder ek baar load karo (baar-baar load na karna pade)
MODELS = {
    "1h": joblib.load("models/artifacts/xgb_model_1h.pkl"),
    "3h": joblib.load("models/artifacts/xgb_model_3h.pkl"),
    "6h": joblib.load("models/artifacts/xgb_model_6h.pkl"),
}
station_encoder = joblib.load("models/artifacts/station_encoder.pkl")

FEATURE_COLS = [
    "water_level", "water_level_lag1", "water_level_lag2", "water_level_lag3",
    "rainfall_lag1", "rainfall", "rainfall_sum_6h", "water_level_trend", "station_encoded"
]


def prepare_station_features(df, station):
    """Ek station ke liye wahi features banata hai jo training me bane the."""
    station_df = df[df["station"] == station].sort_values("Data Acquisition Time").copy()

    station_df["water_level_lag1"] = station_df["water_level"].shift(1)
    station_df["water_level_lag2"] = station_df["water_level"].shift(2)
    station_df["water_level_lag3"] = station_df["water_level"].shift(3)
    station_df["rainfall_lag1"] = station_df["rainfall"].shift(1)
    station_df["water_level_trend"] = station_df["water_level_lag1"] - station_df["water_level_lag2"]

    station_df = station_df.set_index("Data Acquisition Time")
    station_df["rainfall_sum_6h"] = station_df["rainfall"].rolling("6h").sum()
    station_df = station_df.reset_index()

    station_df["station_encoded"] = station_encoder.transform(station_df["station"])
    return station_df


def get_station_forecast(station):
    """Ek station ke liye current status + 1h/3h/6h forecast + risk nikalta hai."""
    df = pd.read_parquet("data/curated/flood_data_clean.parquet")
    thresholds = get_all_thresholds().set_index("station_name")

    station_df = prepare_station_features(df, station)
    latest = station_df.dropna(subset=FEATURE_COLS).iloc[-1]

    current_level = latest["water_level"]
    X = latest[FEATURE_COLS].to_frame().T.astype(float)

    result = {
        "station": station,
        "current_time": latest["Data Acquisition Time"],
        "current_level": current_level,
        "current_risk": classify_risk(current_level, station, thresholds),
        "forecasts": {}
    }

    for horizon, model in MODELS.items():
        predicted_delta = model.predict(X)[0]
        predicted_level = current_level + predicted_delta
        risk = classify_risk(predicted_level, station, thresholds)
        result["forecasts"][horizon] = {
            "predicted_level": round(predicted_level, 3),
            "risk": risk
        }

    return result

def get_all_stations_status():
    """Sabhi stations ka current status + forecasts ek list me deta hai."""
    df = pd.read_parquet("data/curated/flood_data_clean.parquet")
    all_stations = df["station"].unique()

    results = []
    for station in all_stations:
        try:
            forecast = get_station_forecast(station)
            results.append(forecast)
        except Exception as e:
            # Agar kisi station me issue aaye (jaise bahut kam data), skip karo
            continue

    return results

import shap

def get_shap_explanation(station, horizon="1h"):
    """Ek station ke latest prediction ke liye SHAP values nikalta hai."""
    df = pd.read_parquet("data/curated/flood_data_clean.parquet")
    station_df = prepare_station_features(df, station)
    latest = station_df.dropna(subset=FEATURE_COLS).iloc[-1]

    X = latest[FEATURE_COLS].to_frame().T.astype(float)

    model = MODELS[horizon]
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)[0]

    # Readable feature names
    readable_names = {
        "water_level": "Current Water Level",
        "water_level_lag1": "Level (1h ago)",
        "water_level_lag2": "Level (2h ago)",
        "water_level_lag3": "Level (3h ago)",
        "rainfall": "Current Rainfall",
        "rainfall_lag1": "Rainfall (1h ago)",
        "rainfall_sum_6h": "Rainfall (last 6h total)",
        "water_level_trend": "Recent Trend",
        "station_encoded": "Station Identity"
    }

    result = pd.DataFrame({
        "feature": [readable_names.get(f, f) for f in FEATURE_COLS],
        "shap_value": shap_values
    }).sort_values("shap_value", key=abs, ascending=False)

    return result
def backtest_station(station, horizon="1h"):
    """Poori history pe model chalata hai, taaki predicted vs actual compare kar sakein."""
    df = pd.read_parquet("data/curated/flood_data_clean.parquet")
    station_df = prepare_station_features(df, station)

    target_shift = {"1h": -1, "3h": -3, "6h": -6}[horizon]
    station_df["actual_future"] = station_df["water_level"].shift(target_shift)

    valid = station_df.dropna(subset=FEATURE_COLS + ["actual_future"]).copy()

    X = valid[FEATURE_COLS].astype(float)
    model = MODELS[horizon]
    predicted_delta = model.predict(X)
    valid["predicted_future"] = valid["water_level"].values + predicted_delta

    return valid[["Data Acquisition Time", "water_level", "actual_future", "predicted_future"]]

if __name__ == "__main__":
    all_status = get_all_stations_status()

    print(f"Total stations processed: {len(all_status)}\n")

    for station_data in all_status[:10]:
        print(f"{station_data['station']:30s} → {station_data['current_time']} | Risk: {station_data['current_risk']}")