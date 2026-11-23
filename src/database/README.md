# PostgreSQL database foundation

This module stores the aggregated taxi data produced by the ingestion and Polars
transformation modules. It provides four tables, an ERD, four analytical queries,
and SQL integration tests. It does not load raw trip records or train models.

## Files

- `sql/schema.sql`: transactional, repeatable initialization.
- `sql/queries.sql`: zone rankings, hourly patterns, borough totals, and weekday/weekend comparisons.
- `sql/test_data.sql`: explicitly synthetic fixtures for a dedicated test database.
- `tests/test_database.sql`: SQL assertions and expected constraint failures; test mutations roll back.
- [ERD](../../docs/erd.md): table columns, keys, and relationships.

## Run locally with Docker

Run these commands from the repository root. Docker Desktop must be running.
PostgreSQL is local; no cloud account, paid service, or AI API key is needed.
Choose a local development password when prompted; do not put it in Git.

```bash
read -s POSTGRES_PASSWORD
export POSTGRES_PASSWORD
docker run -d --name nyc-taxi-postgres \
  -e POSTGRES_PASSWORD -e POSTGRES_DB=taxi \
  -p 127.0.0.1:5433:5432 \
  -v nyc-taxi-pgdata:/var/lib/postgresql/data \
  postgres:16-alpine
unset POSTGRES_PASSWORD
docker exec nyc-taxi-postgres pg_isready -U postgres -d taxi
```

Wait until `pg_isready` reports accepting connections, then initialize:

```bash
docker exec -i nyc-taxi-postgres psql -X -U postgres -d taxi \
  -v ON_ERROR_STOP=1 < sql/schema.sql
```

If the named container already exists, use `docker start nyc-taxi-postgres`
instead of running `docker run` again. The named volume preserves local data.
For host Python clients use host `localhost`, port `5433`, database `taxi`, user
`postgres`, and the password you chose through environment variables. Never
commit a real connection string. Other containers need a shared Docker network
and the database service name rather than `localhost`; that deployment setup
belongs to the project's Docker integration.

### Run the sample and tests separately from real data

Create the test database once; reuse it on later runs:

```bash
docker exec nyc-taxi-postgres createdb -U postgres taxi_schema_test
docker exec -i nyc-taxi-postgres psql -X -U postgres -d taxi_schema_test \
  -v ON_ERROR_STOP=1 < sql/schema.sql
docker exec -i nyc-taxi-postgres psql -X -U postgres -d taxi_schema_test \
  -v ON_ERROR_STOP=1 < sql/test_data.sql
docker exec -i nyc-taxi-postgres psql -X -U postgres -d taxi_schema_test \
  -v ON_ERROR_STOP=1 < tests/test_database.sql
docker exec -i nyc-taxi-postgres psql -X -U postgres -d taxi_schema_test \
  -v ON_ERROR_STOP=1 < sql/queries.sql
```

These are real PostgreSQL integration tests, not pytest tests. They are run
explicitly using `psql`; `python -m pytest` does not discover `.sql` files.
Successful verification ends with `PASS: database fixtures, constraints, upsert
and model-run isolation`. `ON_ERROR_STOP=1` makes failures return a nonzero exit.

When finished, `docker stop nyc-taxi-postgres` stops local compute while keeping
the database in its named volume.

## Integration contract

Load the zone lookup first. Map its columns as follows:

| Upstream CSV | PostgreSQL `taxi_zones` |
|---|---|
| `LocationID` | `location_id` |
| `Borough` | `borough` |
| `Zone` | `zone` |
| `service_zone` | `service_zone` |

Then load the processed Parquet columns unchanged:

| Column | SQL type | Rule |
|---|---|---|
| `location_id` | `INTEGER` | Must exist in `taxi_zones` |
| `hour` | `TIMESTAMP WITHOUT TIME ZONE` | Finite, exactly on an hour boundary |
| `pickup_count` | `BIGINT` | Nonnegative; supports upstream `UInt32` range |

The `(location_id, hour)` primary key prevents duplicate observations. A loader
can use the following parameterized pattern to replace a recomputed count:

```sql
INSERT INTO public.hourly_demand (location_id, hour, pickup_count)
VALUES (%s, %s, %s)
ON CONFLICT (location_id, hour) DO UPDATE
SET pickup_count = EXCLUDED.pickup_count;
```

`%s` is a psycopg parameter placeholder, not literal SQL for `psql`. Pass values
separately to the driver. Do not add new counts to old counts when replaying the
same batch. Upserting does not remove stale keys if a recomputed month has fewer
rows; a future full-month loader should replace that month atomically in a
transaction. The Parquet loader is not implemented in this foundation.

`model_metrics` stores one model name, one training/evaluation window, MAE, RMSE,
and the number of evaluated zone-hours per run. Windows are `[start, end)` and
cannot overlap. MAE/RMSE are measured in pickups per zone-hour. This initial
design supports one evaluation summary per run; multiple folds or evaluation
splits would require a schema extension. The constraints validate metadata, not
whether training code actually prevents leakage.

Insert a model's evaluation row before its `model_forecasts` rows. Use a new
`model_run_id` for each fitted/evaluated run. Predictions may be fractional but
must be finite and nonnegative. `forecast_hour` is the **target hour**. The ML
module must enforce next-hour alignment and use only available historical
features. `generated_at` records when the row was written, including retrospective
backtests. No demand-row foreign key is required because future actuals may not
exist. Consumers should select a specific model run to avoid mixing versions.

## Time and missing-data assumptions

- Preserve the upstream NYC local, timezone-naive timestamps; do not silently
  reinterpret them as UTC. Audit timestamps use `TIMESTAMPTZ`.
- Current input contains only observed zone-hour combinations. An absent row is
  not automatically zero. Store an explicit zero only when upstream has verified
  that hour's coverage. Any later zero-filling must be an explicit team decision.
- Local naive timestamps cannot distinguish repeated hours when daylight saving
  time ends. Extending into a DST transition needs an agreed timestamp policy;
  simply attaching a timezone cannot reconstruct missing offset information.
- The queries report observation coverage. Weekday/weekend averages use daily
  totals, but unequal hour/zone coverage can still make comparisons misleading.
- Lookup entries such as unknown zones remain valid if supplied upstream. This
  schema does not restrict IDs to a hardcoded list of current TLC zones.
- `CREATE TABLE IF NOT EXISTS` supports repeated initialization, not schema
  migration. It will not update a table created with an older definition.

## Verification

Verified on November 22, 2026 using PostgreSQL 16.16 (ARM64) in a temporary
`postgres:16-alpine` container with networking disabled:

- Schema initialization ran twice successfully.
- Synthetic fixtures loaded twice without increasing row counts.
- All 14 SQL assertions and 21 expected constraint-rejection cases passed.
- All four analytical queries matched the hand-calculated results below.
- Test rollback restored the original counts: 8 demand rows, 140 pickups,
  1 model run and 2 forecasts.
- A separate non-fixture test database rejected the seed script and remained
  unchanged.

The temporary container was removed after verification. These checks used only
the labeled synthetic fixtures; the full January Parquet was not loaded into
PostgreSQL, and no model was trained as part of this contribution.

Synthetic hand-check totals: 3 zones, 8 demand rows, 140 pickups, 1 model run and
2 forecasts. Zone A contributes 100 pickups and Zone B 40. The 08:00 buckets total
60 and 09:00 buckets total 80. Friday has 35 pickups and Saturday 105. Zone C has
no observations and is not silently filled. Forecast and metric values are test
fixtures, not measured model performance.

## References and contribution

- Existing [data pipeline and contract](../../data/README.md).
- PostgreSQL [constraints](https://www.postgresql.org/docs/16/ddl-constraints.html),
  [timestamps](https://www.postgresql.org/docs/16/datatype-datetime.html), and
  [INSERT / ON CONFLICT](https://www.postgresql.org/docs/16/sql-insert.html).

This database foundation was implemented with AI assistance. Validation results
describe executed checks; they do not imply completion of the team's end-to-end
pipeline or model training.
