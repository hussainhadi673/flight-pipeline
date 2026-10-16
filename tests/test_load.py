from flight_pipeline.load import connect, upsert
from flight_pipeline.transform import transform_flights


def test_upsert_is_idempotent(tmp_path, raw_states, zrh):
    df = transform_flights(raw_states, zrh)
    conn = connect(tmp_path / "test.db")
    upsert(conn, "flight_snapshots", df)
    upsert(conn, "flight_snapshots", df)  # running twice must not duplicate
    (count,) = conn.execute("SELECT COUNT(*) FROM flight_snapshots").fetchone()
    assert count == 3


def test_nulls_are_stored_as_null(tmp_path, raw_states, zrh):
    conn = connect(tmp_path / "test.db")
    upsert(conn, "flight_snapshots", transform_flights(raw_states, zrh))
    row = conn.execute("SELECT callsign FROM flight_snapshots WHERE icao24='3c6444'").fetchone()
    assert row == (None,)
