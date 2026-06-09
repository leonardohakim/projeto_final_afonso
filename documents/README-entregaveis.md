# Checklist de Entregáveis - Aula 05

Checklist resumido dos entregáveis consolidados para o projeto Northwind ETL.

- [x] MinIO configurado como origem principal da camada Bronze, com fallback para CSV local.
- [x] ETL atualizado com retry, CircuitBreaker e variáveis de ambiente para a fonte de dados.
- [x] Healthchecks adicionados aos serviços críticos no `docker-compose.yml`.
- [x] Suíte completa de testes pytest organizada em `tests/unit/` e `tests/integration/`.
- [x] Testes unitários do `CircuitBreaker` cobrindo estados, transições e timeout.
- [x] Testes de integração do pipeline cobrindo ingestão e carga em Postgres e ClickHouse.
- [x] Tabela ATAM documentada em [documents/atam.md](atam.md) com os 7 atributos de qualidade.
- [x] README atualizado com instruções finais de execução e validação.

## Comandos Principais

```bash
docker-compose up -d
python3 scripts/db_setup.py
python3 scripts/etl.py
python -m pytest tests/ -v --tb=short
```