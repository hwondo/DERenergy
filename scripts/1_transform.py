import yaml
import psycopg2
from pathlib import Path


def get_connection():
    with open("./config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    c = config['sql_config']
    
    conn =  psycopg2.connect(
        host=c['server'],
        dbname=c['dbname'],
        user=c['usr'],
        password=c['password']
    )
    
    return conn


def run_sql_file(conn, filepath: Path):
    sql = filepath.read_text()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f"Completed: {filepath.name}")


def main():
    sql_files = sorted(Path("scripts/sql").glob("*.sql"))

    conn = get_connection()

    try:
        for filepath in sql_files:
            print(f"Running: {filepath.name}")
            run_sql_file(conn, filepath)
    except Exception as e:
        conn.rollback()
        print(f"Error in {filepath.name}: {e}")
        raise
    finally:
        conn.close()

    print("Transformed Data.")


if __name__ == "__main__":
    main()