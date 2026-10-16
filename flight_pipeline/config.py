"""Static configuration: airports and API endpoints."""

from dataclasses import dataclass

OPENSKY_URL = "https://opensky-network.org/api/states/all"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
HTTP_TIMEOUT_S = 20


@dataclass(frozen=True)
class Airport:
    iata: str
    name: str
    lat: float
    lon: float
    elevation_m: float

    def bbox(self, radius_deg: float = 0.5) -> dict[str, float]:
        """Bounding box around the airport for the OpenSky query."""
        return {
            "lamin": self.lat - radius_deg,
            "lamax": self.lat + radius_deg,
            "lomin": self.lon - radius_deg,
            "lomax": self.lon + radius_deg,
        }


AIRPORTS: dict[str, Airport] = {
    "ZRH": Airport("ZRH", "Zurich", 47.4647, 8.5492, 432),
    "HAM": Airport("HAM", "Hamburg", 53.6304, 9.9882, 16),
    "LHR": Airport("LHR", "London Heathrow", 51.4700, -0.4543, 25),
    "ISB": Airport("ISB", "Islamabad", 33.5491, 72.8256, 520),
    "DXB": Airport("DXB", "Dubai", 25.2532, 55.3657, 19),
}


def get_airport(iata: str) -> Airport:
    try:
        return AIRPORTS[iata.upper()]
    except KeyError as exc:
        known = ", ".join(sorted(AIRPORTS))
        raise ValueError(f"Unknown airport '{iata}'. Known: {known}") from exc
