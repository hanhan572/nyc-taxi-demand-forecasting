
# Data Directory

This directory contains instructions for obtaining and managing the datasets used in the project.

## Data Sources

### 1. NYC TLC Yellow Taxi Trip Records

Source:
https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

Format: Parquet

Planned scope: Approximately three months of 2025 data.

Important fields:
- tpep_pickup_datetime
- tpep_dropoff_datetime
- PULocationID
- DOLocationID
- trip_distance
- fare_amount

### 2. NYC Taxi Zone Lookup

Source:
https://data.cityofnewyork.us/Transportation/NYC-Taxi-Zones/8meu-9t5y/about_data

Used to map taxi zone IDs to borough and zone names.

## Local Data Organization

- data/raw/: downloaded source datasets
- data/interim/: intermediate transformation outputs
- data/processed/: cleaned and aggregated datasets

Large datasets are excluded from Git using .gitignore.

## Shared Output Contract

Hourly taxi demand data should include:

| Column | Meaning |
|---|---|
| location_id | NYC taxi pickup zone ID |
| hour | Hourly pickup timestamp |
| pickup_count | Number of pickups during the hour |

## Reproducibility

Data download and transformation scripts will be maintained in src/ingestion/ and src/transformation/.

Detailed execution commands will be added during implementation.
