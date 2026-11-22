
"""Transform NYC taxi trips into hourly pickup demand."""

import argparse
from datetime import datetime
from pathlib import Path

import polars as pl


def build_hourly_demand(
    trips: pl.LazyFrame,
    zones: pl.DataFrame,
    year: int = 2025,
    month: int = 1,
) -> pl.DataFrame:
    """Clean trips and count pickups by location and hour."""

    if not 1 <= month <= 12:
        raise ValueError("Month must be between 1 and 12")

    start = datetime(year, month, 1)
    end = (
        datetime(year + 1, 1, 1)
        if month == 12
        else datetime(year, month + 1, 1)
    )

    valid_zones = (
        zones
        .select(
            pl.col("LocationID")
            .cast(pl.Int64)
            .alias("location_id")
        )
        .unique()
        .lazy()
    )

    cleaned = (
        trips
        .select(
            pl.col("tpep_pickup_datetime")
            .cast(pl.Datetime("us"), strict=False)
            .alias("pickup_time"),
            pl.col("tpep_dropoff_datetime")
            .cast(pl.Datetime("us"), strict=False)
            .alias("dropoff_time"),
            pl.col("PULocationID")
            .cast(pl.Int64, strict=False)
            .alias("location_id"),
        )
        .filter(
            pl.col("pickup_time").is_not_null()
            & pl.col("dropoff_time").is_not_null()
            & pl.col("location_id").is_not_null()
            & (pl.col("pickup_time") >= start)
            & (pl.col("pickup_time") < end)
            & (pl.col("dropoff_time") >= pl.col("pickup_time"))
        )
        .join(
            valid_zones,
            on="location_id",
            how="inner",
        )
        .with_columns(
            pl.col("pickup_time")
            .dt.truncate("1h")
            .alias("hour")
        )
    )

    return (
        cleaned
        .group_by(["location_id", "hour"])
        .agg(pl.len().alias("pickup_count"))
        .sort(["hour", "location_id"])
        .collect()
    )


def main(year: int, month: int) -> None:
    filename = f"yellow_tripdata_{year}-{month:02d}.parquet"

    raw_path = Path("data/raw") / filename
    zone_path = Path("data/raw/taxi_zone_lookup.csv")
    output_path = (
        Path("data/processed")
        / f"hourly_demand_{year}-{month:02d}.parquet"
    )

    if not raw_path.exists():
        raise FileNotFoundError(raw_path)

    if not zone_path.exists():
        raise FileNotFoundError(zone_path)

    trips = pl.scan_parquet(raw_path)
    zones = pl.read_csv(zone_path)

    result = build_hourly_demand(
        trips,
        zones,
        year=year,
        month=month,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.write_parquet(output_path)

    print("Transformation completed successfully!")
    print(f"Output: {output_path}")
    print(f"Rows: {result.height}")
    print(f"Total valid pickups: {result['pickup_count'].sum()}")
    print(result.head(10))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--month", type=int, default=1)
    args = parser.parse_args()

    main(args.year, args.month)
