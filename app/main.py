import streamlit as st
import pandas as pd
import clickhouse_connect
import os

st.set_page_config(page_title="Northwind ETL Dashboard", layout="wide")

st.title("Northwind ETL Dashboard")

@st.cache_resource
def get_ch_client():
    return clickhouse_connect.get_client(
        host=os.getenv('CLICKHOUSE_HOST', 'localhost'),
        port=8123,
        username='admin',
        password='admin'
    )

ch_client = get_ch_client()

st.sidebar.header("Status do Pipeline")
try:
    ch_client.command("SELECT 1")
    st.sidebar.success("ClickHouse Online")
except Exception as e:
    st.sidebar.error(f"Erro ClickHouse: {e}")

st.write("Monitoramento em tempo real do pipeline Northwind.")

# Metrics
col1, col2, col3 = st.columns(3)

total_orders = ch_client.command("SELECT count() FROM northwind.orders")
col1.metric("Total de Pedidos", total_orders)

avg_freight = ch_client.command("SELECT round(avg(freight), 2) FROM northwind.orders")
col2.metric("Frete Médio", f"${avg_freight}")

total_details = ch_client.command("SELECT count() FROM northwind.order_details")
col3.metric("Itens de Pedido", total_details)

st.subheader("Volume de Pedidos por Dia")
df_orders = ch_client.query_df("SELECT order_date, count() as count FROM northwind.orders GROUP BY order_date ORDER BY order_date")
if not df_orders.empty:
    st.line_chart(df_orders.set_index('order_date'))
else:
    st.info("Nenhum dado de pedido encontrado.")

st.subheader("Top 10 Cidades por Volume de Pedidos")
df_cities = ch_client.query_df("SELECT ship_city, count() as count FROM northwind.orders GROUP BY ship_city ORDER BY count DESC LIMIT 10")
st.bar_chart(df_cities.set_index('ship_city'))
