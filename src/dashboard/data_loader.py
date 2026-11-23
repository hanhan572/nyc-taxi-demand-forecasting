"""Data loading for the Streamlit dashboard.

The dashboard only depends on the shared hourly-demand contract:

    location_id (int), hour (datetime), pickup_count (int)

Today the only implemented source is a small SYNTHETIC sample generated in
code. It is NOT real NYC TLC data. When the PostgreSQL module is ready,
implement ``_load_from_postgres`` and the rest of the dashboard should not
need to change.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ["location_id", "hour", "pickup_count"]

SAMPLE_DATA_LABEL = (
    "SAMPLE DATA: synthetic values generated in code for development only. "
    "These are NOT real NYC TLC pickup counts."
)

# Zone names verified against the official TLC taxi_zone_lookup.csv.
SAMPLE_ZONES = {
    132: "JFK Airport (Queens)",
    161: "Midtown Center (Manhattan)",
    237: "Upper East Side South (Manhattan)",
}

# Rough synthetic daily scale per zone (purely illustrative).
_SAMPLE_SCALE = {132: 180, 161: 260, 237: 140}


def load_sample_demand(
    start: str = "2025-01-06",
    days: int = 3,
    seed: int = 706,
) -> pd.DataFrame:
    """Return a small, deterministic synthetic hourly-demand dataset."""
    rng = np.random.default_rng(seed)
    hours = pd.date_range(start=start, periods=days * 24, freq="h")
    hour_of_day = hours.hour.to_numpy()

    # Two-peak daily shape (morning + evening), low overnight.
    shape = (
        0.15
        + 0.6 * np.exp(-((hour_of_day - 8) ** 2) / 6)
        + 0.8 * np.exp(-((hour_of_day - 18) ** 2) / 8)
    )

    frames = []
    for location_id, scale in _SAMPLE_SCALE.items():
        noise = rng.normal(1.0, 0.08, size=len(hours)).clip(0.7, 1.3)
        counts = np.round(scale * shape * noise).astype("int64")
        frames.append(
            pd.DataFrame(
                {
                    "location_id": location_id,
                    "hour": hours,
                    "pickup_count": counts,
                }
            )
        )

    df = pd.concat(frames, ignore_index=True)
    df["location_id"] = df["location_id"].astype("int64")
    return validate_demand(df)


def _load_from_postgres() -> pd.DataFrame:
    """Placeholder for the database integration (not implemented yet)."""
    raise NotImplementedError(
        "PostgreSQL loading is not implemented yet. "
        "Use source='sample' until the database module is ready."
    )


def load_hourly_demand(source: str = "sample") -> pd.DataFrame:
    """Load hourly demand from the requested source."""
    if source == "sample":
        return load_sample_demand()
    if source == "postgres":
        return validate_demand(_load_from_postgres())
    raise ValueError(f"Unknown data source: {source!r}")


def validate_demand(df: pd.DataFrame) -> pd.DataFrame:
    """Check the shared data contract and return a sorted copy."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if df[REQUIRED_COLUMNS].isnull().any().any():
        raise ValueError("Demand data contains null values")

    if not pd.api.types.is_datetime64_any_dtype(df["hour"]):
        raise TypeError("Column 'hour' must be a datetime type")

    if (df["pickup_count"] < 0).any():
        raise ValueError("pickup_count must be non-negative")

    if df.duplicated(subset=["location_id", "hour"]).any():
        raise ValueError("Duplicate (location_id, hour) keys found")

    return (
        df[REQUIRED_COLUMNS]
        .sort_values(["location_id", "hour"])
        .reset_index(drop=True)
    )


def summarize_zone(df: pd.DataFrame, location_id: int) -> dict:
    """Return simple summary statistics for one zone."""
    zone = df[df["location_id"] == location_id]
    if zone.empty:
        raise ValueError(f"No data for location_id={location_id}")

    peak_row = zone.loc[zone["pickup_count"].idxmax()]
    by_hour_of_day = zone.groupby(zone["hour"].dt.hour)["pickup_count"].mean()

    return {
        "total_pickups": int(zone["pickup_count"].sum()),
        "peak_hour": peak_row["hour"],
        "peak_pickups": int(peak_row["pickup_count"]),
        "busiest_hour_of_day": int(by_hour_of_day.idxmax()),
        "hours_covered": int(zone["hour"].nunique()),
    }
