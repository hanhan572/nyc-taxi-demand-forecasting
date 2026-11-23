-- PostgreSQL 16+. Run against the project's database, not the Airflow metadata DB.
-- Safe to rerun for initialization; IF NOT EXISTS does not migrate old definitions.
BEGIN;

CREATE TABLE IF NOT EXISTS public.taxi_zones (
    location_id INTEGER PRIMARY KEY CHECK (location_id > 0),
    borough TEXT NOT NULL CHECK (btrim(borough) <> ''),
    zone TEXT NOT NULL CHECK (btrim(zone) <> ''),
    service_zone TEXT
);

CREATE TABLE IF NOT EXISTS public.hourly_demand (
    location_id INTEGER NOT NULL REFERENCES public.taxi_zones (location_id),
    hour TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    pickup_count BIGINT NOT NULL CHECK (pickup_count >= 0),
    PRIMARY KEY (location_id, hour),
    CONSTRAINT demand_whole_hour CHECK (
        isfinite(hour) AND hour = date_trunc('hour', hour)
    )
);

-- One evaluation summary per uniquely named model run, not one row per prediction.
-- All time windows are half-open: [start, end).
CREATE TABLE IF NOT EXISTS public.model_metrics (
    model_run_id TEXT PRIMARY KEY CHECK (btrim(model_run_id) <> ''),
    model_name TEXT NOT NULL CHECK (btrim(model_name) <> ''),
    train_start TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    train_end TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    evaluation_start TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    evaluation_end TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    n_evaluated BIGINT NOT NULL CHECK (n_evaluated > 0),
    mae DOUBLE PRECISION NOT NULL CHECK (mae >= 0 AND mae < 'Infinity'::DOUBLE PRECISION),
    rmse DOUBLE PRECISION NOT NULL CHECK (rmse >= 0 AND rmse < 'Infinity'::DOUBLE PRECISION),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_evaluation_windows CHECK (
        isfinite(train_start) AND isfinite(train_end)
        AND isfinite(evaluation_start) AND isfinite(evaluation_end)
        AND train_start < train_end
        AND train_end <= evaluation_start
        AND evaluation_start < evaluation_end
    )
);

CREATE TABLE IF NOT EXISTS public.model_forecasts (
    model_run_id TEXT NOT NULL REFERENCES public.model_metrics (model_run_id),
    location_id INTEGER NOT NULL REFERENCES public.taxi_zones (location_id),
    forecast_hour TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    predicted_pickup_count DOUBLE PRECISION NOT NULL CHECK (
        predicted_pickup_count >= 0
        AND predicted_pickup_count < 'Infinity'::DOUBLE PRECISION
    ),
    generated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (model_run_id, location_id, forecast_hour),
    CONSTRAINT forecast_whole_hour CHECK (
        isfinite(forecast_hour)
        AND forecast_hour = date_trunc('hour', forecast_hour)
    )
);

-- Existing primary-key indexes already support zone-first demand queries and
-- run-first forecast queries. These indexes support time-first filters instead.
CREATE INDEX IF NOT EXISTS hourly_demand_hour_idx
    ON public.hourly_demand (hour);
CREATE INDEX IF NOT EXISTS model_forecasts_hour_location_idx
    ON public.model_forecasts (forecast_hour, location_id);

COMMENT ON COLUMN public.hourly_demand.hour IS
    'Start of NYC local pickup-hour bucket; timezone-naive, matching upstream Parquet.';
COMMENT ON COLUMN public.hourly_demand.pickup_count IS
    'Observed valid pickups. An absent row means missing/unrepresented, not automatically zero.';
COMMENT ON TABLE public.model_metrics IS
    'One model run and one chronological evaluation window per row. Metrics are in pickups per zone-hour.';
COMMENT ON COLUMN public.model_forecasts.forecast_hour IS
    'Target pickup-hour bucket, not prediction creation time. Upstream ML is responsible for next-hour alignment and leakage prevention.';

COMMIT;
