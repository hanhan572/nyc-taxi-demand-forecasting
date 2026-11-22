
"""Unit tests for hourly taxi demand transformation."""

from datetime import datetime

import polars as pl

from src.transformation.clean_taxi_data import build_hourly_demand


def test_hourly_aggregation():
    trips = pl.DataFrame({
        "tpep_pickup_datetime": [
            datetime(2025, 1, 1, 8, 10),
            datetime(2025, 1, 1, 8, 30),
            datetime(2025, 1, 1, 9, 10),
        ],
        "tpep_dropoff_datetime": [
            datetime(2025, 1, 1, 8, 25),
            datetime(2025, 1, 1, 8, 45),
            datetime(2025, 1, 1, 9, 25),
        ],
        "PULocationID": [161, 161, 237],
    }).lazy()

    zones = pl.DataFrame({"LocationID": [161, 237]})

    result = build_hourly_demand(trips, zones)

    assert result.height == 2
    assert result["pickup_count"].sum() == 3

    zone_161 = result.filter(pl.col("location_id") == 161)
    assert zone_161["pickup_count"][0] == 2


def test_invalid_location_removed():
    trips = pl.DataFrame({
        "tpep_pickup_datetime": [
            datetime(2025, 1, 1, 8, 0),
            datetime(2025, 1, 1, 8, 10),
        ],
        "tpep_dropoff_datetime": [
            datetime(2025, 1, 1, 8, 20),
            datetime(2025, 1, 1, 8, 30),
        ],
        "PULocationID": [161, 999],
    }).lazy()

    zones = pl.DataFrame({"LocationID": [161]})

    result = build_hourly_demand(trips, zones)

    assert result.height == 1
    assert result["pickup_count"].sum() == 1


def test_invalid_timing_removed():
    trips = pl.DataFrame({
        "tpep_pickup_datetime": [
            datetime(2025, 1, 1, 8, 30),
        ],
        "tpep_dropoff_datetime": [
            datetime(2025, 1, 1, 8, 10),
        ],
        "PULocationID": [161],
    }).lazy()

    zones = pl.DataFrame({"LocationID": [161]})

    result = build_hourly_demand(trips, zones)

    assert result.is_empty()


def test_correct_output_schema():
    trips = pl.DataFrame({
        "tpep_pickup_datetime": [
            datetime(2025, 1, 1, 8, 0),
        ],
        "tpep_dropoff_datetime": [
            datetime(2025, 1, 1, 8, 10),
        ],
        "PULocationID": [161],
    }).lazy()

    zones = pl.DataFrame({"LocationID": [161]})

    result = build_hourly_demand(trips, zones)

    assert result.columns == [
        "location_id",
        "hour",
        "pickup_count",
    ]
