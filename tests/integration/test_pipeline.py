from pathlib import Path

import clickhouse_connect
import pandas as pd
import psycopg2
import pytest

import etl
from db_setup import setup_clickhouse, setup_postgres


CSV_DIR = Path(etl.CSV_DIR)


def _services_available():
    try:
        ch_client = clickhouse_connect.get_client(
            host=etl.CH_HOST,
            port=8123,
            username="admin",
            password="admin",
        )
        ch_client.query("SELECT 1")

        pg_conn = psycopg2.connect(
            host=etl.PG_HOST,
            database="northwind",
            user="admin",
            password="admin",
        )
        try:
            with pg_conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        finally:
            pg_conn.close()
    except Exception:
        return False

    return True


@pytest.fixture()
def prepared_pipeline_environment():
    if not _services_available():
        pytest.skip("Postgres/ClickHouse indisponíveis para o teste de integração")

    setup_clickhouse()
    setup_postgres()

    ch_client = clickhouse_connect.get_client(
        host=etl.CH_HOST,
        port=8123,
        username="admin",
        password="admin",
    )
    pg_conn = psycopg2.connect(
        host=etl.PG_HOST,
        database="northwind",
        user="admin",
        password="admin",
    )

    ch_client.command("TRUNCATE TABLE IF EXISTS northwind.orders")
    ch_client.command("TRUNCATE TABLE IF EXISTS northwind.order_details")
    with pg_conn.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE order_details, orders")
    pg_conn.commit()

    try:
        yield ch_client, pg_conn
    finally:
        ch_client.command("TRUNCATE TABLE IF EXISTS northwind.orders")
        ch_client.command("TRUNCATE TABLE IF EXISTS northwind.order_details")
        with pg_conn.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE order_details, orders")
        pg_conn.commit()
        pg_conn.close()


def test_process_orders_loads_rows_into_both_databases(prepared_pipeline_environment):
    ch_client, pg_conn = prepared_pipeline_environment
    expected_rows = len(pd.read_csv(CSV_DIR / "northwind_orders.csv"))

    etl.process_orders()

    clickhouse_rows = ch_client.query("SELECT count() FROM northwind.orders").result_rows[0][0]
    with pg_conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM orders")
        postgres_rows = cursor.fetchone()[0]

    assert clickhouse_rows == expected_rows
    assert postgres_rows == expected_rows


def test_process_order_details_loads_rows_into_both_databases(prepared_pipeline_environment):
    ch_client, pg_conn = prepared_pipeline_environment
    expected_rows = len(pd.read_csv(CSV_DIR / "northwind_order_details.csv"))

    etl.process_order_details()

    clickhouse_rows = ch_client.query("SELECT count() FROM northwind.order_details").result_rows[0][0]
    with pg_conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM order_details")
        postgres_rows = cursor.fetchone()[0]

    assert clickhouse_rows == expected_rows
    assert postgres_rows == expected_rows