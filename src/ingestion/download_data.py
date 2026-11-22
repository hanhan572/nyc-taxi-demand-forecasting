
"""Download NYC TLC Yellow Taxi trip and zone lookup datasets."""

import argparse
from pathlib import Path
from urllib.request import urlretrieve

BASE_URL = "https://d37ci6vzurychx.cloudfront.net"
RAW_DIR = Path("data/raw")


def download_file(url: str, destination: Path) -> None:
    """Download file unless it already exists."""
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists() and destination.stat().st_size > 0:
        print(f"Already exists: {destination}")
        return

    temp_path = destination.with_name(destination.name + ".part")
    print(f"Downloading: {url}")

    try:
        urlretrieve(url, temp_path)
        temp_path.replace(destination)
    finally:
        temp_path.unlink(missing_ok=True)

    print(f"Saved: {destination}")


def download_taxi_data(year: int, month: int) -> None:
    if not 1 <= month <= 12:
        raise ValueError("Month must be between 1 and 12")

    filename = f"yellow_tripdata_{year}-{month:02d}.parquet"

    download_file(
        f"{BASE_URL}/trip-data/{filename}",
        RAW_DIR / filename,
    )


def download_zone_lookup() -> None:
    download_file(
        f"{BASE_URL}/misc/taxi_zone_lookup.csv",
        RAW_DIR / "taxi_zone_lookup.csv",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--month", type=int, default=1)
    args = parser.parse_args()

    download_taxi_data(args.year, args.month)
    download_zone_lookup()
