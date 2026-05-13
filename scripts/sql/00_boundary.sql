--- Reproject to CRS: 7844

DROP TABLE IF EXISTS staging.poa_proj;

CREATE TABLE staging.poa_proj AS
SELECT 
	poa_code21, 
	ST_Transform(geometry, 7844) AS geometry 
FROM raw.poa_boundary;

CREATE INDEX ON staging.poa_proj USING GIST(geometry);

DROP TABLE IF EXISTS staging.lga_proj;

CREATE TABLE staging.lga_proj AS
SELECT 
	lga_code21, 
	ST_Transform(geometry, 7844) AS geometry 
FROM raw.lga_boundary;

CREATE INDEX ON staging.lga_proj USING GIST(geometry);

--- Create LGA to POA correspondence

DROP TABLE IF EXISTS staging.poa2lga_correspondence;

CREATE TABLE staging.poa2lga_correspondence AS
WITH intersections AS (
    SELECT
        p.poa_code21 AS postcode,
        l.lga_code21 AS lga,
        ST_Intersection(p.geometry, l.geometry) AS geom_intersection,
        ST_Area(p.geometry) AS poa_area
    FROM staging.poa_proj p
    JOIN staging.lga_proj l ON ST_Intersects(p.geometry, l.geometry)
)
SELECT
    postcode,
    lga,
    ST_Area(geom_intersection) / poa_area AS ratio
FROM intersections
WHERE ST_Area(geom_intersection) > 0;


--- Filter out largest LGA in each postcode
DROP TABLE IF EXISTS staging.poa2lga_dominant;

CREATE TABLE staging.poa2lga_dominant AS
SELECT DISTINCT ON (postcode)
    postcode,
    lga,
    ratio
FROM staging.poa2lga_correspondence
ORDER BY postcode, ratio DESC;