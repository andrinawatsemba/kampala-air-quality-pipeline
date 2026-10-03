-- Views only use real readings (is_forecast = false), never model predictions.
-- WHO 24-hour guideline for PM2.5 is 15 ug/m3.

-- 1) One row per day
CREATE OR REPLACE VIEW daily_air_quality AS
SELECT
    time::date                                  AS day,
    ROUND(AVG(pm2_5)::numeric, 1)               AS avg_pm2_5,
    ROUND(MAX(pm2_5)::numeric, 1)               AS max_pm2_5,
    ROUND(AVG(pm10)::numeric, 1)                AS avg_pm10,
    ROUND(AVG(temperature_2m)::numeric, 1)      AS avg_temp_c,
    ROUND(SUM(precipitation)::numeric, 1)       AS total_rain_mm,
    COUNT(*)                                    AS hours_recorded,
    COUNT(*) = 24                               AS is_complete_day,
    AVG(pm2_5) > 15                             AS above_who_guideline
FROM air_quality_hourly
WHERE is_forecast = false
GROUP BY time::date;

-- 2) One row per week (weeks start on Monday)
CREATE OR REPLACE VIEW weekly_air_quality AS
SELECT
    date_trunc('week', time)::date              AS week_start,
    ROUND(AVG(pm2_5)::numeric, 1)               AS avg_pm2_5,
    ROUND(AVG(pm10)::numeric, 1)                AS avg_pm10,
    ROUND(AVG(temperature_2m)::numeric, 1)      AS avg_temp_c,
    ROUND(SUM(precipitation)::numeric, 1)       AS total_rain_mm,
    COUNT(*)                                    AS hours_recorded
FROM air_quality_hourly
WHERE is_forecast = false
GROUP BY date_trunc('week', time);

-- 3) The 10 worst full days. Partial days are skipped so they can't skew the ranking.
CREATE OR REPLACE VIEW worst_air_days AS
SELECT day, avg_pm2_5, max_pm2_5, total_rain_mm
FROM daily_air_quality
WHERE is_complete_day
ORDER BY avg_pm2_5 DESC
LIMIT 10;