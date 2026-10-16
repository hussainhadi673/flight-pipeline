"""Transform step: clean, normalise and enrich raw records with pandas."""

import numpy as np
import pandas as pd

from .config import Airport

M_TO_FT = 3.28084
MS_TO_KT = 1.943844

# WMO weather codes -> operational scenario
SCENARIOS = [
    ({95, 96, 99}, "THUNDERSTORM"),
    ({71, 73, 75, 77, 85, 86}, "SNOW"),
    ({56, 57, 66, 67}, "ICE"),
    ({45, 48}, "FOG"),
    ({51, 53, 55, 61, 63, 65, 80, 81, 82}, "WET"),
]


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km. Accepts scalars, arrays or pandas Series."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    h = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(h))


def classify_phase(row: pd.Series, field_elev_ft: float) -> str:
    if row["on_ground"]:
        return "GROUND"
    agl = row["altitude_ft"] - field_elev_ft
    vr = row["vertical_rate_fpm"]
    if row["distance_km"] <= 20 and agl < 3000 and vr < -300:
        return "APPROACH"
    if row["distance_km"] <= 20 and agl < 3000 and vr > 300:
        return "DEPARTURE"
    return "ENROUTE"


def transform_flights(rows: list[dict], airport: Airport) -> pd.DataFrame:
    """Raw OpenSky states -> clean, typed, enriched DataFrame."""
    cols = [
        "snapshot_ts",
        "icao24",
        "callsign",
        "origin_country",
        "latitude",
        "longitude",
        "altitude_ft",
        "speed_kt",
        "heading_deg",
        "vertical_rate_fpm",
        "on_ground",
        "distance_km",
        "phase",
        "airport_iata",
    ]
    if not rows:
        return pd.DataFrame(columns=cols)

    df = pd.DataFrame(rows)
    df = df.dropna(subset=["icao24", "latitude", "longitude"])
    df["icao24"] = df["icao24"].str.lower().str.strip()
    df["callsign"] = df["callsign"].fillna("").str.strip().replace("", pd.NA)
    df["on_ground"] = df["on_ground"].fillna(False).astype(bool)

    alt_m = df["geo_altitude"].fillna(df["baro_altitude"])
    df["altitude_ft"] = (alt_m * M_TO_FT).round(0)
    df.loc[df["on_ground"], "altitude_ft"] = airport.elevation_m * M_TO_FT
    df["speed_kt"] = (df["velocity"] * MS_TO_KT).round(1)
    df["heading_deg"] = df["true_track"].round(0)
    df["vertical_rate_fpm"] = (df["vertical_rate"].fillna(0) * M_TO_FT * 60).round(0)
    df["distance_km"] = haversine_km(airport.lat, airport.lon, df["latitude"], df["longitude"]).round(2)

    df["phase"] = df.apply(classify_phase, axis=1, field_elev_ft=airport.elevation_m * M_TO_FT)
    df["airport_iata"] = airport.iata

    # one row per aircraft per snapshot; keep the freshest contact
    df = df.sort_values("last_contact").drop_duplicates(["snapshot_ts", "icao24"], keep="last")
    return df[cols].reset_index(drop=True)


def weather_scenario(code: int | None, temp_c: float | None) -> str:
    if code is None:
        return "UNKNOWN"
    for codes, label in SCENARIOS:
        if code in codes:
            if label == "WET" and temp_c is not None and temp_c <= 0:
                return "ICE"
            return label
    return "DRY"


def transform_weather(current: dict, airport: Airport) -> pd.DataFrame:
    if not current:
        return pd.DataFrame()
    row = {
        "observed_at": current.get("time"),
        "airport_iata": airport.iata,
        "temperature_c": current.get("temperature_2m"),
        "precipitation_mm": current.get("precipitation"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "visibility_m": current.get("visibility"),
        "weather_code": current.get("weather_code"),
    }
    row["scenario"] = weather_scenario(row["weather_code"], row["temperature_c"])
    return pd.DataFrame([row])
