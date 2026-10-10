import sqlite3
import pandas as pd
import datetime


def get_connection():
    """Database se connection deta hai."""
    return sqlite3.connect("floodguard.db")


def initialize_database():
    """Sabhi zaroori tables banata hai (agar pehle se nahi hain to)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stations (
            station_name TEXT PRIMARY KEY,
            river TEXT,
            latitude REAL,
            longitude REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS thresholds (
            station_name TEXT PRIMARY KEY,
            watch_threshold REAL,
            warning_threshold REAL,
            danger_threshold REAL,
            last_updated TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_name TEXT,
            severity TEXT,
            water_level REAL,
            opened_at TEXT,
            status TEXT DEFAULT 'open',
            acknowledged_by TEXT,
            notes TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor TEXT,
            action TEXT,
            details TEXT,
            occurred_at TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialized: floodguard.db")


def sync_alerts(all_status):
    """Jo stations Normal nahi hain, unke liye naya alert banao (agar already open nahi hai)."""
    conn = get_connection()
    cursor = conn.cursor()

    for station_data in all_status:
        station = station_data["station"]
        risk = station_data["current_risk"]

        if risk == "Normal":
            continue

        cursor.execute(
            "SELECT alert_id FROM alerts WHERE station_name = ? AND status = 'open'",
            (station,)
        )
        existing = cursor.fetchone()

        if existing is None:
            cursor.execute(
                "INSERT INTO alerts (station_name, severity, water_level, opened_at, status) VALUES (?, ?, ?, ?, 'open')",
                (station, risk, station_data["current_level"], datetime.datetime.now().isoformat())
            )

    conn.commit()
    conn.close()


def get_open_alerts():
    """Sabhi 'open' alerts ko ek table me deta hai."""
    conn = get_connection()
    df = pd.read_sql(
        "SELECT * FROM alerts WHERE status = 'open' ORDER BY severity DESC, opened_at DESC",
        conn
    )
    conn.close()
    return df


def acknowledge_alert(alert_id, acknowledged_by, note):
    """Ek alert ko acknowledge karta hai aur audit log banata hai."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE alerts SET acknowledged_by = ?, notes = ? WHERE alert_id = ?",
        (acknowledged_by, note, alert_id)
    )
    cursor.execute(
        "INSERT INTO audit_events (actor, action, details, occurred_at) VALUES (?, ?, ?, ?)",
        (acknowledged_by, "acknowledge_alert", f"Alert {alert_id}: {note}", datetime.datetime.now().isoformat())
    )

    conn.commit()
    conn.close()


def close_alert(alert_id, closed_by):
    """Ek alert ko close karta hai."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE alerts SET status = 'closed' WHERE alert_id = ?", (alert_id,))
    cursor.execute(
        "INSERT INTO audit_events (actor, action, details, occurred_at) VALUES (?, ?, ?, ?)",
        (closed_by, "close_alert", f"Alert {alert_id} closed", datetime.datetime.now().isoformat())
    )

    conn.commit()
    conn.close()


def get_all_thresholds():
    """Sabhi stations ke thresholds deta hai."""
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM thresholds", conn)
    conn.close()
    return df


def update_threshold(station_name, watch, warning, danger, updated_by):
    """Ek station ka threshold update karta hai aur audit log banata hai."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE thresholds SET watch_threshold = ?, warning_threshold = ?, danger_threshold = ?, last_updated = ? WHERE station_name = ?",
        (watch, warning, danger, datetime.datetime.now().isoformat(), station_name)
    )
    cursor.execute(
        "INSERT INTO audit_events (actor, action, details, occurred_at) VALUES (?, ?, ?, ?)",
        (updated_by, "update_threshold", f"{station_name}: watch={watch}, warning={warning}, danger={danger}", datetime.datetime.now().isoformat())
    )

    conn.commit()
    conn.close()


def get_audit_log(limit=50):
    """Recent audit events deta hai."""
    conn = get_connection()
    df = pd.read_sql(f"SELECT * FROM audit_events ORDER BY occurred_at DESC LIMIT {int(limit)}", conn)
    conn.close()
    return df

def ensure_database():
    """Fresh start par tables banata hai, aur thresholds khaali ho to CSV se bharta hai."""
    initialize_database()
    conn = get_connection()
    count = pd.read_sql("SELECT COUNT(*) AS n FROM thresholds", conn)["n"][0]
    if count == 0:
        thresholds_df = pd.read_csv("data/curated/station_thresholds.csv")
        thresholds_df = thresholds_df.rename(columns={"station": "station_name"})
        thresholds_df["last_updated"] = pd.Timestamp.now().isoformat()
        thresholds_df.to_sql("thresholds", conn, if_exists="append", index=False)
    conn.close()


ensure_database()

if __name__ == "__main__":
    initialize_database()

    df = pd.read_parquet("data/curated/flood_data_clean.parquet")
    stations_info = df[["station"]].drop_duplicates().rename(columns={"station": "station_name"})

    conn = get_connection()
    stations_info.to_sql("stations", conn, if_exists="replace", index=False)
    print(f"Inserted {len(stations_info)} stations")

    thresholds_df = pd.read_csv("data/curated/station_thresholds.csv")
    thresholds_df["last_updated"] = pd.Timestamp.now().isoformat()
    thresholds_df.rename(columns={"station": "station_name"}, inplace=True)
    thresholds_df.to_sql("thresholds", conn, if_exists="replace", index=False)
    print(f"Inserted {len(thresholds_df)} threshold records")

    sample = pd.read_sql("SELECT * FROM thresholds LIMIT 5", conn)
    print("\nSample from thresholds table:")
    print(sample.to_string())
    conn.close()