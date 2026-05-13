DROP TABLE IF EXISTS processed.dim_region;

CREATE TABLE processed.dim_region AS
WITH rural AS (
    SELECT DISTINCT ON (postcode)
        postcode,
        area_km2,
        mmm_area,
        CASE
            WHEN mmm_class IN ('1','2') THEN 'Urban'
            ELSE 'Rural'
        END AS region_type
    FROM raw.rural_class
    ORDER BY postcode, mmm_area DESC
),
postcode_lga AS (
    SELECT DISTINCT
        d.postcode,
        d.state,
        c.lga,
        r.area_km2,
        r.mmm_area,
        r.region_type
    FROM raw.raw_der d
    LEFT JOIN staging.poa2lga_dominant c ON d.postcode = c.postcode
    LEFT JOIN rural r                     ON d.postcode = r.postcode
)
SELECT
    p.postcode,
    p.state,
    p.lga,
    a.region,
    p.area_km2      AS postcode_area,
    p.mmm_area      AS region_type_area,
    p.region_type
FROM postcode_lga p
LEFT JOIN (
    SELECT DISTINCT lga, region FROM raw.raw_abs
) a ON p.lga = a.lga;