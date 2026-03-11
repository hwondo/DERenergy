
######### SQL Queries #########

# -- Drop Existing Tables --- #
Q_Drop_Tables = """
    DROP TABLE IF EXISTS Dim_DataItem;
    DROP TABLE IF EXISTS Dim_Region;
    DROP TABLE IF EXISTS Fact_Derr;
    DROP TABLE IF EXISTS Fact_Population;
    DROP TABLE IF EXISTS Fact_Economic;
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

# Region (Postcode to LGA)
Q_Region = """ 
    CREATE TABLE Dim_Region AS 
    WITH Postcode_LGA AS (
    SELECT DISTINCT 
        d.Postcode, 
        d.State,
        l.Lga
    FROM Raw_Derr d
    LEFT JOIN Lga2Postcode l 
        ON l.Postcode = d.Postcode
    )
    SELECT * 
    FROM Postcode_LGA l
    LEFT JOIN (
        SELECT DISTINCT Lga, Region 
        FROM Raw_ABS 
    ) abs
    ON l.Lga = abs.Lga
"""

# --- Create Derr Fact Table --- #

# Aggrigate by Derr by LGA
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

# --- Create Population Fact Table --- #

Q_Population_Agg = f"""
    CREATE TABLE Fact_Population AS 
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


# --- Create Economic Fact Table --- #

Q_Business_Agg = f"""
    CREATE TABLE Fact_Economic AS
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
    cursor.execute(Q_Business_Agg)

    # Save for evaluation
    # Derr_df = pd.read_sql("SELECT * FROM Fact_Derr", conn)
    # Pop_df = pd.read_sql("SELECT * FROM Fact_Population", conn)
    # Econ_df = pd.read_sql("SELECT * FROM Fact_Economic", conn)

    # Drop raw tables
    cursor.executescript(Q_drop_raw)

    conn.close()
    
    print("Completed SQL Queries")
    


if __name__ == "__main__": 
    main()