DROP TABLE IF EXISTS processed.dim_economic;

CREATE TABLE processed.dim_economic AS
SELECT
    lga::text                                                                   AS lga,
    time_period                                                                 AS year,
    MAX(CASE WHEN measure = 'CABEE_5'  THEN obs_value END)                     AS total_businesses,
    SUM(CASE WHEN measure IN ('CABEE_19','CABEE_28') THEN obs_value END)       AS primary_industry,
    SUM(CASE WHEN measure IN ('CABEE_21','CABEE_23','CABEE_27') THEN obs_value END)
                                                                                AS secondary_industry,
    SUM(CASE WHEN measure IN (
        'CABEE_17','CABEE_18','CABEE_20','CABEE_22','CABEE_24',
        'CABEE_25','CABEE_26','CABEE_30','CABEE_32','CABEE_33',
        'CABEE_34','CABEE_36','CABEE_37') THEN obs_value END)                  AS tertiary_industry,
    SUM(CASE WHEN measure = 'CABEE_31' THEN obs_value END)                     AS quaternary_industry,
    SUM(CASE WHEN measure IN ('CABEE_42','CABEE_43') THEN obs_value END)       AS small_businesses,
    SUM(CASE WHEN measure IN ('CABEE_44','CABEE_45') THEN obs_value END)       AS medium_businesses,
    SUM(CASE WHEN measure IN ('CABEE_46','CABEE_47') THEN obs_value END)       AS large_businesses
FROM raw.raw_abs
GROUP BY lga, time_period
ORDER BY lga, time_period;
