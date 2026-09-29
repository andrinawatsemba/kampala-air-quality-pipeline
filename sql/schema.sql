-- One row per hour in Kampala. "time" is the primary key, so an hour can only exist once.
CREATE TABLE IF NOT EXISTS air_quality_hourly (
    time                  TIMESTAMP PRIMARY KEY,
    pm2_5                 DOUBLE PRECISION,
    pm10                  DOUBLE PRECISION,
    nitrogen_dioxide      DOUBLE PRECISION,
    ozone                 DOUBLE PRECISION,
    temperature_2m        DOUBLE PRECISION,
    relative_humidity_2m  INTEGER,
    precipitation         DOUBLE PRECISION,
    is_forecast           BOOLEAN NOT NULL,
    loaded_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);