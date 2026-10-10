import pandas as pd

rainfall = pd.read_csv("data/raw/rainfall_nca_mp_2021_2025.csv")
water_level = pd.read_csv("data/raw/water_level_narmada_2021_2025.csv")

# print("RAINFALL — Columns:")
# print(rainfall.columns.tolist())

# print("\nRAINFALL — Unique Basins:")
# print(rainfall["Basin"].unique())

# print("\nRAINFALL — Narmada basin station count:")
# narmada_rain = rainfall[rainfall["Basin"] == "Narmada"]
# print(narmada_rain["Station"].nunique(), "stations")
# print(narmada_rain["Station"].unique())

# print("\nRAINFALL — Total rows:", len(rainfall))
# print("Date range (rainfall):")
# print(rainfall["Data Acquisition Time"].min(), "to", rainfall["Data Acquisition Time"].max())

# print("\n" + "="*50)

# print("\nWATER LEVEL — Total rows:", len(water_level))
# print("Date range (water level):")
# print(water_level["Data Acquisition Time"].min(), "to", water_level["Data Acquisition Time"].max())
# print("RAINFALL — Missing values per column:")
# print(rainfall.isnull().sum())

# print("\nWATER LEVEL — Missing values per column:")
# print(water_level.isnull().sum())
# print("RAINFALL — Duplicate rows:", rainfall.duplicated().sum())
# print("RAINFALL — Value range (mm):")
# print(rainfall["Telemetry Hourly Rainfall (mm)"].describe())

# print("\n" + "="*50)

# print("\nWATER LEVEL — Duplicate rows:", water_level.duplicated().sum())
# print("WATER LEVEL — Value range (meter):")
# print(water_level["River Water Level Manual Hourly (meter)"].describe())

# # RAINFALL — domain knowledge wali limit (negative ya 300mm+ galat maano)
# rain_col = "Telemetry Hourly Rainfall (mm)"
# rain_outliers = rainfall[(rainfall[rain_col] < 0) | (rainfall[rain_col] > 300)]
# print("Rainfall outliers:", len(rain_outliers), "out of", len(rainfall))
# print("Percentage:", round(len(rain_outliers) / len(rainfall) * 100, 2), "%")

# print("\n" + "="*50 + "\n")

# # WATER LEVEL — IQR method, PER STATION (kyunki har station ka apna range hai)
# wl_col = "River Water Level Manual Hourly (meter)"

# def count_outliers(group):
#     Q1 = group[wl_col].quantile(0.25)
#     Q3 = group[wl_col].quantile(0.75)
#     IQR = Q3 - Q1
#     lower = Q1 - 1.5 * IQR
#     upper = Q3 + 1.5 * IQR
#     return ((group[wl_col] < lower) | (group[wl_col] > upper)).sum()

# outlier_counts = water_level.groupby("Station").apply(count_outliers)
# total_wl_outliers = outlier_counts.sum()
# print("Water level outliers:", total_wl_outliers, "out of", len(water_level))
# print("Percentage:", round(total_wl_outliers / len(water_level) * 100, 2), "%")


# # Ek station chuno, jaise "Handia"
# one_station = rainfall[rainfall["Station"] == "Handia"].copy()

# # Time ke hisaab se sort karo
# one_station["Data Acquisition Time"] = pd.to_datetime(one_station["Data Acquisition Time"], format="%d-%m-%Y %H:%M")
# one_station = one_station.sort_values("Data Acquisition Time")

# # Pehle 30 rows dikhao — sirf time aur rainfall value
# print(one_station[["Data Acquisition Time", "Telemetry Hourly Rainfall (mm)"]].head(30).to_string())
# rainfall["Data Acquisition Time"] = pd.to_datetime(
#     rainfall["Data Acquisition Time"], format="%d-%m-%Y %H:%M", errors="coerce"
# )

# # Explicitly datetime type me convert karo (dtype confusion fix karne ke liye)
# rainfall["Data Acquisition Time"] = rainfall["Data Acquisition Time"].astype("datetime64[ns]")

# rain_col = "Telemetry Hourly Rainfall (mm)"

# one_station = rainfall[rainfall["Station"] == "Handia"].copy()
# one_station = one_station.sort_values("Data Acquisition Time")

# one_station["hours_since_last"] = one_station["Data Acquisition Time"].diff().dt.total_seconds() / 3600

# outliers_only = one_station[one_station[rain_col] > 300]
# print(outliers_only[["Data Acquisition Time", rain_col, "hours_since_last"]].to_string())
# rain_col = "Telemetry Hourly Rainfall (mm)"

# # 1. Negative values kitni hain, aur kaisi dikhti hain
# negative_rows = rainfall[rainfall[rain_col] < 0]
# print("Total negative rainfall rows:", len(negative_rows))
# print(negative_rows[["Station", "Data Acquisition Time", rain_col]].head(15).to_string())

# print("\n" + "="*50 + "\n")

# # 2. Duplicate timestamps (same station + same time, alag values) kitni hain
# duplicate_timestamps = rainfall.duplicated(subset=["Station", "Data Acquisition Time"]).sum()
# print("Duplicate (Station + Time) rows:", duplicate_timestamps)

# print("\n" + "="*50 + "\n")

# # 3. >300 wali outliers ka total count (poore dataset me)
# high_outliers = rainfall[rainfall[rain_col] > 300]
# print("Total rows with rainfall > 300mm:", len(high_outliers))
# rainfall["Data Acquisition Time"] = pd.to_datetime(
#     rainfall["Data Acquisition Time"], format="%d-%m-%Y %H:%M", errors="coerce"
# )

# rain_col = "Telemetry Hourly Rainfall (mm)"

# high_values = rainfall[rainfall[rain_col] > 300].copy()
# high_values["hour"] = high_values["Data Acquisition Time"].dt.hour

# print("High-value (>300mm) rows — kis hour pe kitni baar aati hain:")
# print(high_values["hour"].value_counts().sort_index())
rain_col = "Telemetry Hourly Rainfall (mm)"

# Test: agar hum 10 se divide karein, to distribution kaisa dikhta hai
test_divided = rainfall[rain_col] / 10

print("Original stats:")
print(rainfall[rain_col].describe())

print("\nDivided by 10 stats:")
print(test_divided.describe())

print("\nDivided by 10 — kitni values ab bhi 300 se zyada hain:")
print((test_divided > 300).sum(), "out of", len(rainfall))