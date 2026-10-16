"""Load step: idempotent upserts into SQLite (swap the connection for Postgres in prod)."""

import sqlite3
from pathlib import Path

import pandas as pd

SCHEMA = """
CREATE TABLE IF NOT EXISTS flight_snapshots (
    snapshot_ts       INTEGER NOT NULL,
    icao24            TEXT    NOT NULL,
    callsign          TEXT,
    origin_country    TEXT,
    latitude          REAL,
    longitude         REAL,
    altitude_ft       REAL,
    speed_kt          REAL,
    heading_deg       REAL,
    vertical_rate_fpm REAL,
    on_ground         INTEGER,
    distance_km       REAL,
    phase             TEXT,
    airport_iata      TEXT    NOT NULL,
    PRIMARY KEY (snapshot_ts, icao24)
);
CREATE INDEX IF NOT EXISTS ix_flights_airport_ts ON flight_snapshots (airport_iata, snapshot_ts);

CREATE TABLE IF NOT EXISTS weather_observations (
    observed_at      TEXT NOT NULL,
    airport_iata     TEXT NOT NULL,
    temperature_c    REAL,
    precipitation_mm REAL,
    wind_speed_kmh   REAL,
    visibility_m     REAL,
    weather_code     INTEGER,
    scenario         TEXT,
    PRIMARY KEY (observed_at, airport_iata)
);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn


def upsert(conn: sqlite3.Connection, table: str, df: pd.DataFrame) -> int:
    """Insert rows, replacing any existing row with the same primary key."""
    if df.empty:
        return 0
    df = df.astype(object).where(pd.notna(df), None)
    cols = list(df.columns)
    sql = f"INSERT OR REPLACE INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})"
    with conn:
        conn.executemany(sql, df.itertuples(index=False, name=None))
    return len(df)
