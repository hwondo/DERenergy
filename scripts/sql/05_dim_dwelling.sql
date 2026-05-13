DROP TABLE IF EXISTS processed.dim_dwelling;

CREATE TABLE processed.dim_dwelling AS
SELECT
    lga_2021::text  AS lga,
    time_period     AS year,
    obs_value       AS total_dwellings
FROM raw.raw_dwelling
WHERE type = '_T';
