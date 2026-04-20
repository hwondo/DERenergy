# Distributed Energy Resources (DER) Dashboard and Analysis

---

## Overview

This project analyses Distributed Energy Resource (DER) adoption across Local 
Government Areas (LGAs) in Australia, focusing on capacity trends, socioeconomic 
characteristics, and adoption patterns.

**Objectives:**

- Derive key metrics for solar and batter adoption. 
- Cluster LGAs into adoption profiles to support policy-making.
- Identify key drivers of solar and batter adoption. 
- Deliver a Power BI dashboard that provides intuitive, data-driven insights 
  for decision-makers.

---

## Key Insights

1. LGAs are segmented into interpretable groups based on adoption behaviours 
   (see Market Segmentation below). Notably:
   - LGAs with strong solar adoption but low battery adoption were identified, 
     indicating potential pricing barriers to battery storage conversion.
   - LGAs with saturated solar and battery adoption were identified. Policies 
     targeting energy export rather than further solar adoption should be 
     prioritised in these areas.
2. No statistically significant difference in residential capacity was found 
   between high- and low-income LGAs.
3. Analysis of differences in business capacity between rural and urban LGAs 
   could not be completed due to a fundamental overlap violation — a substantial 
   proportion of LGAs could not be matched after controlling for observed 
   covariates.

---

## Detailed Objectives

1. Aggregate and clean DER and socioeconomic data at the LGA level.
2. Load cleaned data into an SQL database for reproducible and future analysis.
3. Generate metrics that provide a clear summary of DER adoption across Australia.
4. Cluster LGAs based on metrics to profile adoption behaviour.
5. Run statistical inference over socioeconomic variables to determine key 
   drivers of DER adoption.
6. Produce an interactive dashboard summarising key metrics, socioeconomic data, 
   and cluster insights.

---

## Usage

1. Save raw DER Registry (DERR) data from AEMO in `data/aemo` and raw ABS data 
   in `data/abs`.
2. Run the ETL script at `code/ETL.py` to clean and load data into the SQLite 
   database at `data/sql_db/energy.db`.
3. Run or view notebooks in order. The `market_segmentation` notebook is 
   required to generate LGA clusters for the dashboard. The 
   `observational_causal_inference` notebook applies propensity score matching 
   to analyse the effect of rurality on DER adoption patterns.
4. Update the Power BI dashboard at `dashboard/EnergyDashboard.pbix`.

---

## Data Sources

| Source | Variables |
|---|---|
| ABS (Australian Bureau of Statistics) | Population, median age, income, education levels, business sectors and business size |
| DER Registry (AEMO) | Installed capacity, DER connections, and breakdown by DER type (solar, battery, other) |
| Geographical mapping | Postcode-to-LGA mapping based on the 2021 boundary map |
| Modified Monash Model | Classification of locations as metropolitan, rural, remote, or very remote |

---

## Data Processing

### DERR Preprocessing

- Merged multiple DERR files (one per year) into a single file.
- Standardised column names.
- Attached LGA codes to postcodes using the 2021 postcode map.
- Extracted year and month from file names into a date column.
- Selected relevant DERR columns.

### ABS Preprocessing

- Selected relevant columns from raw ABS population and economic data.
- Standardised column names.
- Combined into a single DataFrame.

### Star Schema in SQLite Database

| Query | Description |
|---|---|
| `Q_abs_data_items` | Dimension table of ABS measure codes and measure items |
| `Q_Region` | Dimension table of postcode-to-LGA correspondence |
| `Q_Main_Derr` | Fact table for DERR data, aggregated by LGA and year |
| `Q_Population_Agg` | Population data table in long form |
| `Q_Business_Agg` | Economic data table in long form |

### ETL for Analysis and Power BI Dashboard

**DER Fact Table:**
- Dropped `None` and `Blank` entries in the `Type` column.
- Removed misaligned LGAs and recorded their codes in an SQL table.
- Filtered out 2025 data as the year is incomplete.

**Population and Economic Fact Tables:**
- Applied forward-fill followed by back-fill to population data. With the 
  exception of the first year, each year corresponds to data from the most 
  recently reported census.
- Processed mismatches between total business counts and the sum of business 
  sector counts. Where the discrepancy is less than 5% of the total business 
  count, missing values are filled with zero. Remaining affected LGAs are 
  dropped.

---

## Database Schema

### `Dim_DataItem`

| Column | Description |
|---|---|
| `DataItem` | Name of ABS variable |
| `Measure` | ABS code for variable |

### `Dim_Region`

| Column | Description |
|---|---|
| `Postcode` | Postcode |
| `State` | State the postcode is in |
| `Lga` | LGA code of postcode |
| `Region` | Name of postcode region |

### `Fact_Population`

| Column | Description |
|---|---|
| `Lga` | LGA code |
| `Year` | Year of data |
| `TotalPopulation` | Total population |
| `PopulationDensity` | Population density |
| `MedianAge` | Median age |
| `MedianEquivalisedHouseholdIncome` | Median equivalised household income |
| `Certificate` | Share of population with a certificate qualification |
| `AdvDiploma` | Share of population with an advanced diploma |
| `BachelorsDegree` | Share of population with a bachelor's degree |
| `GraduateDiploma` | Share of population with a graduate diploma |
| `Postgraduate` | Share of population with a postgraduate degree |

### `Fact_Economic`

| Column | Description |
|---|---|
| `Lga` | LGA code |
| `Year` | Year of data |
| `TotalBusinesses` | Total number of businesses |
| `PrimaryIndustry` | Number of businesses in the primary industry sector |
| `SecondaryIndustry` | Number of businesses in the secondary industry sector |
| `TertiaryIndustry` | Number of businesses in the tertiary industry sector |
| `QuaternaryIndustry` | Number of businesses in the quaternary industry sector |
| `SmallBusinesses` | Number of small businesses |
| `MediumBusinesses` | Number of medium businesses |
| `LargeBusinesses` | Number of large businesses |

---

## Exploratory Data Analysis

The data is first split into two tables: residential data (DER type `RESIDENTIAL` 
joined with ABS population data) and business data (DER type `BUSINESS` joined 
with ABS economic data).

### Residential Data

The following features are positively skewed and are normalised using 
log base-10 scaling:

- `TotalCapacity`, `BatteryCapacity`, `SolarCapacity`, `OtherCapacity`
- `TotalDerConnections`, `BatteryConnections`, `SolarConnections`, `OtherConnections`
- `TotalPopulation`, `PopulationDensity`

There is very high correlation (> 0.9) between total capacity, battery capacity, 
total connections, and solar connections. Solar capacity dominates total capacity. 
Total capacity also correlates highly with LGA population, reflecting the 
expected size effect of larger LGAs having greater aggregate DER capacity.

Capacity per capita is therefore used as the primary metric, alongside a growth 
rate metric defined as the OLS slope over 2021–2024 normalised by baseline 
capacity.

Capacity per capita shows moderate negative correlation with total population, 
population density, university degree attainment, and median income — reflecting 
a metropolitan versus suburban divide. A moderate positive correlation with 
growth rate is expected given its derivation.

### Business Data

All features are positively skewed and are normalised using a log transformation. 
Total capacity and solar capacity are very highly correlated (> 0.9). Moderate 
to weak correlations are observed with business count across size and industry 
type, with the exception of primary industry.

Capacity per business is used as the primary metric to remove the LGA size 
effect. A similar correlation profile is observed: capacity per business is 
strongly negatively correlated with total business count and the number of 
quaternary industry businesses, again reflecting a metropolitan versus suburban 
divide.

---

## KPIs

| Metric | Definition | Policy Relevance |
|---|---|---|
| **Penetration Rate** | Share of total dwellings with at least one DER connection | Primary equity and access indicator — measures adoption breadth regardless of system size |
| **Battery-to-Solar Ratio (BSR)** | Battery connections as a proportion of solar connections | A low BSR in a high-penetration LGA signals a price or policy barrier suppressing storage uptake |
| **Capacity per Connection (CPC)** | Total installed capacity divided by number of DER connections | Measures average system size — particularly informative for business segments where large commercial installs dominate aggregate capacity |
| **Capacity per Dwelling (CPD)** | Total installed capacity divided by total dwellings | Combines adoption breadth and system size into a single grid-relevant metric |
| **Growth Rate** | OLS linear trend in installed capacity over 2021–2024, normalised by baseline capacity | Measures adoption velocity — an LGA with low penetration but high growth rate is a near-term infrastructure priority |

---

## Market Segmentation

K-means clustering (four clusters) is applied separately to residential and 
business DERR data. The features used are:

- `TotalCapacity`
- `TotalDerConnections`
- `CapacityPerCapita`
- `CapacityPerConnection`
- `GrowthRate`

A median is taken over 2021–2024 (excluding growth rate) for each feature, 
followed by standard normalisation. Clusters are projected onto three principal 
components for interpretation. No significant cluster separation is visible when 
projecting onto socioeconomic or economic data — further analysis is required to 
assess predictive power from these variables.

### Business Clusters

| Cluster | Profile | Policy Implication |
|---|---|---|
| Cluster 0 | Lowest base capacity, fastest growth | Most urgent infrastructure priority — grid connection capacity must anticipate rapid near-term uptake |
| Cluster 3 | Highest penetration, zero growth | At ceiling — policy focus should shift to export management and grid stability rather than new connections |
| Cluster 1 | Moderate penetration, highest BSR | Solar base is maturing and storage conversion is underway — battery infrastructure investment is warranted |
| Cluster 2 | Moderate growth, lowest BSR despite mid-tier solar penetration | Storage conversion is not occurring despite adoption momentum — the clearest signal of a price or policy barrier suppressing battery uptake |

### Residential Clusters

| Cluster | Profile | Policy Implication |
|---|---|---|
| Cluster 0 | Lowest penetration, fastest growth in solar and battery | Most infrastructure-critical — these LGAs will place the greatest demand on the grid in the near term |
| Cluster 3 | Highest penetration and capacity, near-zero growth | At ceiling — investment should shift from connection capacity to grid stability and export management |
| Cluster 2 | Moderate solar base, highest BSR | Battery infrastructure (inverters, grid-scale BESS) is the priority |
| Cluster 1 | Moderate solar adoption, no storage uptake, no battery growth | Low BSR suggests a feed-in tariff or price barrier is suppressing storage conversion |