import pandas as pd

raw = pd.read_csv("data/raw/water_level_narmada_2021_2025.csv", usecols=["Station", "Latitude", "Longitude"])
coords = raw.drop_duplicates(subset=["Station"]).rename(columns={"Station": "station"})
coords.to_csv("data/curated/station_coords.csv", index=False)
print(f"Saved {len(coords)} stations to data/curated/station_coords.csv")