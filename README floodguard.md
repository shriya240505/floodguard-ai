# FloodGuard AI

Flood-risk decision-support dashboard for the Narmada Basin, Madhya Pradesh. Built with Streamlit, XGBoost and SQLite on public hydrological data.

> **This is a prototype, not an official warning system.** It does not replace government agencies, field verification or human judgment. Forecasts can be wrong, and the risk thresholds used here are derived from historical data, not set by any authority.

## What it does

- Shows the current water-level status of 66 gauge stations in the Narmada Basin (Madhya Pradesh), with 1-hour, 3-hour and 6-hour forecasts for each.
- Classifies each station as Normal, Watch, Warning or Danger using per-station thresholds.
- Explains an individual forecast with SHAP.
- Lets an operator acknowledge and close alerts, and edit thresholds, with every action written to an audit log.

## Pages

| Page | What it shows |
|---|---|
| Dashboard (`app.py`) | Count of stations per risk level, and a table of current level, current risk, 1h/3h/6h forecast risk and a data-freshness flag |
| Station Detail | Station picker with three tabs: Overview (current level, risk, forecasts), History (last 30 days), and "Why this forecast?" (SHAP contributions for the 1-hour model) |
| Alert Center | Open alerts filtered by severity; acknowledge with a name and note, or close. Backed by SQLite |
| Map Explorer | Folium map of stations, coloured by current risk |
| Analytics | Model comparison table and a forecast-vs-actual backtest chart per station |
| Governance | Editable threshold table (validated, logged) and the audit log |

## Data

| Dataset | Source | Used for |
|---|---|---|
| River water level, manual hourly, Narmada basin | Central Water Commission (CWC), via the National Water Data Portal (NWIC, Ministry of Jal Shakti) | Forecast target and lag features. 76 stations in the file, 68 in Madhya Pradesh |
| Rainfall, telemetry hourly, Madhya Pradesh | National Water Data Portal, Narmada Control Authority (NCA) dataset | Rainfall features. 38 stations |

Terms: the portal's [Copyright Policy](https://nwdp.nwic.gov.in/en/footer/copyrightPolicy) allows free reproduction in any format provided the material is reproduced accurately, is not used in a derogatory or misleading way, and the source is prominently acknowledged. Per the portal's [Disclaimer](https://nwdp.nwic.gov.in/en/footer/disclaimer), NWIC does not warrant the accuracy or completeness of the data, which comes from the producing agencies. The values used in this project were cleaned, rescaled and interpolated (see "Data preparation") and are **not official figures**.

The raw CSVs (about 50 MB and 270 MB) are not included in this repository. Download them from the portal (see "Running locally").

### Data preparation

1. **Rainfall unit fix.** Raw rainfall values were about 10x too high to be hourly millimetres (maximum about 1,022 "mm" in one hour). Dividing by 10 gave a plausible distribution (maximum 102 mm). This is an inference from the distribution; it has not been confirmed from the provider's documentation. Negative readings (45 rows) were set to 0, and duplicate station-time rows were removed.
2. **Water level.** Restricted to stations in Madhya Pradesh (this dropped Gujarat stations further down the river). Outliers were removed per station using the 1.5 x IQR rule, and duplicate station-time rows were removed.
3. **Station matching.** Water-level and rainfall stations do not share names, so each water-level station is paired with the nearest rainfall station by Haversine distance (median about 15 km, maximum 56 km).
4. **Hourly timeline and gaps.** Each station was put on a continuous hourly timeline. Gaps of up to 6 hours were filled by linear interpolation; longer gaps were left missing and those rows dropped.
5. **Excluded station.** "Mukki" was removed: its level drops by roughly 139 m in 2025, which is physically implausible and looks like a datum or sensor change. A check for train/test range shifts above 10 m found no other station with this problem.

Result: 66 stations and 606,915 hourly rows (about March 2022 to December 2025).

## Models

- **Task:** predict the change in water level (future level minus current level) at +1h, +3h and +6h, one XGBoost model per horizon. Predicting the change rather than the absolute level fixed a large error caused by stations sitting at very different absolute levels (about 139 m to 739 m).
- **Features:** current level, levels 1/2/3 hours ago, short-term trend, current rainfall, rainfall 1 hour ago, rainfall total over the previous 6 hours, and an encoded station identifier.
- **Settings:** `n_estimators=200`, `max_depth=6`, `learning_rate=0.1`, `random_state=42`.
- **Split:** chronological 80/20 with one global split date (2024-08-12). 485,378 training rows, 121,339 test rows.
- **Baselines:** persistence (the future level equals the current level) and linear regression on the same features and target.
- **Tracking:** each training run is logged to MLflow (`floodguard_forecasting` experiment, run `xgb_delta_v1`), including parameters, metrics and the saved models.

### Results (held-out test period, meters)

| Horizon | MAE: Persistence | MAE: Linear reg. | MAE: XGBoost | RMSE: Persistence | RMSE: Linear reg. | RMSE: XGBoost |
|---|---|---|---|---|---|---|
| 1 hour | **0.0128** | 0.0178 | 0.0193 | 0.0869 | 0.0853 | **0.0830** |
| 3 hour | **0.0355** | 0.0494 | 0.0506 | 0.1642 | 0.1605 | **0.1521** |
| 6 hour | **0.0656** | 0.0916 | 0.0979 | 0.2514 | 0.2431 | **0.2419** |

How to read this:

- On all test rows, **persistence has the lowest MAE** at every horizon. XGBoost's MAE is higher by about 0.7 cm (1h), 1.5 cm (3h) and 3.2 cm (6h).
- XGBoost has the **lowest RMSE**, by roughly 4 to 7 percent, which means it makes fewer large errors. This is one run on one split with no confidence intervals, so differences this small may not hold on other splits.
- **During high rainfall** (hourly rainfall above 34.39 mm, 20,471 of 121,284 test rows, 1-hour horizon), persistence and XGBoost are effectively tied: MAE 0.0121 vs 0.0124.

### Rows where the level actually changed by more than 0.1 m

| Horizon | Rows (of test total) | MAE: Persistence | MAE: XGBoost |
|---|---|---|---|
| 1 hour | 4,745 of 121,284 | 0.2682 | 0.2266 |
| 3 hour | 15,172 of 121,174 | 0.3066 | 0.2380 |
| 6 hour | 26,435 of 121,009 | 0.3599 | 0.2972 |

XGBoost's MAE is about 15 to 22 percent lower on these rows. **Important caveat:** this slice is selected using the realised outcome. Persistence always predicts "no change", so it is guaranteed to do badly on rows where a change happened. This result shows that XGBoost captures part of real rises and falls; it does not show that the system would give useful early warning, because it says nothing about false alarms in quiet periods. A threshold-crossing evaluation (lead time, false alerts, missed events) has not been done.

## Risk thresholds and governance

- Per-station thresholds are the 70th (Watch), 90th (Warning) and 97th (Danger) percentiles of that station's own historical water level. **They are not official flood levels.**
- Thresholds are stored in SQLite and editable on the Governance page. A save is rejected unless `watch <= warning <= danger` for every station, and each accepted change is written to the audit log.
- The dashboard, Alert Center and Map read thresholds from SQLite, so an edit changes the displayed risk.
- Alerts are created for stations that are not Normal when no open alert exists for them. Acknowledge and close actions are written to the audit log.

## Explainability

The Station Detail page shows SHAP values (TreeExplainer) for the 1-hour model at a station's latest reading, labelled in plain language. SHAP shows how much each feature contributed to the model's output. It does not show causes, and it does not show that the forecast is correct.

## Model card

- **Intended use:** a prototype for exploring flood-risk monitoring and decision support in the Narmada Basin, for learning and demonstration.
- **Not intended for:** issuing public warnings, replacing official forecasts, or any operational decision without verification against official sources.
- **Training data:** the two datasets above, 2022 to 2025, 66 stations.
- **Evaluation:** one chronological split; MAE and RMSE overall, under high rainfall, and on rows with a realised change above 0.1 m (see above).
- **Known weaknesses:** no uncertainty estimates (none are shown); no threshold-crossing evaluation; accuracy for extreme floods is untested because the evaluation period contains few extreme events; performance at stations outside the 66 is unknown.

## Limitations

1. **Historical replay, not live.** Data ends in December 2025. The dashboard shows each station's last available reading, and a freshness flag marks stations whose latest reading is more than 45 days older than the typical station. There is no ingestion job.
2. **Rainfall assumptions are unverified.** Besides the unit inference above, rainfall rows appear to be logged mainly when rain occurred (dry hours seem to be absent), and gaps of up to 6 hours were linearly interpolated, which may create rain in dry periods. The average of recorded hourly values (22.7 mm) is also high for a complete hourly series. Rainfall units and logging rules should be checked against the provider's documentation.
3. **Interpolated values are not flagged** in the data.
4. **Nearest-station rainfall matching** ignores upstream and downstream relationships between stations.
5. **Thresholds are statistical, not official** (see above).
6. **Basic access control only.** Alert actions and threshold edits require one shared admin password (stored in Streamlit Secrets). There are no individual accounts, so names typed into the audit log are not verified, and there is no limit on password attempts.
7. **Open alerts keep their original severity** if thresholds are edited afterwards.
8. **Analytics numbers are typed into the page**, copied from the MLflow run. Retraining does not update that table automatically.
9. **Single run, single split.** No cross-validation or confidence intervals.

## Project structure

```
app.py                  Dashboard
pages/                  Station Detail, Alert Center, Map Explorer, Analytics, Governance
src/data_pipeline.py    Cleaning, station matching, merge -> data/curated/flood_data_clean.parquet
src/risk_engine.py      Percentile thresholds and risk classification
src/database.py         SQLite tables and helper functions (alerts, thresholds, audit log)
src/theme.py            Styling
models/train.py         Baselines, XGBoost training, evaluation, MLflow logging
models/predict.py       Forecasting, SHAP and backtest helpers
models/artifacts/       Saved models and station encoder
.streamlit/config.toml  Theme
```

## Running locally

```bash
conda create -n floodguard python=3.11 -y
conda activate floodguard
pip install -r requirements.txt
Training also needs MLflow: pip install mlflow
```

1. Download the two datasets from the National Water Data Portal (https://nwdp.nwic.gov.in) and save them as `data/raw/           water_level_narmada_2021_2025.csv` and `data/raw/rainfall_nca_mp_2021_2025.csv`.
2. Build the cleaned dataset: `python src/data_pipeline.py`
3. Save station coordinates for the map: python make_station_coords.py
4. Compute thresholds: `python src/risk_engine.py`
5. Create the database: `python src/database.py` (run this once only; running it again resets the thresholds table and discards edits)
6. Train and log models: `python models/train.py`
7. Start the app: `streamlit run app.py`
8. Optional, view experiments: `mlflow ui` (run from the project root)

## Data attribution
Water-level data: Central Water Commission (CWC). Rainfall data: Narmada Control Authority (NCA). Both obtained from the National Water Data Portal, National Water Informatics Centre, Ministry of Jal Shakti, Government of India. This project is independent and is not endorsed by these organisations.