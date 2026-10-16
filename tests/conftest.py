import pytest

from flight_pipeline.config import get_airport


@pytest.fixture
def zrh():
    return get_airport("ZRH")


@pytest.fixture
def raw_states():
    """Three OpenSky-style rows: approaching, on ground, en route (+ one duplicate)."""
    base = dict(
        origin_country="Switzerland",
        time_position=1,
        sensors=None,
        squawk=None,
        spi=False,
        position_source=0,
        snapshot_ts=1_700_000_000,
    )
    return [
        dict(
            base,
            icao24="4B1805",
            callsign="SWR123  ",
            last_contact=10,
            latitude=47.40,
            longitude=8.50,
            baro_altitude=700,
            geo_altitude=710,
            on_ground=False,
            velocity=75,
            true_track=280,
            vertical_rate=-4,
        ),
        dict(
            base,
            icao24="4b1806",
            callsign="EDW45",
            last_contact=10,
            latitude=47.46,
            longitude=8.55,
            baro_altitude=None,
            geo_altitude=None,
            on_ground=True,
            velocity=5,
            true_track=90,
            vertical_rate=None,
        ),
        dict(
            base,
            icao24="3c6444",
            callsign="",
            last_contact=10,
            latitude=47.90,
            longitude=8.90,
            baro_altitude=11000,
            geo_altitude=11200,
            on_ground=False,
            velocity=240,
            true_track=45,
            vertical_rate=0,
        ),
        dict(
            base,
            icao24="4b1805",
            callsign="SWR123",
            last_contact=12,
            latitude=47.41,
            longitude=8.51,
            baro_altitude=650,
            geo_altitude=660,
            on_ground=False,
            velocity=74,
            true_track=280,
            vertical_rate=-4,
        ),
    ]
