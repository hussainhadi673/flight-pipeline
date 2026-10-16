import pandas as pd

from flight_pipeline.quality import check_flights, check_weather
from flight_pipeline.transform import transform_flights


def test_clean_snapshot_passes(raw_states, zrh):
    assert check_flights(transform_flights(raw_states, zrh)).ok


def test_duplicate_keys_fail(raw_states, zrh):
    df = transform_flights(raw_states, zrh)
    report = check_flights(pd.concat([df, df.head(1)]))
    assert not report.ok
    assert "duplicate" in report.errors[0]


def test_bad_coordinates_fail(raw_states, zrh):
    df = transform_flights(raw_states, zrh)
    df.loc[0, "latitude"] = 123.0
    assert not check_flights(df).ok


def test_empty_weather_fails():
    assert not check_weather(pd.DataFrame()).ok
