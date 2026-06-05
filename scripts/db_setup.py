import clickhouse_connect
import psycopg2
import os

def setup_clickhouse():
    client = clickhouse_connect.get_client(
        host='localhost',
        port=8123,
        username='admin',
        password='admin'
    )
    
    # Create orders table
    client.command("""
    CREATE TABLE IF NOT EXISTS northwind.orders (
        order_id UInt32,
        customer_id String,
        employee_id UInt32,
        order_date Date,
        required_date Date,
        shipped_date Nullable(Date),
        ship_via UInt32,
        freight Float32,
        ship_name String,
        ship_address String,
        ship_city String,
        ship_region Nullable(String),
        ship_postal_code Nullable(String),
        ship_country String
    ) ENGINE = ReplacingMergeTree()
    ORDER BY order_id
    """)
    
    # Create order_details table
    client.command("""
    CREATE TABLE IF NOT EXISTS northwind.order_details (
        order_id UInt32,
        product_id UInt32,
        unit_price Float32,
        quantity UInt32,
        discount Float32
    ) ENGINE = ReplacingMergeTree()
    ORDER BY (order_id, product_id)
    """)
    print("ClickHouse tables created.")

def setup_postgres():
    conn = psycopg2.connect(
        host="localhost",
        database="northwind",
        user="admin",
        password="admin"
    )
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id INT PRIMARY KEY,
        customer_id VARCHAR(10),
        employee_id INT,
        order_date DATE,
        required_date DATE,
        shipped_date DATE,
        ship_via INT,
        freight REAL,
        ship_name VARCHAR(100),
        ship_address VARCHAR(200),
        ship_city VARCHAR(100),
        ship_region VARCHAR(100),
        ship_postal_code VARCHAR(20),
        ship_country VARCHAR(100)
    );
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS order_details (
        order_id INT,
        product_id INT,
        unit_price REAL,
        quantity INT,
        discount REAL,
        PRIMARY KEY (order_id, product_id)
    );
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("Postgres tables created.")

if __name__ == "__main__":
    setup_clickhouse()
    setup_postgres()
