DROP TABLE IF EXISTS processed.dim_population;

CREATE TABLE processed.dim_population AS
SELECT
    lga::text                                                                   AS lga,
    time_period                                                                 AS year,
    MAX(CASE WHEN measure = 'ERP_P_20' THEN obs_value END)                     AS total_population,
    MAX(CASE WHEN measure = 'ERP_21'   THEN obs_value END)                     AS population_density,
    MAX(CASE WHEN measure = 'ERP_23'   THEN obs_value END)                     AS median_age,
    MAX(CASE WHEN measure = 'EQUIV_2'  THEN obs_value END)                     AS median_household_income,
    MAX(CASE WHEN measure = 'SCHOOL_7' THEN obs_value END)                     AS certificate,
    MAX(CASE WHEN measure = 'SCHOOL_6' THEN obs_value END)                     AS adv_diploma,
    MAX(CASE WHEN measure = 'SCHOOL_5' THEN obs_value END)                     AS bachelor_degree,
    MAX(CASE WHEN measure = 'SCHOOL_4' THEN obs_value END)                     AS graduate_diploma,
    MAX(CASE WHEN measure = 'SCHOOL_3' THEN obs_value END)                     AS postgraduate
FROM raw.raw_abs
GROUP BY lga, time_period
ORDER BY lga, time_period;
