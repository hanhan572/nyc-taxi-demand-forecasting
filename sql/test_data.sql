-- SYNTHETIC FIXTURES ONLY. Use a dedicated test database, never the real pipeline DB.
-- IDs 900001-900003 are fictional and deliberately outside the current TLC lookup.
-- Counts, forecasts and metrics are invented test values, not research results.
BEGIN;

-- Refuse to mix these fixtures with any existing non-fixture data.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM public.taxi_zones
               WHERE location_id NOT IN (900001, 900002, 900003))
       OR EXISTS (SELECT 1 FROM public.hourly_demand
                  WHERE location_id NOT IN (900001, 900002, 900003))
       OR EXISTS (SELECT 1 FROM public.model_metrics
                  WHERE model_run_id <> 'demo_baseline_run')
       OR EXISTS (SELECT 1 FROM public.model_forecasts
                  WHERE model_run_id <> 'demo_baseline_run') THEN
        RAISE EXCEPTION 'Use an empty, dedicated test database for synthetic fixtures';
    END IF;
END;
$$;

INSERT INTO public.taxi_zones (location_id, borough, zone, service_zone)
VALUES (900001, 'Manhattan', 'SYNTHETIC Zone A', 'DEMO'),
       (900002, 'Queens', 'SYNTHETIC Zone B', 'DEMO'),
       (900003, 'Brooklyn', 'SYNTHETIC Zone C (no observations)', 'DEMO')
ON CONFLICT (location_id) DO UPDATE
SET borough = EXCLUDED.borough, zone = EXCLUDED.zone,
    service_zone = EXCLUDED.service_zone;

INSERT INTO public.hourly_demand (location_id, hour, pickup_count)
VALUES (900001, '2025-01-03 08:00:00', 10),
       (900002, '2025-01-03 08:00:00', 5),
       (900001, '2025-01-03 09:00:00', 20),
       (900002, '2025-01-03 09:00:00', 0),
       (900001, '2025-01-04 08:00:00', 30),
       (900002, '2025-01-04 08:00:00', 15),
       (900001, '2025-01-04 09:00:00', 40),
       (900002, '2025-01-04 09:00:00', 20)
ON CONFLICT (location_id, hour) DO UPDATE
SET pickup_count = EXCLUDED.pickup_count;

INSERT INTO public.model_metrics (
    model_run_id, model_name, train_start, train_end,
    evaluation_start, evaluation_end, n_evaluated, mae, rmse
)
VALUES ('demo_baseline_run', 'SYNTHETIC baseline (not trained)',
        '2025-01-01', '2025-01-03', '2025-01-03', '2025-01-05', 8, 2.0, 2.5)
ON CONFLICT (model_run_id) DO UPDATE
SET model_name = EXCLUDED.model_name,
    train_start = EXCLUDED.train_start, train_end = EXCLUDED.train_end,
    evaluation_start = EXCLUDED.evaluation_start,
    evaluation_end = EXCLUDED.evaluation_end,
    n_evaluated = EXCLUDED.n_evaluated, mae = EXCLUDED.mae, rmse = EXCLUDED.rmse;

-- These future target hours have no actuals yet: forecasts must still be storable.
INSERT INTO public.model_forecasts (
    model_run_id, location_id, forecast_hour, predicted_pickup_count
)
VALUES ('demo_baseline_run', 900001, '2025-01-05 10:00:00', 12.5),
       ('demo_baseline_run', 900002, '2025-01-05 10:00:00', 8.0)
ON CONFLICT (model_run_id, location_id, forecast_hour) DO UPDATE
SET predicted_pickup_count = EXCLUDED.predicted_pickup_count;

COMMIT;
