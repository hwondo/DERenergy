
Distributed Energy Resources (DER) Dashboard and Analysis

----------

Overview: This project analyses Distributed Energy Resource (DER) adoption across Local Government Areas (LGAs) in Australia, focusing on capacity trends, socioeconomic characteristics, and adoption patterns.


The objective is to:
    - Identify key socieconomic drivers of DER adoption. 
    - Cluster LGAs into adoption profiles to support policy making. 
    - Deliver a Power BI dashboard that provides intuitive, data-driven insights for decision-makers. 

Key Insights: 
    1. LGAs are segmented into interpretable groups (see below) based on adoption behaviours. Notably: 
        - Identified LGAs with strong solar adoption but low battery adoption indicating potential pricing barriers for battery storage conversion. 
        - Identified LGAs with saturated solar and battery adoption. Policies targeting energy export rather than solar adoption should be prioritised in these areas. 
    2. No statistical difference of residential capacity between high and low income LGAs. 
    3. Unable to carry out analysis on difference between business capacity between rural and urban LGAs due to fundamental overlap violation (unable to properly control covariances for a substantial sample group of LGAs).

Detailed Objectives:
    1. Aggregate and clean DER and socioeconomic data at the LGA level. 
    2. Load cleaned data into SQL database for reproducible and future analysis. 
    2. Generate metrics that provide a clear summary of DER adoption across Australia.
    3. Cluster LGAs based on metrics to profile adoption behaviour. 
    4. Run statistical inferences over socioeconomic variables to determine key driving factors for DER adoption.
    5. Produce an interactive dashboard summarising key metrics socioeconomic data and cluster insights.

Usage:
    1. Save raw DER Registry (DERR) data from AEMO in data/aemo and raw ABS data in data/abs. 
    2. Run ETL script in code/ETL.py to clean and load data into SQLite database in data/sql_db/energy.db.
    4. Run or view notebooks in order. The notebook 'market_segmentation' notebook is crucial to generate LGA clusters in dashboard. The 'obervation_causal_inference' notebook is used to apply propensity score matching to anlayse causal effect of LGAs on DER adoption patterns.
    6. Update Power BI dashboard in dashboard/EnergyDashboard.pbix. 

----------

Data Sources:
    - ABS (Australian Bureau of Statistics): Population, median age, income, education levels, business sectors and business size
    - DER Registry (AEMO): Installed capacity, DER connections, and breakdown by DER type (solar, battery, other)
    - Geographical mapping: Postcode to LGA mapping based on 2021 map. 
    - Modified Monash Model: Defines whether a location is metropolitan, rural, remote or very remote. 


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
            - Forwardfill followed by backfill population data. With the exception of the first year, each year corresponds to  data from the last reported census. 
            - Processed mismatches in total number of businesses and sum of business sectors. If discrepancy is less than 5% of total business number, fill NAs with 0. For the remaining rows, drop LGA. 

Tables in SQL:
    Dim_DataItem:
        - DataItem: Name of ABS variable
        - Measure: ABS code for variable
    Dim_Region:
        - Postcode
        - State: State postcode is in
        - Lga: LGA code of postcode 
        - Region: Name of postcode
    Fact_Derr:

    Fact_Population:
        - Lga: LGA code
        - Year: Year of data
        - TotalPopulation: 
        - PopulationDensity
        - MedianAge
        - MedianEquivalisedHouseholdIncome
        - Certificate: Percentage of population with certificate
        - AdvDiploma: Percentage of population with advanced diplomas
        - BachelorsDegree: Percentage of population with bachelors degree
        - GraduateDiploma: Percentage of population with graduate diplomas
        - Postgraduate: Percentage of popoulation with postgraduate degrees 
    Fact_Economic:
        - Lga: LGA code
        - Year: Year of data
        - TotalBusinesses: Total number of businesses. 
        - PrimaryIndustry: Total amount of businesses in primary industry sector. 
        - SecondaryIndustry: Total amount of businesses in secondary industry sector.
        - TertiaryIndustry: Total amount of businesses in tertiary industry sector.
        - QuarternaryIndistry: Total amount of businesses in quaternary industry sector.
        - SmallBusinesses: 
        - MediumBusinesses:
        - LargeBusinesses: 

--- 

Exploratory Data Analysis:
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



KPIs:

Using capacity and ABS data, we created several metrics to characterise solar and battery adoption. 

1. Penetration Rate
The share of total dwellings with at least one DER connection. Measures adoption breadth rather than intensity — an LGA with high penetration has broad uptake regardless of system size. The primary equity and access indicator for policy reporting.
2. Battery-to-Solar Ratio (BSR)
The number of battery storage connections expressed as a proportion of solar connections. Measures the rate at which solar adopters are converting to storage. A low BSR in a high-penetration LGA signals a price or policy barrier suppressing storage uptake.
3. Capacity per Connection (CPC)
Total installed capacity divided by the number of DER connections. Measures average system size among adopters — a measure of installation intensity rather than adoption breadth. Particularly informative for business segments where a small number of large commercial installs can dominate aggregate capacity figures.
4. Capacity per Dwelling (CPD)
Total installed capacity divided by total dwellings. Measures the aggregate energy contribution of DER relative to the dwelling base, regardless of how many households have adopted. Combines adoption breadth and system size into a single grid-relevant metric.
5. Growth Rate
The linear trend in installed capacity over time, estimated per LGA using ordinary least squares regression and normalised by baseline capacity. Expressed as a proportional rate per year. Measures adoption velocity rather than current stock — an LGA with low penetration but high growth rate represents a near-term infrastructure priority.

Market Segmentation:
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

    Cluster 0 — lowest base, fastest growth in both dimensions. Most urgent infrastructure priority — grid connection capacity needs to anticipate rapid near-term uptake.
    Cluster 3 — highest penetration, zero growth. At ceiling. Policy focus should shift to export management and grid stability rather than new connections.
    Cluster 1 — moderate penetration with highest BSR. Solar base is maturing and storage conversion is underway. Battery infrastructure investment warranted.
    Cluster 2 — moderate growth but lowest BSR despite mid-tier solar penetration. Storage conversion is not occurring despite adoption momentum — the clearest signal of a price or policy barrier suppressing battery uptake.

    Residential Clusters 

    Cluster 0 is the most infrastructure-critical — lowest current penetration but fastest growth in both solar and battery. These LGAs will place the most demand on the grid in the near term.
    Cluster 3 is at ceiling — highest penetration and capacity but near-zero growth. Infrastructure investment here should shift from connection capacity to grid stability and export management.
    Cluster 2 is the storage conversion story — moderate solar base but highest BSR. Battery infrastructure (inverters, grid-scale BESS) is the priority here.
    Cluster 1 is the policy concern — moderate solar adoption with no storage uptake and no battery growth. Low BSR suggests a feed-in tariff or price barrier is suppressing storage conversion.

