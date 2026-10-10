from utils import haversine_distance
import pandas as pd


def load_and_clean_rainfall(filepath="data/raw/rainfall_nca_mp_2021_2025.csv"):
    df = pd.read_csv(filepath)

    rain_col = "Telemetry Hourly Rainfall (mm)"

    # Fix 1: Unit scale issue (values were 10x too high)
    df[rain_col] = df[rain_col] / 10

    # Fix 2: Negative values ko 0 kar do (rainfall never negative)
    df[rain_col] = df[rain_col].clip(lower=0)

    # Fix 3: Duplicate (Station + Time) rows hatao, pehli entry rakho
    df["Data Acquisition Time"] = pd.to_datetime(
        df["Data Acquisition Time"], format="%d-%m-%Y %H:%M", errors="coerce"
    )
    df = df.drop_duplicates(subset=["Station", "Data Acquisition Time"], keep="first")

    return df


def load_and_clean_water_level(filepath="data/raw/water_level_narmada_2021_2025.csv"):
    df = pd.read_csv(filepath)
    df = df[df["State"] == "Madhya Pradesh"]

    wl_col = "River Water Level Manual Hourly (meter)"

    df["Data Acquisition Time"] = pd.to_datetime(
        df["Data Acquisition Time"], format="%d-%m-%Y %H:%M", errors="coerce"
    )

    # Har station ke Q1, Q3 nikalo aur wapas har row me copy kar do (transform)
    Q1 = df.groupby("Station")[wl_col].transform(lambda x: x.quantile(0.25))
    Q3 = df.groupby("Station")[wl_col].transform(lambda x: x.quantile(0.75))
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    df = df[(df[wl_col] >= lower) & (df[wl_col] <= upper)]

    # Duplicate (Station + Time) rows bhi hatao
    df = df.drop_duplicates(subset=["Station", "Data Acquisition Time"], keep="first")

    return df


def build_station_mapping(rainfall_df, water_level_df):
    # Har station ki unique lat/lon nikalo (ek station ki har row me same lat/lon hoti hai)
    rain_stations = rainfall_df[["Station", "Latitude", "Longitude"]].drop_duplicates(subset=["Station"])
    wl_stations = water_level_df[["Station", "Latitude", "Longitude"]].drop_duplicates(subset=["Station"])

    mapping = []

    for _, wl_row in wl_stations.iterrows():
        distances = haversine_distance(
            wl_row["Latitude"], wl_row["Longitude"],
            rain_stations["Latitude"], rain_stations["Longitude"]
        )
        nearest_index = distances.idxmin()
        nearest_rain_station = rain_stations.loc[nearest_index, "Station"]
        nearest_distance_km = distances.min()

        mapping.append({
            "water_level_station": wl_row["Station"],
            "nearest_rainfall_station": nearest_rain_station,
            "distance_km": round(nearest_distance_km, 2)
        })

    return pd.DataFrame(mapping)


def build_merged_dataset(rainfall_df, water_level_df, mapping_df):
    wl_col = "River Water Level Manual Hourly (meter)"
    rain_col = "Telemetry Hourly Rainfall (mm)"

    # In stations me severe data-quality issues mile (jaise achanak, physically-impossible level jump)
    excluded_stations = ["Mukki"]

    merged_pieces = []

    for _, map_row in mapping_df.iterrows():
        wl_station_name = map_row["water_level_station"]
        rain_station_name = map_row["nearest_rainfall_station"]

        if wl_station_name in excluded_stations:
            continue

        # Sirf isi station ka data nikalo
        wl_subset = water_level_df[water_level_df["Station"] == wl_station_name][
            ["Data Acquisition Time", wl_col]
        ].rename(columns={wl_col: "water_level"})

        rain_subset = rainfall_df[rainfall_df["Station"] == rain_station_name][
            ["Data Acquisition Time", rain_col]
        ].rename(columns={rain_col: "rainfall"})

        # Time ke hisaab se jodo (inner = sirf dono me maujood timestamps rakho)
        merged = pd.merge(wl_subset, rain_subset, on="Data Acquisition Time", how="inner")

        # Agar is station ka koi bhi overlapping data nahi mila, to skip karo
        if len(merged) == 0:
            continue

        # Time ke hisaab se sort karo
        merged = merged.sort_values("Data Acquisition Time")

        # Poori hourly timeline banao (start se end tak, har ghante ka slot)
        full_range = pd.date_range(
            start=merged["Data Acquisition Time"].min(),
            end=merged["Data Acquisition Time"].max(),
            freq="h"
        )
        merged = merged.set_index("Data Acquisition Time").reindex(full_range)
        merged.index.name = "Data Acquisition Time"

        # Chhote gaps (<=6 ghante) interpolate karo, bade gaps ko missing hi rehne do
        merged["water_level"] = merged["water_level"].interpolate(method="linear", limit=6)
        merged["rainfall"] = merged["rainfall"].interpolate(method="linear", limit=6)

        merged = merged.reset_index()
        merged["station"] = wl_station_name

        merged_pieces.append(merged)

    final_df = pd.concat(merged_pieces, ignore_index=True)

    # Ab jo rows me water_level ya rainfall NaN hai, unhe hata do (bade gaps wali)
    rows_before = len(final_df)
    final_df = final_df.dropna(subset=["water_level", "rainfall"])
    rows_after = len(final_df)

    print(f"\nDropped {rows_before - rows_after} rows with unfillable gaps (large missing periods)")
    print(f"Remaining usable rows: {rows_after}")

    return final_df


if __name__ == "__main__":
    rainfall = load_and_clean_rainfall()
    print("Cleaned rainfall data:")
    print(rainfall["Telemetry Hourly Rainfall (mm)"].describe())
    print("Total rows after cleaning:", len(rainfall))

    print("\n" + "=" * 50 + "\n")

    water_level = load_and_clean_water_level()
    print("Cleaned water level data:")
    print(water_level["River Water Level Manual Hourly (meter)"].describe())
    print("Total rows after cleaning:", len(water_level))

    print("\n" + "=" * 50 + "\n")

    mapping = build_station_mapping(rainfall, water_level)
    print("Station mapping (first 10):")
    print(mapping.head(10).to_string())
    print("\nMax distance:", mapping["distance_km"].max(), "km")
    print("Min distance:", mapping["distance_km"].min(), "km")

    print("\n" + "=" * 50 + "\n")

    final_dataset = build_merged_dataset(rainfall, water_level, mapping)
    print("Final merged dataset sample:")
    print(final_dataset.head(10).to_string())
    print("\nTotal rows:", len(final_dataset))
    print("Unique stations in final dataset:", final_dataset["station"].nunique())

    final_dataset.to_parquet("data/curated/flood_data_clean.parquet", index=False)
    print("\nSaved cleaned dataset to data/curated/flood_data_clean.parquet")