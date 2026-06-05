import pandas as pd
import clickhouse_connect
import psycopg2
from psycopg2.extras import execute_values
import os
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Import local CircuitBreaker
from breakers import CircuitBreaker

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configs
CSV_DIR = 'spec/arquivos_csv_northwind'
CH_HOST = os.getenv('CLICKHOUSE_HOST', 'localhost')
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')

# Initialize Circuit Breakers for Databases
ch_breaker = CircuitBreaker(failure_threshold=5, recovery_seconds=30)
pg_breaker = CircuitBreaker(failure_threshold=5, recovery_seconds=30)

def get_clickhouse_client():
    return clickhouse_connect.get_client(host=CH_HOST, port=8123, username='admin', password='admin')

def get_postgres_conn():
    return psycopg2.connect(host=PG_HOST, database="northwind", user="admin", password="admin")

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True
)
def load_to_clickhouse_with_retry(table_name, df):
    """Loads a dataframe to ClickHouse wrapped with Retry and CircuitBreaker."""
    ch_client = get_clickhouse_client()
    # cb.call executes the lambda. If it fails consecutively, it opens the circuit.
    ch_breaker.call(lambda: ch_client.insert_df(table_name, df))
    logging.info(f"Loaded {len(df)} rows to ClickHouse table {table_name}", extra={"rows": len(df)})

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True
)
def load_to_postgres_with_retry(insert_query, values, desc):
    """Loads data to Postgres wrapped with Retry and CircuitBreaker."""
    def _execute():
        pg_conn = get_postgres_conn()
        try:
            cur = pg_conn.cursor()
            execute_values(cur, insert_query, values)
            pg_conn.commit()
            cur.close()
        finally:
            pg_conn.close()
    
    pg_breaker.call(_execute)
    logging.info(f"Loaded {len(values)} rows to Postgres ({desc})", extra={"rows": len(values)})

def process_orders():
    logging.info("Processing orders...")
    df = pd.read_csv(f"{CSV_DIR}/northwind_orders.csv")
    
    # Validation/Cleaning
    df['order_date'] = pd.to_datetime(df['order_date']).dt.date
    df['required_date'] = pd.to_datetime(df['required_date']).dt.date
    df['shipped_date'] = pd.to_datetime(df['shipped_date']).dt.date
    # Replace NaT with None for SQL null compatibility
    df = df.where(pd.notnull(df), None)
    
    # Load to ClickHouse
    load_to_clickhouse_with_retry('northwind.orders', df)
    
    # Load to Postgres
    df_pg = df.astype(object).where(pd.notnull(df), None)
    columns = df_pg.columns.tolist()
    values = [tuple(x) for x in df_pg.values]
    
    insert_query = f"""
    INSERT INTO orders ({", ".join(columns)})
    VALUES %s
    ON CONFLICT (order_id) DO UPDATE SET
    {", ".join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'order_id'])}
    """
    load_to_postgres_with_retry(insert_query, values, 'orders')

def process_order_details():
    logging.info("Processing order details...")
    df = pd.read_csv(f"{CSV_DIR}/northwind_order_details.csv")
    
    # Load to ClickHouse
    load_to_clickhouse_with_retry('northwind.order_details', df)
    
    # Load to Postgres
    df_pg = df.astype(object).where(pd.notnull(df), None)
    columns = df_pg.columns.tolist()
    values = [tuple(x) for x in df_pg.values]
    
    insert_query = f"""
    INSERT INTO order_details ({", ".join(columns)})
    VALUES %s
    ON CONFLICT (order_id, product_id) DO UPDATE SET
    {", ".join([f"{col} = EXCLUDED.{col}" for col in columns if col not in ['order_id', 'product_id']])}
    """
    load_to_postgres_with_retry(insert_query, values, 'order_details')

if __name__ == "__main__":
    process_orders()
    process_order_details()
    logging.info("ETL process completed successfully.")
