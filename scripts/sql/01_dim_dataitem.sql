DROP TABLE IF EXISTS processed.dim_dataitem;

CREATE TABLE processed.dim_dataitem AS
SELECT DISTINCT
    data_item,
    measure
FROM raw.raw_abs
ORDER BY data_item;
