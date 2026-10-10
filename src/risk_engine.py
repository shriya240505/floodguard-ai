import pandas as pd


def compute_station_thresholds(df):
    """Har station ke liye percentile-based thresholds nikalta hai."""
    thresholds = df.groupby("station")["water_level"].quantile([0.70, 0.90, 0.97]).unstack()
    thresholds.columns = ["watch_threshold", "warning_threshold", "danger_threshold"]
    return thresholds


def classify_risk(water_level, station, thresholds_df):
    """Ek water-level value ko station ke thresholds ke against classify karta hai."""
    if station not in thresholds_df.index:
        return "Unknown"

    station_thresh = thresholds_df.loc[station]

    if water_level >= station_thresh["danger_threshold"]:
        return "Danger"
    elif water_level >= station_thresh["warning_threshold"]:
        return "Warning"
    elif water_level >= station_thresh["watch_threshold"]:
        return "Watch"
    else:
        return "Normal"


if __name__ == "__main__":
    df = pd.read_parquet("data/curated/flood_data_clean.parquet")
    thresholds = compute_station_thresholds(df)

    print("Sample thresholds (first 5 stations):")
    print(thresholds.head())

    # Test — ek station ka latest reading classify karo
    sample_station = df["station"].iloc[0]
    latest_reading = df[df["station"] == sample_station].sort_values("Data Acquisition Time").iloc[-1]

    risk = classify_risk(latest_reading["water_level"], sample_station, thresholds)
    print(f"\nStation: {sample_station}")
    print(f"Latest water level: {latest_reading['water_level']:.2f}m")
    print(f"Risk classification: {risk}")

    thresholds.to_csv("data/curated/station_thresholds.csv")
    print("\nSaved thresholds to data/curated/station_thresholds.csv")