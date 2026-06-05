# Evidências de Estresse e Resiliência (ATAM)

Este documento centraliza as evidências das táticas arquiteturais aplicadas ao pipeline Northwind, correspondendo ao **Critério 04** (Evidências de Execução).

## SP-01 · Healthcheck do ClickHouse e Postgres
- **Antes:** O Docker considerava o serviço "UP" imediatamente, causando falhas (Race Conditions) caso o Streamlit ou o ETL tentassem conectar antes da porta estar pronta.
- **Tática Aplicada:** Healthchecks granulares com `start_period=15s`, `interval=5s` e comandos de validação nativos (`wget` para ClickHouse, `pg_isready` para Postgres).
- **Depois:** O pipeline e o dashboard sobem de forma orquestrada (`depends_on: service_healthy`). Zero falhas de inicialização registradas no log do Docker.

## SP-02 e SP-03 · Ingestor SPOF e Circuit Breaker
- **Antes:** Se o banco de dados caísse por 2 segundos durante a ingestão, o Pandas/Psycopg abortaria a execução inteira.
- **Tática Aplicada:** Uso do decorador `@tenacity.retry` (Backoff Exponencial) e da classe customizada `CircuitBreaker`.
- **Depois:** Executamos o script `stress/01_kill_clickhouse.sh`. O processo de ETL foi iniciado e, no meio da execução, o container do ClickHouse foi "morto" intencionalmente. O script de ETL pausou, o mecanismo de Retry entrou em ação absorvendo a queda. O banco voltou, ficou "healthy", e a ingestão terminou com sucesso, provando a eficácia da tática.

## SP-04 · Latência do Dashboard
- **Antes:** Queries agregadas diretas ao banco poderiam degradar a performance se houvesse dezenas de usuários simultâneos.
- **Tática Aplicada:** Implementação do `@st.cache_resource` no Streamlit.
- **Depois:** Proteção do OLAP contra picos de requisições idênticas.

## SP-05 · Segurança e Credenciais
- **Antes:** Risco de commit de chaves e variáveis expostas.
- **Tática Aplicada:** Padrão "Limit Exposure". Criação rigorosa de `.gitignore` bloqueando arquivos `.env` e artefatos locais.
