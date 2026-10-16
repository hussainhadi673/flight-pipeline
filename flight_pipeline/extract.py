"""Extract step: pull raw data from public APIs with retries."""

import logging
import time
from typing import Any

import requests

from .config import HTTP_TIMEOUT_S, OPEN_METEO_URL, OPENSKY_URL, Airport

log = logging.getLogger(__name__)

STATE_FIELDS = [
    "icao24",
    "callsign",
    "origin_country",
    "time_position",
    "last_contact",
    "longitude",
    "latitude",
    "baro_altitude",
    "on_ground",
    "velocity",
    "true_track",
    "vertical_rate",
    "sensors",
    "geo_altitude",
    "squawk",
    "spi",
    "position_source",
]


def get_json(
    url: str,
    params: dict[str, Any],
    retries: int = 3,
    backoff_s: float = 2.0,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """GET a JSON endpoint, retrying on network errors, 429 and 5xx."""
    http = session or requests.Session()
    for attempt in range(1, retries + 1):
        try:
            resp = http.get(url, params=params, timeout=HTTP_TIMEOUT_S)
            if resp.status_code == 429 or resp.status_code >= 500:
                raise requests.HTTPError(f"retryable status {resp.status_code}")
            resp.raise_for_status()
            return resp.json()
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as exc:
            if attempt == retries:
                raise
            wait = backoff_s * 2 ** (attempt - 1)
            log.warning("%s failed (%s), retry %d/%d in %.1fs", url, exc, attempt, retries, wait)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def extract_flights(airport: Airport, **kwargs: Any) -> list[dict[str, Any]]:
    """Live aircraft states (ADS-B) in a box around the airport, as dicts."""
    payload = get_json(OPENSKY_URL, airport.bbox(), **kwargs)
    states = payload.get("states") or []
    snapshot_ts = payload.get("time")
    rows = [dict(zip(STATE_FIELDS, s, strict=False)) for s in states]
    for row in rows:
        row["snapshot_ts"] = snapshot_ts
    log.info("Extracted %d aircraft states near %s", len(rows), airport.iata)
    return rows


def extract_weather(airport: Airport, **kwargs: Any) -> dict[str, Any]:
    """Current weather at the airport from Open-Meteo."""
    params = {
        "latitude": airport.lat,
        "longitude": airport.lon,
        "current": "temperature_2m,precipitation,wind_speed_10m,weather_code,visibility",
    }
    payload = get_json(OPEN_METEO_URL, params, **kwargs)
    return payload.get("current", {})
