# Modelo Lógico de Dados - Northwind

## Entidade: orders
Representa o cabeçalho do pedido.

| Atributo | Tipo de Dado | Restrição |
|---|---|---|
| order_id | INT | PRIMARY KEY |
| customer_id | VARCHAR(10) | NOT NULL |
| employee_id | INT | |
| order_date | DATE | |
| required_date | DATE | |
| shipped_date | DATE | NULLABLE |
| ship_via | INT | |
| freight | REAL | |
| ship_name | VARCHAR(100) | |
| ship_address | VARCHAR(200) | |
| ship_city | VARCHAR(100) | |
| ship_region | VARCHAR(100) | NULLABLE |
| ship_postal_code | VARCHAR(20) | NULLABLE |
| ship_country | VARCHAR(100) | |

## Entidade: order_details
Representa as linhas/itens de cada pedido.

| Atributo | Tipo de Dado | Restrição |
|---|---|---|
| order_id | INT | PRIMARY KEY, FOREIGN KEY (orders) |
| product_id | INT | PRIMARY KEY |
| unit_price | REAL | NOT NULL |
| quantity | INT | NOT NULL |
| discount | REAL | NOT NULL |

*Nota: A chave primária de order_details é composta por (order_id, product_id).*
