"""Data-quality checks run before anything is loaded."""

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class QualityReport:
    rows: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def check_flights(df: pd.DataFrame) -> QualityReport:
    report = QualityReport(rows=len(df))
    if df.empty:
        report.warnings.append("no aircraft in snapshot")
        return report

    dupes = df.duplicated(["snapshot_ts", "icao24"]).sum()
    if dupes:
        report.errors.append(f"{dupes} duplicate (snapshot_ts, icao24) keys")

    bad_coords = (~df["latitude"].between(-90, 90) | ~df["longitude"].between(-180, 180)).sum()
    if bad_coords:
        report.errors.append(f"{bad_coords} rows with invalid coordinates")

    airborne = df[~df["on_ground"]]
    crazy_speed = (airborne["speed_kt"] > 750).sum()
    if crazy_speed:
        report.warnings.append(f"{crazy_speed} airborne rows faster than 750 kt")

    missing_cs = df["callsign"].isna().mean()
    if missing_cs > 0.3:
        report.warnings.append(f"{missing_cs:.0%} of rows missing callsign")
    return report


def check_weather(df: pd.DataFrame) -> QualityReport:
    report = QualityReport(rows=len(df))
    if df.empty:
        report.errors.append("weather payload empty")
        return report
    t = df["temperature_c"].iloc[0]
    if t is None or not -80 <= t <= 60:
        report.errors.append(f"temperature out of range: {t}")
    return report
