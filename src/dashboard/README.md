# Streamlit Dashboard

Initial version of the NYC Taxi Demand Forecasting dashboard.

> **Sample data only.** The dashboard currently uses a small synthetic dataset
> generated in `data_loader.py`. These numbers are **not** real NYC TLC pickups.
> Forecasts are not shown yet ("Forecasting integration coming soon").

## Features (current)

- Sidebar selector for 3 sample taxi zones (132 JFK Airport, 161 Midtown Center, 237 Upper East Side South)
- Line chart of hourly pickup demand
- Summary metrics: total pickups, peak hour, busiest hour of day
- Placeholder for forecasting results

## Data contract

`data_loader.load_hourly_demand()` returns a DataFrame with the shared columns:

| Column | Type |
|---|---|
| location_id | int64 |
| hour | datetime64 |
| pickup_count | int64 (non-negative) |

To switch to PostgreSQL later, implement `_load_from_postgres()` in
`data_loader.py` and call `load_hourly_demand(source="postgres")`.
Credentials must come from environment variables, never hardcoded.

## Run locally

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run src/dashboard/app.py
```

Open http://localhost:8501

## Run with Docker

From the repository root:

```bash
docker build -t nyc-taxi-dashboard .
docker run --rm -p 8501:8501 nyc-taxi-dashboard
```

Open http://localhost:8501

The image installs only `requirements-dashboard.txt` (streamlit, pandas, numpy).

## Tests

```bash
python -m pytest tests/test_dashboard.py -v
```

Use `python -m pytest` (not bare `pytest`) so the repository root is on the
import path for `src.*` imports.

## CI

`.github/workflows/ci.yml` runs on pushes to `main` / `feature/**` and on PRs:

1. Installs `requirements.txt`
2. `compileall` syntax check on `src/` and `tests/`
3. Import check of the dashboard data loader
4. `python -m pytest -v` (all project tests, including a Streamlit `AppTest` smoke test)
5. Builds the Docker image and checks `/_stcore/health`

No API keys or database are required.
