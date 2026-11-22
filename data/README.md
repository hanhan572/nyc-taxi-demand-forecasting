
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

## Implemented Data Pipeline — Week 1

### Dataset

- Source: NYC TLC Yellow Taxi Trip Records
- Period: January 2025
- Raw trip records: 3,475,226
- Taxi zone lookup records: 265

### Data Ingestion

Download the source datasets:

```bash
python src/ingestion/download_data.py --year 2025 --month 1
```

Files are stored in `data/raw/` and excluded from Git.

### Data Transformation

Run the Polars transformation:

```bash
python src/transformation/clean_taxi_data.py --year 2025 --month 1
```

The pipeline:

1. Selects pickup time, dropoff time, and pickup zone ID.
2. Removes missing and invalid records.
3. Restricts pickups to January 2025.
4. Validates pickup zone IDs against Taxi Zone Lookup.
5. Aggregates pickup counts by location and hour.
6. Saves the processed results as Parquet.

### Verified Results

| Metric | Result |
|---|---:|
| Raw taxi trips | 3,475,226 |
| Valid pickup records | 3,475,080 |
| Excluded records | 146 |
| Aggregated zone-hour rows | 96,989 |
| Unique pickup zones | 261 |
| Null values in output | 0 |
| Duplicate zone-hour keys | 0 |

The 146 excluded records are the combined result of the filtering and zone-validation rules. The individual reasons have not yet been separately counted.

### Output Schema

File:

`data/processed/hourly_demand_2025-01.parquet`

| Column | Polars Type | Description |
|---|---|---|
| location_id | Int64 | Taxi pickup zone ID |
| hour | Datetime(us) | Pickup hour |
| pickup_count | UInt32 | Number of valid pickups |

The dataset contains only observed zone-hour combinations. Missing combinations are not automatically filled with zero.

The source timestamps are treated as local timestamps without timezone conversion.

### Testing

Run:

```bash
python -m pytest tests/test_transformation.py -v
```

Verified result: 4 tests passed.

Tests cover:

- Hourly aggregation correctness
- Invalid pickup location filtering
- Invalid trip timing filtering
- Output schema validation

### Downstream Integration

Database and ML modules should use the shared data contract:

`location_id, hour, pickup_count`

Database integration should preserve the timestamp type and enforce a unique key on `(location_id, hour)`.

Forecasting models should account for missing zero-demand hours and use chronological train/test splits.

### Future Work

- Extend processing to additional months of 2025.
- Add detailed data-quality rejection statistics.
- Integrate PostgreSQL storage.
- Add Airflow orchestration.
- Add end-to-end pipeline tests.
