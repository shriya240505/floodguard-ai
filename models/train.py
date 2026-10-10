import pandas as pd
import numpy as np
import joblib
import mlflow
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor

# MLflow: is poori training ka ek record (run) banega
mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("floodguard_forecasting")
mlflow.start_run(run_name="xgb_delta_v1")

# Cleaned data load karo
df = pd.read_parquet("data/curated/flood_data_clean.parquet")
df = df.sort_values(["station", "Data Acquisition Time"])

# Lag features
df["water_level_lag1"] = df.groupby("station")["water_level"].shift(1)
df["water_level_lag2"] = df.groupby("station")["water_level"].shift(2)
df["water_level_lag3"] = df.groupby("station")["water_level"].shift(3)
df["rainfall_lag1"] = df.groupby("station")["rainfall"].shift(1)

# Trend feature — level kitni tezi se badal raha hai
df["water_level_trend"] = df["water_level_lag1"] - df["water_level_lag2"]

df = df.dropna(subset=["water_level_lag1", "water_level_lag2", "water_level_lag3", "rainfall_lag1"])

# Rolling rainfall sum — pichle 6 ghante ki total baarish
df = df.set_index("Data Acquisition Time")
df["rainfall_sum_6h"] = df.groupby("station")["rainfall"].rolling("6h").sum().reset_index(level=0, drop=True)
df = df.reset_index()

# Targets — absolute future value aur delta (change)
for h in [1, 3, 6]:
    df[f"target_{h}h"] = df.groupby("station")["water_level"].shift(-h)
    df[f"target_{h}h_delta"] = df[f"target_{h}h"] - df["water_level"]

station_encoder = LabelEncoder()
df["station_encoded"] = station_encoder.fit_transform(df["station"])


def evaluate_persistence(df, target_col, horizon_name):
    df_subset = df.dropna(subset=[target_col])
    predictions = df_subset["water_level"]
    actual = df_subset[target_col]

    mae = mean_absolute_error(actual, predictions)
    rmse = np.sqrt(mean_squared_error(actual, predictions))

    print(f"\nPERSISTENCE BASELINE — {horizon_name}")
    print(f"MAE:  {mae:.4f} meters")
    print(f"RMSE: {rmse:.4f} meters")

    mlflow.log_metric(f"persistence_mae_{target_col}", mae)
    mlflow.log_metric(f"persistence_rmse_{target_col}", rmse)


evaluate_persistence(df, "target_1h", "1 Hour Horizon")
evaluate_persistence(df, "target_3h", "3 Hour Horizon")
evaluate_persistence(df, "target_6h", "6 Hour Horizon")

print("\n" + "=" * 50)
print("TIME-BASED SPLIT")
print("=" * 50)

split_date = df["Data Acquisition Time"].quantile(0.8)
print(f"\nSplit date: {split_date}")

train_df = df[df["Data Acquisition Time"] <= split_date]
test_df = df[df["Data Acquisition Time"] > split_date]

print(f"Training rows: {len(train_df)}")
print(f"Testing rows: {len(test_df)}")

feature_cols = [
    "water_level", "water_level_lag1", "water_level_lag2", "water_level_lag3",
    "rainfall_lag1", "rainfall", "rainfall_sum_6h", "water_level_trend"
]
xgb_feature_cols = feature_cols + ["station_encoded"]

xgb_params = {"n_estimators": 200, "max_depth": 6, "learning_rate": 0.1, "random_state": 42}

mlflow.log_params({
    **xgb_params,
    "target": "delta (future level - current level)",
    "split": "chronological 80/20",
    "split_date": str(split_date),
    "features": ", ".join(xgb_feature_cols),
})

print("\n" + "=" * 50)
print("LINEAR REGRESSION (delta-based)")
print("=" * 50)


def evaluate_linear_regression_delta(train_df, test_df, delta_col, actual_target_col, horizon_name):
    train_subset = train_df.dropna(subset=[delta_col])
    test_subset = test_df.dropna(subset=[actual_target_col])

    model = LinearRegression()
    model.fit(train_subset[feature_cols], train_subset[delta_col])

    predicted_delta = model.predict(test_subset[feature_cols])
    final_prediction = test_subset["water_level"].values + predicted_delta
    y_test_actual = test_subset[actual_target_col]

    mae = mean_absolute_error(y_test_actual, final_prediction)
    rmse = np.sqrt(mean_squared_error(y_test_actual, final_prediction))

    print(f"\nLINEAR REGRESSION — {horizon_name}")
    print(f"MAE:  {mae:.4f} meters")
    print(f"RMSE: {rmse:.4f} meters")

    mlflow.log_metric(f"linear_mae_{actual_target_col}", mae)
    mlflow.log_metric(f"linear_rmse_{actual_target_col}", rmse)


evaluate_linear_regression_delta(train_df, test_df, "target_1h_delta", "target_1h", "1 Hour Horizon")
evaluate_linear_regression_delta(train_df, test_df, "target_3h_delta", "target_3h", "3 Hour Horizon")
evaluate_linear_regression_delta(train_df, test_df, "target_6h_delta", "target_6h", "6 Hour Horizon")

print("\n" + "=" * 50)
print("XGBOOST (delta-based)")
print("=" * 50)


def evaluate_xgboost_delta(train_df, test_df, delta_col, actual_target_col, horizon_name):
    train_subset = train_df.dropna(subset=[delta_col])
    test_subset = test_df.dropna(subset=[actual_target_col])

    model = XGBRegressor(**xgb_params)
    model.fit(train_subset[xgb_feature_cols], train_subset[delta_col])

    predicted_delta = model.predict(test_subset[xgb_feature_cols])
    final_prediction = test_subset["water_level"].values + predicted_delta
    y_test_actual = test_subset[actual_target_col]

    mae = mean_absolute_error(y_test_actual, final_prediction)
    rmse = np.sqrt(mean_squared_error(y_test_actual, final_prediction))

    importance = pd.Series(model.feature_importances_, index=xgb_feature_cols)
    print("Feature importance:")
    print(importance.sort_values(ascending=False))

    print(f"\nXGBOOST — {horizon_name}")
    print(f"MAE:  {mae:.4f} meters")
    print(f"RMSE: {rmse:.4f} meters")

    mlflow.log_metric(f"xgb_mae_{actual_target_col}", mae)
    mlflow.log_metric(f"xgb_rmse_{actual_target_col}", rmse)

    return model


model_1h = evaluate_xgboost_delta(train_df, test_df, "target_1h_delta", "target_1h", "1 Hour Horizon")
model_3h = evaluate_xgboost_delta(train_df, test_df, "target_3h_delta", "target_3h", "3 Hour Horizon")
model_6h = evaluate_xgboost_delta(train_df, test_df, "target_6h_delta", "target_6h", "6 Hour Horizon")

print("\n" + "=" * 50)
print("PERFORMANCE DURING HIGH-RAINFALL EVENTS (1 Hour Horizon)")
print("=" * 50)

rainfall_threshold = df["rainfall"].quantile(0.75)
print(f"\nHigh-rainfall threshold: {rainfall_threshold:.2f} mm")

test_subset_1h = test_df.dropna(subset=["target_1h"])
high_rain_test = test_subset_1h[test_subset_1h["rainfall"] > rainfall_threshold]
print(f"High-rainfall test rows: {len(high_rain_test)} out of {len(test_subset_1h)}")

actual = high_rain_test["target_1h"]
persistence_mae = mean_absolute_error(actual, high_rain_test["water_level"])
predicted_delta = model_1h.predict(high_rain_test[xgb_feature_cols])
xgb_mae = mean_absolute_error(actual, high_rain_test["water_level"].values + predicted_delta)

print(f"Persistence MAE: {persistence_mae:.4f} meters")
print(f"XGBoost MAE:     {xgb_mae:.4f} meters")

mlflow.log_metric("persistence_mae_high_rain_target_1h", persistence_mae)
mlflow.log_metric("xgb_mae_high_rain_target_1h", xgb_mae)

print("\n" + "=" * 50)
print("PERFORMANCE DURING SIGNIFICANT WATER-LEVEL CHANGE")
print("=" * 50)


def evaluate_significant_change(test_df, target_col, model, horizon_name):
    subset = test_df.dropna(subset=[target_col]).copy()
    subset["actual_change"] = (subset[target_col] - subset["water_level"]).abs()
    sig = subset[subset["actual_change"] > 0.1]

    persistence_mae = mean_absolute_error(sig[target_col], sig["water_level"])
    predicted_delta = model.predict(sig[xgb_feature_cols])
    xgb_mae = mean_absolute_error(sig[target_col], sig["water_level"].values + predicted_delta)

    print(f"\n{horizon_name} — significant-change rows: {len(sig)} out of {len(subset)}")
    print(f"Persistence MAE: {persistence_mae:.4f} meters")
    print(f"XGBoost MAE:     {xgb_mae:.4f} meters")

    mlflow.log_metric(f"persistence_mae_significant_{target_col}", persistence_mae)
    mlflow.log_metric(f"xgb_mae_significant_{target_col}", xgb_mae)


evaluate_significant_change(test_df, "target_1h", model_1h, "1-Hour")
evaluate_significant_change(test_df, "target_3h", model_3h, "3-Hour")
evaluate_significant_change(test_df, "target_6h", model_6h, "6-Hour")

print("\n" + "=" * 50)
print("SAVING MODELS")
print("=" * 50)

joblib.dump(model_1h, "models/artifacts/xgb_model_1h.pkl")
joblib.dump(model_3h, "models/artifacts/xgb_model_3h.pkl")
joblib.dump(model_6h, "models/artifacts/xgb_model_6h.pkl")
joblib.dump(station_encoder, "models/artifacts/station_encoder.pkl")
print("Saved models to models/artifacts/")

mlflow.log_artifacts("models/artifacts")
mlflow.end_run()
print("MLflow run saved. Terminal me `mlflow ui` chalao aur http://127.0.0.1:5000 kholo.")