-- Read-only examples over all loaded observations. For a reporting window, add
-- WHERE d.hour >= TIMESTAMP '2025-01-01' AND d.hour < TIMESTAMP '2025-02-01'
-- before GROUP BY. Missing zone-hours are not treated as confirmed zeros.

-- 1. Highest-demand pickup zones.
SELECT z.location_id, z.borough, z.zone,
       SUM(d.pickup_count) AS total_pickups,
       COUNT(*) AS observed_zone_hours
FROM public.hourly_demand AS d
JOIN public.taxi_zones AS z ON z.location_id = d.location_id
GROUP BY z.location_id, z.borough, z.zone
ORDER BY total_pickups DESC, z.location_id
LIMIT 10;

-- 2. Hour-of-day patterns across the observed dates and zones.
SELECT EXTRACT(HOUR FROM d.hour)::INTEGER AS hour_of_day,
       SUM(d.pickup_count) AS total_pickups,
       COUNT(*) AS observed_zone_hours
FROM public.hourly_demand AS d
GROUP BY hour_of_day
ORDER BY hour_of_day;

-- 3. Demand by borough. Unknown lookup categories remain visible.
SELECT z.borough,
       SUM(d.pickup_count) AS total_pickups,
       COUNT(DISTINCT d.location_id) AS observed_zones,
       COUNT(*) AS observed_zone_hours
FROM public.hourly_demand AS d
JOIN public.taxi_zones AS z ON z.location_id = d.location_id
GROUP BY z.borough
ORDER BY total_pickups DESC, z.borough;

-- 4. Weekday versus weekend: first total each observed date, then average dates.
-- This avoids confusing five weekdays with two weekend days. It does not correct
-- for missing dates or changing zone/hour coverage, so both counts are reported.
WITH daily_demand AS (
    SELECT d.hour::DATE AS pickup_date,
           SUM(d.pickup_count) AS daily_pickups,
           COUNT(*) AS observed_zone_hours
    FROM public.hourly_demand AS d
    GROUP BY pickup_date
)
SELECT CASE WHEN EXTRACT(ISODOW FROM pickup_date) IN (6, 7)
            THEN 'weekend' ELSE 'weekday' END AS day_type,
       COUNT(*) AS observed_days,
       SUM(observed_zone_hours) AS observed_zone_hours,
       SUM(daily_pickups) AS total_pickups,
       ROUND(AVG(daily_pickups), 2) AS avg_pickups_per_observed_day
FROM daily_demand
GROUP BY day_type
ORDER BY day_type;
