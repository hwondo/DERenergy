DROP TABLE IF EXISTS processed.fact_derr;

CREATE TABLE processed.fact_derr AS
WITH aemo AS (
    SELECT
        postcode,
        year,
        nmi_bus_res,
        SUM(installed_der_capacity)       AS total_capacity,
        SUM(battery_capacity)            AS battery_capacity,
        SUM(solar_capacity)              AS solar_capacity,
        SUM(installed_otherder_capacity)  AS other_capacity,
        SUM(der_connections)             AS total_connections,
        SUM(battery_connections)         AS battery_connections,
        SUM(solar_connections)           AS solar_connections,
        SUM(other_connections)           AS other_connections
    FROM raw.raw_der
    GROUP BY postcode, year, nmi_bus_res
)
SELECT
    c.lga,
    a.year,
    a.nmi_bus_res                                     AS type,
    SUM(a.total_capacity        * c.ratio)          AS total_capacity,
    SUM(a.battery_capacity      * c.ratio)          AS battery_capacity,
    SUM(a.solar_capacity        * c.ratio)          AS solar_capacity,
    SUM(a.other_capacity        * c.ratio)          AS other_capacity,
    SUM(a.total_connections     * c.ratio)          AS total_connections,
    SUM(a.battery_connections   * c.ratio)          AS battery_connections,
    SUM(a.solar_connections     * c.ratio)          AS solar_connections,
    SUM(a.other_connections     * c.ratio)          AS other_connections
FROM aemo a
JOIN staging.poa2lga_correspondence c ON a.postcode = c.postcode
GROUP BY c.lga, a.year, a.nmi_bus_res;