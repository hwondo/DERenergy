import sqlite3 as sql
import pandas as pd
import yaml
import glob

def Get_Paths():
    # --- Import data ---# 
    
    # Get path from config file
    with open("./config.yaml","r") as file:
        config = yaml.safe_load(file)
        
    # Obtain paths from Yaml
    aemo_data_path = config['paths']['raw_aemo']
    abs_data_path =  config['paths']['raw_abs']
    Lga2Po_path = config['paths']['Lga2Po']
    rural_path = config['paths']['rural']
    db_path = config['paths']['sql_db']
    
    return aemo_data_path, abs_data_path, Lga2Po_path, rural_path, db_path


def New_Database(db_path: str):
    # --- Create SQL database --- #
    
    conn = sql.connect(db_path)
    conn.close()
    
    return None

def Der_Transform(aemo_data_path: str):
    # --- Clean DER data for import into database --- #
    
    aemo_files = glob.glob(aemo_data_path+"/*.csv")
    
    # Merge DER csv into single dataframe
    df_list = []

    for files in aemo_files:
        name = files[len(aemo_data_path)+1:-4]
        df = pd.read_csv(files)
        
        # Standardise column names
        df.columns = [col.lower()
                            .replace("sum of ", "")
                            .replace("num_", "")
                            .replace("kvah","")
                            .replace("kva","")
                            .replace("post_code","postcode")
                            .strip()
                            .title()
                            .replace("_","")
                        for col in list(df.columns)]
        
        # Clean Postcode column (rows containing aggregates appear with "<" or ">" no. of postcodes)
        df['Postcode'] = pd.to_numeric(df['Postcode'],errors='coerce')
        df.dropna(inplace=True)
        df['Postcode'] = df['Postcode'].astype(int)
        
        df['Year'] = int(name[:4]) # pass year from file name into column
        df['Month'] = str(name[5:])  # pass month from file name into column
        df_list.append(df)


    derr_raw_df = pd.concat(df_list, ignore_index=True)    

    # Select relevant columns
    select =['State', 'Postcode', 'NmiBusRes', 'DerConnections',
        'InstalledDerCapacity', 'SolarConnections', 'SolarCapacity',
        'BatteryConnections', 'BatteryCapacity', 'BatteryStorage',
        'OtherConnections', 'InstalledOtherderCapacity', 'Year']
    
    derr_raw_df = derr_raw_df[select]
    
    return derr_raw_df


def ABS_Transform(abs_data_path: str):
    # --- Clean ABS data for import into database --- #

    select = ['Data Item', 'MEASURE', 'LGA_2021','Region','TIME_PERIOD','OBS_VALUE','Unit of Measure']

    # Import population df from ABS
    population_raw_df = pd.read_csv(abs_data_path+"/ABS_Population.csv")

    # Standardise Columns
    population_raw_df = population_raw_df[select]
    population_raw_df.columns = [col.lower()
                            .replace("of measure", "")
                            .replace("2021", "")
                            .title()
                            .replace(" ", "")
                            .replace("_","")
                            for col in list(population_raw_df.columns)]

    # Import business numbers from ABS
    economic_raw_df = pd.read_csv(abs_data_path+"/ABS_Economic.csv")

    # Clean Columns
    economic_raw_df = economic_raw_df[select]
    economic_raw_df.columns = [cols.lower()
                                .replace("of measure", "")
                                .replace("2021","")
                                .title()
                                .replace(" ","")
                                .replace("_","")
                            for cols in economic_raw_df.columns]



    abs_raw = pd.concat([population_raw_df, economic_raw_df], ignore_index=True)
    
    return abs_raw


def ABS_Dwelling_Transform(abs_data_path: str):
    select = ['DWTSTRD', 'REGION', 'Region', 'TIME_PERIOD', 'OBS_VALUE']
    
    # Import raw dwelling data
    dwelling_raw_df = pd.read_csv(abs_data_path+"/ABS_Dwelling.csv")
    
    # Clean columns
    dwelling_raw_df = dwelling_raw_df[select]
    dwelling_raw_df.columns = ['Type','LGA_2021','Region','TIME_PERIOD', 'OBS_VALUE']
    
    return dwelling_raw_df
    

def Lga2postcode(Lga2Po_path: str):
    # --- Clean LGA to Postcode Data for import into database --- #

    # Import LGA to Postcode data 
    lga2po_df = pd.read_csv(Lga2Po_path)

    # Clean postcode and LGA columns
    lga2po_df.columns = ["Lga", "Region", "Postcode"]
    lga2po_df['Lga'] = pd.to_numeric(lga2po_df['Lga'], errors='coerce').astype('Int64')
    lga2po_df['Postcode'] = pd.to_numeric(lga2po_df['Postcode'], errors='coerce').astype('Int64')
    
    return lga2po_df


def RuralClass(RuralClass_path: str):
    # --- Clean rural classification data --- #
    
    # Import Rural Classification data 
    rural_class_df = pd.read_csv(RuralClass_path)
    
    # Clean columns
    rural_class_df = rural_class_df.drop(labels='Unnamed: 0',axis=1)
    rural_class_df.columns = ['Postcode', 'Area(km2)', 'MMM_Class','MMM_Area']  
    
    return rural_class_df

def Load_Sqldb(db_path: str,
               derr_raw_df: pd.DataFrame,
               abs_raw_df: pd.DataFrame,
               dwelling_raw_df: pd.DataFrame,
               lga2po_df: pd.DataFrame,
               rural_class_df: pd.DataFrame):
    # --- Load into SQL Database --- #

    # Connect to SQL database
    conn = sql.connect(db_path)
    cursor = conn.cursor()

    # Drop existing tables
    cursor.execute("DROP TABLE IF EXISTS Raw_Derr")
    cursor.execute("DROP TABLE IF EXISTS Raw_ABS")
    cursor.execute("DROP TABLE IF EXISTS Raw_Dwelling")
    cursor.execute("DROP TABLE IF EXISTS Lga2Postcode")
    cursor.execute("DROP TABLE IF EXISTS rural_class")

    # Save data in SQL database
    derr_raw_df.to_sql("Raw_Derr",conn, if_exists='replace', index=False)
    abs_raw_df.to_sql("Raw_ABS", conn, if_exists='replace', index=False)
    dwelling_raw_df.to_sql("Raw_Dwelling", conn, if_exists='replace', index=False)
    lga2po_df.to_sql("Lga2Postcode",conn,if_exists='replace', index=False)
    rural_class_df.to_sql("rural_class",conn,if_exists='replace', index=False)
    
    
    conn.close()
    
    return None


def main():
    
    # Get paths from Config file
    aemo_data_path, abs_data_path, Lga2Po_path, rural_path, db_path = Get_Paths()
    
    # Transform data
    derr_raw_df = Der_Transform(aemo_data_path)
    abs_raw_df = ABS_Transform(abs_data_path)
    dwelling_raw_df = ABS_Dwelling_Transform(abs_data_path)
    lga2po_df =  Lga2postcode(Lga2Po_path)
    rural_class_df = RuralClass(rural_path)
    
    # Create SQLite databases
    New_Database(db_path)

    # Load into SQLite database
    Load_Sqldb(
        db_path,
        derr_raw_df,
        abs_raw_df,
        dwelling_raw_df,
        lga2po_df,
        rural_class_df
        )
    
    print("Completed ETL")


if __name__ == "__main__":
    main()
