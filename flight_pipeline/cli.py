"""Command-line entry point: python -m flight_pipeline.cli --airport ZRH"""

import argparse
import logging
import sys
import time

from . import extract, load, quality, transform
from .config import get_airport

log = logging.getLogger("flight_pipeline")


def run_once(iata: str, db_path: str) -> int:
    airport = get_airport(iata)

    flights = transform.transform_flights(extract.extract_flights(airport), airport)
    weather = transform.transform_weather(extract.extract_weather(airport), airport)

    exit_code = 0
    with load.connect(db_path) as conn:
        for name, df, check, table in (
            ("flights", flights, quality.check_flights, "flight_snapshots"),
            ("weather", weather, quality.check_weather, "weather_observations"),
        ):
            report = check(df)
            for w in report.warnings:
                log.warning("%s: %s", name, w)
            if not report.ok:
                log.error("%s failed quality checks: %s", name, "; ".join(report.errors))
                exit_code = 1
                continue
            n = load.upsert(conn, table, df)
            log.info("%s: loaded %d rows into %s", name, n, table)

    if not flights.empty:
        log.info("phase breakdown: %s", flights["phase"].value_counts().to_dict())
    return exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Airport traffic & weather ETL")
    parser.add_argument("--airport", default="ZRH", help="IATA code, e.g. ZRH, HAM, ISB")
    parser.add_argument("--db", default="flights.db", help="SQLite database path")
    parser.add_argument("--every", type=int, default=0, help="repeat every N seconds (0 = run once)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    while True:
        code = run_once(args.airport, args.db)
        if not args.every:
            return code
        time.sleep(args.every)


if __name__ == "__main__":
    sys.exit(main())
