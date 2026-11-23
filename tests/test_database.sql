-- Run after schema.sql and test_data.sql in a dedicated test database.
-- Every mutation below is rolled back. A failed assertion stops psql with -v ON_ERROR_STOP=1.
BEGIN;
SET LOCAL plpgsql.check_asserts = on;

CREATE FUNCTION pg_temp.expect_error(statement TEXT, expected_state TEXT)
RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE actual_state TEXT;
BEGIN
    BEGIN
        EXECUTE statement;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS actual_state = RETURNED_SQLSTATE;
    END;
    IF actual_state IS DISTINCT FROM expected_state THEN
        RAISE EXCEPTION 'Expected SQLSTATE %, got % for %',
            expected_state, COALESCE(actual_state, 'success'), statement;
    END IF;
END;
$$;

-- Four expected outputs, calculated by hand from the eight synthetic rows.
DO $$
BEGIN
    ASSERT (SELECT COUNT(*) = 3 FROM public.taxi_zones), 'Expected 3 zones';
    ASSERT (SELECT COUNT(*) = 8 AND SUM(pickup_count) = 140
            FROM public.hourly_demand), 'Expected 8 observations / 140 pickups';
    ASSERT (SELECT SUM(pickup_count) = 100 FROM public.hourly_demand
            WHERE location_id = 900001), 'Zone A should have 100 pickups';
    ASSERT (SELECT SUM(pickup_count) = 60 FROM public.hourly_demand
            WHERE EXTRACT(HOUR FROM hour) = 8), '08:00 buckets should total 60';
    ASSERT (SELECT SUM(d.pickup_count) = 40 FROM public.hourly_demand d
            JOIN public.taxi_zones z USING (location_id)
            WHERE z.borough = 'Queens'), 'Queens should total 40';
    ASSERT (SELECT SUM(pickup_count) = 35 FROM public.hourly_demand
            WHERE EXTRACT(ISODOW FROM hour) < 6), 'Weekday should total 35';
    ASSERT (SELECT SUM(pickup_count) = 105 FROM public.hourly_demand
            WHERE EXTRACT(ISODOW FROM hour) >= 6), 'Weekend should total 105';
    ASSERT (SELECT COUNT(*) = 1 FROM public.hourly_demand WHERE pickup_count = 0),
        'A confirmed zero must remain stored';
    ASSERT NOT EXISTS (SELECT 1 FROM public.hourly_demand WHERE location_id = 900003),
        'An unobserved zone must not be silently zero-filled';
    ASSERT (SELECT COUNT(*) = 1 FROM public.model_metrics), 'Expected one demo run';
    ASSERT (SELECT COUNT(*) = 2 FROM public.model_forecasts f
            LEFT JOIN public.hourly_demand d
              ON d.location_id = f.location_id AND d.hour = f.forecast_hour
            WHERE d.location_id IS NULL), 'Future forecasts must not require actuals';
END;
$$;

-- Unique, foreign-key, not-null, and domain constraints.
SELECT pg_temp.expect_error(
    $$INSERT INTO public.hourly_demand VALUES (900001, '2025-01-03 08:00', 99)$$, '23505');
SELECT pg_temp.expect_error(
    $$INSERT INTO public.hourly_demand VALUES (999999, '2025-01-06 08:00', 1)$$, '23503');
SELECT pg_temp.expect_error(
    $$INSERT INTO public.hourly_demand VALUES (900001, '2025-01-06 08:00', -1)$$, '23514');
SELECT pg_temp.expect_error(
    $$INSERT INTO public.hourly_demand VALUES (900001, '2025-01-06 08:30', 1)$$, '23514');
SELECT pg_temp.expect_error(
    $$INSERT INTO public.hourly_demand VALUES (900001, 'infinity', 1)$$, '23514');
SELECT pg_temp.expect_error(
    $$INSERT INTO public.hourly_demand VALUES (900001, '2025-01-06 08:00', NULL)$$, '23502');
SELECT pg_temp.expect_error(
    $$INSERT INTO public.taxi_zones VALUES (-1, 'Queens', 'Bad zone', NULL)$$, '23514');
SELECT pg_temp.expect_error(
    $$INSERT INTO public.taxi_zones VALUES (900004, '', 'Bad borough', NULL)$$, '23514');
SELECT pg_temp.expect_error(
    $$UPDATE public.model_metrics SET train_end = '2025-01-04'$$, '23514');
SELECT pg_temp.expect_error(
    $$UPDATE public.model_metrics SET evaluation_end = evaluation_start$$, '23514');
SELECT pg_temp.expect_error(
    $$UPDATE public.model_metrics SET n_evaluated = 0$$, '23514');
SELECT pg_temp.expect_error(
    $$UPDATE public.model_metrics SET mae = 'NaN'$$, '23514');
SELECT pg_temp.expect_error(
    $$UPDATE public.model_metrics SET rmse = 'Infinity'$$, '23514');
SELECT pg_temp.expect_error(
    $$UPDATE public.model_forecasts SET predicted_pickup_count = -1$$, '23514');
SELECT pg_temp.expect_error(
    $$UPDATE public.model_forecasts SET predicted_pickup_count = 'NaN'$$, '23514');
SELECT pg_temp.expect_error(
    $$UPDATE public.model_forecasts SET predicted_pickup_count = 'Infinity'$$, '23514');
SELECT pg_temp.expect_error(
    $$UPDATE public.model_forecasts SET model_run_id = 'missing_run'$$, '23503');
SELECT pg_temp.expect_error(
    $$UPDATE public.model_forecasts SET location_id = 999999 WHERE location_id = 900001$$, '23503');
SELECT pg_temp.expect_error(
    $$UPDATE public.model_forecasts SET forecast_hour = '2025-01-05 10:30'$$, '23514');
SELECT pg_temp.expect_error(
    $$INSERT INTO public.model_forecasts (model_run_id, location_id, forecast_hour, predicted_pickup_count)
      VALUES ('demo_baseline_run', 900001, '2025-01-05 10:00', 10)$$, '23505');
SELECT pg_temp.expect_error(
    $$DELETE FROM public.taxi_zones WHERE location_id = 900001$$, '23503');

-- An idempotent loader replaces a count instead of adding the batch twice.
INSERT INTO public.hourly_demand VALUES (900001, '2025-01-03 08:00', 11)
ON CONFLICT (location_id, hour) DO UPDATE SET pickup_count = EXCLUDED.pickup_count;

-- A second run can forecast the same zone and target hour.
INSERT INTO public.model_metrics (
    model_run_id, model_name, train_start, train_end,
    evaluation_start, evaluation_end, n_evaluated, mae, rmse
)
SELECT 'demo_second_run', model_name, train_start, train_end,
       evaluation_start, evaluation_end, n_evaluated, mae, rmse
FROM public.model_metrics WHERE model_run_id = 'demo_baseline_run';
INSERT INTO public.model_forecasts (model_run_id, location_id, forecast_hour, predicted_pickup_count)
VALUES ('demo_second_run', 900001, '2025-01-05 10:00', 13.0);

-- Upstream UInt32 values must not overflow a signed 32-bit SQL count column.
INSERT INTO public.hourly_demand VALUES (900001, '2025-01-06 08:00', 4294967295);
DO $$
BEGIN
    ASSERT (SELECT pickup_count = 11 FROM public.hourly_demand
            WHERE location_id = 900001 AND hour = '2025-01-03 08:00'), 'Upsert failed';
    ASSERT (SELECT COUNT(*) = 2 FROM public.model_forecasts
            WHERE location_id = 900001 AND forecast_hour = '2025-01-05 10:00'),
        'Model runs must coexist';
    ASSERT (SELECT pickup_count = 4294967295 FROM public.hourly_demand
            WHERE location_id = 900001 AND hour = '2025-01-06 08:00'), 'BIGINT check failed';
END;
$$;

ROLLBACK;
SELECT 'PASS: database fixtures, constraints, upsert and model-run isolation' AS result;
