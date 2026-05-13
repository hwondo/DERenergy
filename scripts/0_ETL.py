#############################################################################
### Clean Raw Files and Load into SQLite and PostgreSQl/PostGIS Databases ###
#############################################################################

# Raw files directory specified in config.yaml file
# SQL connections specified in config.yaml file
# Run in script in its contained directory. 

import yaml
import glob
import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text

def get_config():
    with open("./config.yaml", "r") as f:
        return yaml.safe_load(f)

def get_engine(config):
    c = config['sql_config']
    return create_engine(
        f"postgresql://{c['usr']}:{c['password']}@{c['server']}:{c['port']}/{c['dbname']}"
    )

# Force postcode as string (prevents errors from 0012 type)
FORCE_DTYPE = {
    "postcode": str, "post_code":str, "POA 2021 Code":str,
    "LGA_2021": str
    } 

# --- Functions to Process Raw Data --- #


# AEMO Data
def der_transform(aemo_data_path: str) -> pd.DataFrame:
    ''' Clean AEMO DER data'''
    
    # Get data from folder
    aemo_files = glob.glob(aemo_data_path + "/*.csv")
    df_list = []

    #  Merge multiple years of DER csv into single dataframe
    for filepath in aemo_files:
        name = filepath[len(aemo_data_path)+1:-4]
        df = pd.read_csv(filepath,dtype=FORCE_DTYPE)

        df.columns = [
            col.lower()
               .replace("sum of ", "")
               .replace("num_", "")
               .replace("kvah", "")
               .replace("kva", "")
               .replace("post_code", "postcode")
               .strip()
               .strip("_")
            for col in df.columns
        ]

        # Clean Postcode column (rows containing aggregates appear with "<" or ">" no. of postcodes)
        df = df[~df['postcode'].str.contains('<|>', na=False)]
        df.dropna(inplace=True)
        
        
        df['year'] = int(name[:4]) # pass year from file name into column
        df['month'] = str(name[5:])  # pass month from file name into column
        df_list.append(df)
        

    derr_df = pd.concat(df_list, ignore_index=True)

    return derr_df

# ABS Census Data
def abs_transform(abs_data_path: str) -> pd.DataFrame:
    ''' Clean ABS census data  '''
    
    # Select relevant columns 
    select = ['Data Item', 'MEASURE', 'LGA_2021', 'Region',
              'TIME_PERIOD', 'OBS_VALUE', 'Unit of Measure']

    # Standardise Columns
    def clean_cols(df):
        df.columns = [
            col.lower()
               .replace("of measure", "")
               .replace("_2021", "")
               .strip()
               .replace(" ", "_")
            for col in df.columns
        ]
        return df
    
    # Read data
    pop_df = pd.read_csv(abs_data_path + "/ABS_Population.csv",dtype=FORCE_DTYPE)[select]
    econ_df = pd.read_csv(abs_data_path + "/ABS_Economic.csv",dtype=FORCE_DTYPE)[select]
    
    # Clean cols
    pop_df  = clean_cols(pop_df)
    econ_df = clean_cols(econ_df)

    return pd.concat([pop_df, econ_df], ignore_index=True)

# ABS Dwelling Data
def abs_dwelling_transform(abs_data_path: str) -> pd.DataFrame:
    ''' Clean ABS Dwelling data  '''

    # Import raw dwelling data
    df = pd.read_csv(abs_data_path + "/ABS_Dwelling.csv",dtype=FORCE_DTYPE)
    # Select relevant columns
    df = df[['DWTSTRD', 'REGION', 'Region', 'TIME_PERIOD', 'OBS_VALUE']]
    # rename
    df.columns = ['Type', 'LGA_2021', 'Region', 'TIME_PERIOD', 'OBS_VALUE']
    
    return df


# Monash Model Rural Classification Data
def rural_transform(rural_path: str) -> pd.DataFrame:
    
    # Import Rural Classification data 
    df = pd.read_csv(rural_path,dtype=FORCE_DTYPE)
    
    # Clean columns
    df = df.drop(labels='Unnamed: 0',axis=1)
    df.columns = ['Postcode', 'Area_km2', 'MMM_Class','MMM_Area']  
    return df

# --- Functions to Load Tables --- #

def load_tables(df_dict: dict, engine):
    ''' Load tables from df_dict = {name: df} into SQL server via engine'''
    
    for name, df in df_dict.items():
        df.columns = df.columns.str.lower()
        df.to_sql(name=name, con=engine, schema="raw",
                  if_exists="replace", index=False)
        print(f"Loaded: raw.{name}")


def load_spatial(filepath: str, name: str, engine):
    ''' Load spatial data from filepath into SQL server via engine'''

    gdf = gpd.read_file(filepath)
    crs = gdf.crs
    gdf.columns = gdf.columns.str.lower()

    gdf.to_postgis(name=name, con=engine, schema="raw",
                   if_exists="replace", index=False)

    with engine.connect() as conn:
        conn.execute(text(
            f'CREATE INDEX IF NOT EXISTS idx_{name}_geometry '
            f'ON raw."{name}" USING GIST(geometry)'
        ))
        conn.commit()

    print(f"Loaded spatial: raw.{name} (CRS: {crs})")


def main():
    
    # Get paths and connect to PostgreSQL server 
    config = get_config()
    paths  = config['paths']
    engine = get_engine(config)

    # Create data dictionary 
    df_dict = {
        "raw_der":     der_transform(paths['raw_aemo']),
        "raw_abs":      abs_transform(paths['raw_abs']),
        "raw_dwelling": abs_dwelling_transform(paths['raw_abs']),
        "rural_class":  rural_transform(paths['rural']),
    } # < ----- Name tables here 

    # Load data into Server
    load_tables(df_dict, engine)
    
    # Load spatial data into server
    load_spatial(paths['lga_shape'], 'lga_boundary', engine)
    load_spatial(paths['poa_shape'], 'poa_boundary', engine)

    print("ETL complete.")


if __name__ == "__main__":
    main()