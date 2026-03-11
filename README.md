
Distributed Energy Resources (DER) Dashboard and Analysis

----------

Overview: This project analyses Distributed Energy Resource (DER) adoption across Local Government Areas (LGAs) in Australia, focusing on capacity trends, socioeconomic characteristics, and adoption patterns.
The analysis is conducted separately for business and residential DER connections.

The objective is to:
    - Identify the key drivers of DER adoption
    - Produce consistent and comparable adoption metrics
    - Cluster LGAs into adoption profiles
    - Deliver a Power BI dashboard that provides intuitive, data-driven insights for decision-makers

Key Insights: 
    1. LGAs can be segmented into distinct adoption profiles based on DER capacity and connection characteristics, enabling clearer identification of high-growth and emerging regions.
    2. DER adoption intensity (capacity per capita and per business) tends to be higher in suburban and regional areas, with comparatively lower penetration in dense metropolitan LGAs, indicating differing economic and infrastructure drivers.
    3. The Power BI analytics dashboard provides an integrated view of DER adoption and socioeconomic indicators, enabling targeted sales strategies, market prioritization, and evidence-based policy planning.

Detailed Objectives:
    1. Aggregate and clean DER and socioeconomic data at the LGA level. 
    2. Load cleaned data into SQL database for reproducible and future analysis. 
    2. Compute derived metrics such as:
        - Total DER capacity
        - Capacity per capita / no. of businesses
        - Capacity per connection
        - Growth rate over time (based on simple linear regression)
    3. Cluster LGAs based on DER adoption patterns.
    4. Produce an interactive dashboard summarising key metrics socioeconomic data and cluster insights.

Usage:
    1. Save raw DER Registry (DERR) data from AEMO in data/aemo and raw ABS data in data/abs. 
    2. Run ETL script in code/ETL.py to clean and load data into SQLite database in data/sql_db/energy.db.
    3. Run SQL_Query.py to create star schema tables in database.
    4. Run or view EDA in analysis/EDA.ipynb (required to clean data for analysis). 
    5. Run analysis in analysis/Analysis.ipynb (required for appending cluster results for dashboard).
    6. Update Power BI dashboard in dashboard/EnergyDashboard.pbix. 

----------

Data Sources:
    - ABS (Australian Bureau of Statistics): Population, median age, income, education levels, business sectors and business size
    - DER Registry (AEMO): Installed capacity, DER connections, and breakdown by DER type (solar, battery, other)
    - Geographical mapping: Postcode to LGA mapping based on 2021 map. 


Data Processing:
    Preprocessing for importing DERR data into SQLite database
     - Merge multiple DERR files, each corresponding to a year, into a singe file. 
     - Standardised column names.
     - Attached LGA to postcode based on 2021 Postcode map. 
     - Passed year and month from file name into a date column. 
     - Selected relevant DERR columns. 
    Preprocessing for importing ABS data into SQLite database
     - Select relevant columns from raw ABS population and economic data.
     - Standardise column names.
     - Combine into a single dataframe. 


    Creating Star schema in SQLite database
     - Q_abs_data_items: Create dimension table of ABS measure codes and measure items (population, no. of business in sectors, etc)
     - Q_Region: Create dimension table of postcode and LGA correspondence.
     - Q_Main_Derr: Create fact table for DERR data by aggregating AEMO DER data by LGA and year then joining LGA via postcode.
     - Q_Population_Agg: Create population data table in long form. 
     - Q_Business_Agg: Create economic data table in long form. 

    ETL for analysis and Power BI dashboard
        DER Fact Table: 
            - Dropped 'None' and 'Blank' entries in 'Type' column in DERR data. 
            - Remove misaligned LGAs and recorded their codes in SQL table.
            - Filter out 2025 since year is incomplete. 
        Population and Economic Fact Tables: 
            - Forwardfill followed by backfill population data. With the exception of the first year, each year corresponds to data from the last reported census. 
            - Processed mismatches in total number of businesses and sum of business sectors. If discrepancy is less than 5% of total business number, fill NAs with 0. For the remaining rows, drop LGA. 



EDA:
    We first split the data into two tables. Residential data (DER with type 'RESIDENTIAl' and BAS population data) and Business data (DER with type "BUSINESS' and ABS economic data).
    
    Residential data: 
        The following features are positively skewed. We normalise these columns using log base 10 scaling. 
            - TotalCapacity
            - BatteryCapacity
            - SolarCapacity
            - OtherCapacity
            - TotalDerConnections
            - BatteryConnections
            - SolarConnections
            - OtherConnections
            - TotalPopulation
            - PopulationDensity
       
        There is very high correlation between total capacity, battery capacity, total connections and solar connections (>0.9). In fact, solar capacity dominates total capacity.
        There is high correlation of total capacity with LGA population. We see the not too surprising effect of the size of LGA driving total DER capacity.
        
        We therefore normalise and use capacity per capita as a metric. Moreover, we calculate a second metric, growth rate, as the slope obtained by a simple linear regression over the four years (2021-2024).

        Capacity per capita has moderate negative correlation with Total population, population density, university degrees and medium incomes. This seems to reflect metropolitan vs suburban LGAs.
        Capacity per capita has a moderate positive correlation with growth, which is expected from its derivation.


        Business data: 
            All features positively skewed. We normalise using a log transformation. 
            Very high correlation between total capacity and solar capacity (>0.9). 
            Moderate to weak correlation with number of businesses across sie and industry type, with the exception of Primary industry. 

            We again remove the size effect of the LGA by analysing capacity per business.

            We observe a similar correlation profile. Capacity per business is strongly negatively correlated with total number of businesses and number of businesses in the quaternary industry. 
            Once again, this highlights a metropolitan vs suburban divide. 



    Analysis:
        The main goal of our analysis is to use KMeans clustering for market segmentation. 
        Using four clusters for both residential and business DERR data. The factors used are 
            - 'TotalCapacity',
            - 'TotalDerConnections',
            - 'CapacityPerCapita',
            - 'CapacityPerConnection' and
            - 'GrowthRate'.
        
        A median is taken over 2021-2024 (with the exception of growth rate) of the above factors followed by a standard normalisation. 
        The clusters are projected onto three principle components which allows us to interpret the data.
        Unfortunately, no significant clusters are visible when projecting onto socioeconomic or business data. 
        Any predictive power from socioeconomic and economic data reacquires further analysis.

        Business Clusters 

        Cluster 0: Saturated. Low growth. High total capacity and connections. High capacity per capita.  
        Cluster 1: Steady Adoption. Low growth. Medium total capacity and connections. Medium capacity per capita.  
        Cluster 2: Reluctant Adoption. Low growth. Low total capacity and connections. Low capacity per capita.  
        Cluster 3: New Adoption. High growth, low total capacity and connections. 

        Residential Clusters 

        Cluster 0: Reluctant Adoption. Low capacity per capita and low growth rate. 
        Cluster 1: Low Quality Steady Adoption. Low capacity per connection, moderate capacity per capita and growth rate. 
        Cluster 2: High Quality Stead Adoption. High capacity per connection, moderate capacity per capita and growth rate. 
        Cluster 3: Enthusiastic Adoption. High capacity per capita (>100 kVA/capita) and high growth rate. 
        

