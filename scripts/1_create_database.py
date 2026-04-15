
######### SQL Queries #########

# -- Drop Existing Tables --- #

Q_Drop_Tables = """
    DROP TABLE IF EXISTS Dim_DataItem;
    DROP TABLE IF EXISTS Dim_Region;
    DROP TABLE IF EXISTS Dim_Population;
    DROP TABLE IF EXISTS Dim_Dwelling;
    DROP TABLE IF EXISTS Dim_Economic;
    DROP TABLE IF EXISTS Fact_Derr;
"""

# --- Dimension Tables --- #

# ABS Data Items
Q_abs_data_items = """
    CREATE TABLE Dim_DataItem AS
    SELECT DISTINCT DataItem,
            Measure
    FROM Raw_ABS
    ORDER BY DataItem
"""

# Subquery for rural classification
Qsub_rural = """
    SELECT 
        r.Postcode,
        r."Area(km2)",
        r.MMM_Area,
        r.MMM_Class
    FROM rural_class r
    INNER JOIN (
        SELECT 
            Postcode, 
            MAX(MMM_Area) AS Max_MMM_Area
        FROM rural_class
        GROUP BY Postcode
    ) m
        ON r.Postcode = m.Postcode 
        AND r.MMM_Area = m.Max_MMM_Area
"""

# Subquery for rural classification
Qsub_class =f"""
    SELECT
        s.Postcode,
        s."Area(km2)",
        s.MMM_Area,
        CASE 
            WHEN s.MMM_Class IN ('1','2') THEN 'Urban' 
            ELSE 'Rural' 
        END AS Region_Type
    FROM ({Qsub_rural}) s
"""

# Subquery to join with Postcode Lga data
Qsub_lga2PostcodeReg = f"""
    SELECT * FROM Lga2Postcode l
    LEFT JOIN ({Qsub_class}) s
        ON l.Postcode = s.Postcode
"""


# Region Postcode, LGA and Rural Classification
Q_Region = f""" 
    CREATE TABLE Dim_Region AS 
    WITH Postcode_LGA AS (
        SELECT DISTINCT 
            d.Postcode, 
            d.State,
            l.Lga,
            l."Area(km2)",
            l.MMM_Area,
            l.Region_Type
        FROM Raw_Derr d
        LEFT JOIN ({Qsub_lga2PostcodeReg}) l 
            ON l.Postcode = d.Postcode
    )
    SELECT         
        l.Postcode,              
        l.State,
        l.Lga, 
        abs.Region,
        l."Area(km2)" AS Postcode_Area,
        l.MMM_Area AS Region_Type_Area,
        l.Region_Type 
    FROM Postcode_LGA l
    LEFT JOIN (
        SELECT DISTINCT Lga, Region 
        FROM Raw_ABS 
    ) abs
    ON l.Lga = abs.Lga
"""


# Create Economic Table 

Q_Business_Agg = f"""
    CREATE TABLE Dim_Economic AS
    SELECT 
        abs.Lga,
        abs.TimePeriod AS Year,
        MAX(CASE WHEN abs.Measure = 'CABEE_5' 
            THEN abs.ObsValue ELSE 0 END) AS TotalBusinesses,
        --- Business Sector Indicators ---
        SUM(CASE WHEN abs.Measure IN ('CABEE_19','CABEE_28') 
            THEN abs.ObsValue ELSE 0 END) AS PrimaryIndustry,
        SUM(CASE WHEN abs.Measure IN ('CABEE_21','CABEE_23','CABEE_27')
            THEN abs.ObsValue ELSE 0 END) AS SecondaryIndustry,
        SUM(CASE WHEN abs.Measure IN ('CABEE_17','CABEE_18','CABEE_20','CABEE_22','CABEE_24','CABEE_25','CABEE_26','CABEE_30','CABEE_32','CABEE_33','CABEE_34','CABEE_36','CABEE_37')
            THEN abs.ObsValue ELSE 0 END) AS TertiaryIndustry,
        SUM(CASE WHEN abs.Measure IN ('CABEE_31')
            THEN abs.ObsValue ELSE 0 END) AS QuaternaryIndustry,      
        --- Business Size Indicators ---
        SUM (CASE WHEN abs.Measure IN ('CABEE_42','CABEE_43')
            THEN abs.ObsValue ELSE 0 END) AS SmallBusinesses,
        SUM (CASE WHEN Measure IN ('CABEE_44','CABEE_45')
            THEN abs.ObsValue ELSE 0 END) AS MediumBusinesses,
        SUM (CASE WHEN abs.Measure IN ('CABEE_46','CABEE_47')
            THEN abs.ObsValue ELSE 0 END) AS LargeBusinesses
    FROM Raw_ABS abs
    GROUP BY 
        abs.Lga, abs.TimePeriod
    ORDER BY 
        abs.Lga, abs.TimePeriod;
"""



# Create Population Table --- #

Q_Population_Agg = f"""
    CREATE TABLE Dim_Population AS 
    SELECT 
        abs.Lga,
        abs.TimePeriod AS Year,
        MAX(CASE WHEN abs.Measure = 'ERP_P_20' 
            THEN abs.ObsValue END) AS TotalPopulation,
        MAX(CASE WHEN abs.Measure = 'ERP_21' 
            THEN abs.ObsValue END) AS PopulationDensity,
        MAX(CASE WHEN abs.Measure = 'ERP_23' 
            THEN abs.ObsValue END) AS MedianAge,
        MAX(CASE WHEN abs.Measure = 'EQUIV_2'
            THEN abs.ObsValue END) AS MedianEquivalisedHouseholdIncome,
        MAX(CASE WHEN abs.Measure = 'SCHOOL_7'
            THEN abs.ObsValue END) AS Certificate,
        MAX(CASE WHEN abs.Measure = 'SCHOOL_6'
            THEN abs.ObsValue END) AS AdvDiploma,
        MAX(CASE WHEN abs.Measure = 'SCHOOL_5'
            THEN abs.ObsValue END) AS BachelorDegree,
        MAX(CASE WHEN abs.Measure = 'SCHOOL_4'
            THEN abs.ObsValue END) AS GraduateDiploma,
        MAX(CASE WHEN abs.Measure = 'SCHOOL_3'
            THEN abs.ObsValue END) AS Postgraduate
    FROM Raw_ABS abs 
    GROUP BY 
        abs.Lga, abs.TimePeriod
    ORDER BY 
        abs.Lga, abs.TimePeriod;
"""

# Create Dwellings Table

Q_Dwelling = f"""
    CREATE TABLE Dim_Dwelling AS 
    SELECT
        LGA_2021 AS Lga,
        TIME_PERIOD AS Year,
        OBS_VALUE AS TotalDwelling
    FROM Raw_Dwelling
    WHERE Type = '_T'
    """

# --- Create Derr Fact Table --- #

# Aggregate by Derr by LGA
Q_Main_Derr = f""" 
    CREATE TABLE Fact_Derr AS 
    SELECT 
        d.Year,
        r.Lga,
        d.NmiBusRes AS Type,
        -- Aggreate by LGA ---
        SUM(d.InstalledDerCapacity) AS TotalCapacity,
        SUM(d.BatteryCapacity) AS BatteryCapacity,
        SUM(d.SolarCapacity) AS SolarCapacity,
        SUM(d.InstalledOtherderCapacity) AS OtherCapacity,
        SUM(d.DerConnections) AS TotalDerConnections,
        SUM(d.BatteryConnections) AS BatteryConnections,
        SUM(d.SolarConnections) AS SolarConnections,
        SUM(d.OtherConnections) AS OtherConnections
    FROM Raw_Derr d
    LEFT JOIN Dim_Region r
        ON d.Postcode = r.Postcode
    GROUP BY 
        r.Lga, d.Year, d.NmiBusRes
    ORDER BY 
        r.Lga, d.Year, d.NmiBusRes
"""


Q_drop_raw = """
    DROP TABLE IF EXISTS Raw_Derr;
    DROP TABLE IF EXISTS Raw_ABS;
    DROP TABLE IF EXISTS Lga2Postcode;
    """

# --- Run SQL Queries --- #

import yaml
import sqlite3 as sql
import pandas as pd

def main(Refresh_Tables: bool = True):
    
    # Connect to database
    with open("config.yaml","r") as file:
        config= yaml.safe_load(file)
    
    DB_PATH = config["paths"]['sql_db']
        
    conn = sql.connect(DB_PATH)
    cursor = conn.cursor()

    # Drop existing tables
    if Refresh_Tables:
        cursor.executescript(Q_Drop_Tables)

    # Create Dimension Tables 
    cursor.execute(Q_abs_data_items)
    cursor.execute(Q_Region)

    # Create Fact Tables
    cursor.execute(Q_Main_Derr) 
    cursor.execute(Q_Population_Agg) 
    cursor.execute(Q_Dwelling)
    cursor.execute(Q_Business_Agg)

    # Save for evaluation
    # Derr_df = pd.read_sql("SELECT * FROM Fact_Derr", conn)
    # Pop_df = pd.read_sql("SELECT * FROM Fact_Population", conn)
    # Econ_df = pd.read_sql("SELECT * FROM Fact_Economic", conn)
    # Region_df = pd.read_sql("SELECT * FROM Dim_Region", conn)

    # Drop raw tables
    cursor.executescript(Q_drop_raw)

    conn.close()
    
    print("Completed SQL Queries")
    


if __name__ == "__main__": 
    main()