import pytest
import requests

from flight_pipeline import extract


class FakeResponse:
    def __init__(self, status, payload=None):
        self.status_code = status
        self._payload = payload or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def get(self, url, params=None, timeout=None):
        self.calls += 1
        return self.responses.pop(0)


def test_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr(extract.time, "sleep", lambda s: None)
    session = FakeSession([FakeResponse(503), FakeResponse(429), FakeResponse(200, {"ok": 1})])
    assert extract.get_json("http://x", {}, session=session) == {"ok": 1}
    assert session.calls == 3


def test_gives_up_after_max_retries(monkeypatch):
    monkeypatch.setattr(extract.time, "sleep", lambda s: None)
    session = FakeSession([FakeResponse(500)] * 3)
    with pytest.raises(requests.HTTPError):
        extract.get_json("http://x", {}, session=session)


def test_extract_flights_maps_fields(monkeypatch, zrh):
    state = [
        "abc123",
        "TEST1 ",
        "CH",
        1,
        2,
        8.5,
        47.4,
        1000.0,
        False,
        100.0,
        90.0,
        0.0,
        None,
        1010.0,
        None,
        False,
        0,
    ]
    monkeypatch.setattr(extract, "get_json", lambda *a, **k: {"time": 99, "states": [state]})
    rows = extract.extract_flights(zrh)
    assert rows[0]["icao24"] == "abc123"
    assert rows[0]["latitude"] == 47.4
    assert rows[0]["snapshot_ts"] == 99
