import pytest

from flight_pipeline.transform import (
    haversine_km,
    transform_flights,
    transform_weather,
    weather_scenario,
)


def test_haversine_known_distance():
    # Zurich -> Hamburg is ~693 km
    assert haversine_km(47.4647, 8.5492, 53.6304, 9.9882) == pytest.approx(693, abs=5)


def test_transform_dedupes_and_keeps_latest_contact(raw_states, zrh):
    df = transform_flights(raw_states, zrh)
    assert len(df) == 3
    swr = df[df["icao24"] == "4b1805"].iloc[0]
    assert swr["latitude"] == 47.41  # the later contact won


def test_transform_normalises_fields(raw_states, zrh):
    df = transform_flights(raw_states, zrh).set_index("icao24")
    assert df.loc["4b1805", "callsign"] == "SWR123"
    assert df.isna().loc["3c6444", "callsign"]  # empty callsign -> NA
    assert df.loc["3c6444", "speed_kt"] == pytest.approx(466.5, abs=0.1)


def test_flight_phases(raw_states, zrh):
    phases = transform_flights(raw_states, zrh).set_index("icao24")["phase"].to_dict()
    assert phases == {"4b1805": "APPROACH", "4b1806": "GROUND", "3c6444": "ENROUTE"}


def test_empty_snapshot_returns_empty_frame(zrh):
    df = transform_flights([], zrh)
    assert df.empty and "phase" in df.columns


@pytest.mark.parametrize(
    ("code", "temp", "expected"),
    [
        (0, 15, "DRY"),
        (61, 10, "WET"),
        (61, -2, "ICE"),
        (45, 5, "FOG"),
        (73, -5, "SNOW"),
        (95, 20, "THUNDERSTORM"),
        (None, 10, "UNKNOWN"),
    ],
)
def test_weather_scenario(code, temp, expected):
    assert weather_scenario(code, temp) == expected


def test_transform_weather(zrh):
    df = transform_weather(
        {
            "time": "2026-10-16T10:00",
            "temperature_2m": 9.5,
            "precipitation": 1.2,
            "wind_speed_10m": 14,
            "weather_code": 63,
            "visibility": 8000,
        },
        zrh,
    )
    assert df.iloc[0]["scenario"] == "WET"
    assert df.iloc[0]["airport_iata"] == "ZRH"
