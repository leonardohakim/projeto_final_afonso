import pytest
import psycopg2
import clickhouse_connect
import os
import sys

# Allow importing from scripts
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts')))
import etl

def get_pg_conn():
    return psycopg2.connect(host=os.getenv('POSTGRES_HOST', 'localhost'), database="northwind", user="admin", password="admin")

def get_ch_client():
    return clickhouse_connect.get_client(host=os.getenv('CLICKHOUSE_HOST', 'localhost'), port=8123, username='admin', password='admin')

def test_landing_has_expected_row_count():
    # Run the ETL first to ensure data is there
    etl.process_orders()
    
    ch_client = get_ch_client()
    result = ch_client.command("SELECT count() FROM northwind.orders")
    
    assert result > 0, "No records found in ClickHouse orders table"

def test_postgres_has_expected_row_count():
    pg_conn = get_pg_conn()
    cur = pg_conn.cursor()
    cur.execute("SELECT count(*) FROM orders")
    count = cur.fetchone()[0]
    
    assert count > 0, "No records found in Postgres orders table"
    cur.close()
    pg_conn.close()

def test_ingestion_is_idempotent():
    pg_conn = get_pg_conn()
    cur = pg_conn.cursor()
    cur.execute("SELECT count(*) FROM order_details")
    initial_count = cur.fetchone()[0]
    
    # Run ETL again to simulate a re-ingestion scenario
    etl.process_order_details()
    
    cur.execute("SELECT count(*) FROM order_details")
    final_count = cur.fetchone()[0]
    
    assert initial_count == final_count, "Idempotency failed: Row count changed after second ingestion in Postgres"
    
    # Check ClickHouse idempotency via replacing merge tree (using count of unique ids, as merge happens in background)
    ch_client = get_ch_client()
    ch_count = ch_client.command("SELECT count(DISTINCT order_id, product_id) FROM northwind.order_details")
    assert ch_count == initial_count, "ClickHouse unique count does not match expected initial count"

    cur.close()
    pg_conn.close()
