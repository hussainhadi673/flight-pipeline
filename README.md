# flight-pipeline

[![CI](https://github.com/hussainhadi673/flight-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/hussainhadi673/flight-pipeline/actions/workflows/ci.yml)

A small, production-style **ETL pipeline** that collects live air traffic and weather around an airport,
cleans and enriches it with **pandas**, checks data quality, and loads it idempotently into SQL.

It is a public, simplified example of the kind of aviation data pipelines I build professionally
(multi-source flight data, weather, AWS). No client code or data is included.

```
 OpenSky (ADS-B states) ─┐                                     ┌─► flight_snapshots
                         ├─► extract ─► transform ─► quality ─► load (upsert)
 Open-Meteo (weather) ───┘   retries    pandas       checks   └─► weather_observations
```

## What it shows

| Concern | How |
| --- | --- |
| **Extract** | `requests` with exponential-backoff retries on timeouts, 429 and 5xx |
| **Transform** | unit conversion (m → ft, m/s → kt), null handling, de-duplication per snapshot, distance to airport (vectorised haversine), flight-phase classification (GROUND / APPROACH / DEPARTURE / ENROUTE) |
| **Weather** | WMO weather codes → operational scenario (DRY, WET, ICE, SNOW, FOG, THUNDERSTORM) |
| **Data quality** | duplicate keys, coordinate ranges, implausible speeds, missing callsigns — bad batches are not loaded |
| **Load** | idempotent upserts on primary keys, so re-runs never duplicate data |
| **Engineering** | typed modules, pytest suite with mocked HTTP, Ruff lint/format, GitHub Actions CI on Python 3.11 & 3.12 |

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

python -m flight_pipeline.cli --airport ZRH            # run once
python -m flight_pipeline.cli --airport ISB --every 60  # poll every minute
```

Airports: `ZRH`, `HAM`, `LHR`, `ISB`, `DXB` (add more in `flight_pipeline/config.py`).

Example query:

```sql
SELECT phase, COUNT(*) FROM flight_snapshots
WHERE airport_iata = 'ZRH' GROUP BY phase;
```

## Tests

```bash
pytest          # 22 tests, no network needed
ruff check .
```

## Project layout

```
flight_pipeline/
  config.py     airports + endpoints
  extract.py    API clients with retries
  transform.py  pandas cleaning & enrichment
  quality.py    data-quality checks
  load.py       SQLite schema + idempotent upserts
  cli.py        entry point
tests/          unit tests (HTTP mocked)
```

## Taking it to production

The same structure scales up the way I run it at work: swap SQLite for PostgreSQL or DynamoDB,
schedule `run_once` on AWS ECS / Lambda (EventBridge), ship logs to CloudWatch, and add more flight
data providers behind the same `extract` interface.

## License

MIT — Hussain Hadi
