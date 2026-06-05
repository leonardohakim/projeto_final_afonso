#!/usr/bin/env bash
set -euo pipefail

echo "Iniciando ingestao em background..."
python3 scripts/etl.py &
PID=$!

sleep 2
echo "Matando ClickHouse no meio da ingestao..."
docker kill gabriel-csilva-20261sre-projeto-final-clickhouse-1

sleep 5
echo "Subindo ClickHouse de novo..."
docker start gabriel-csilva-20261sre-projeto-final-clickhouse-1
echo "Aguardando healthy..."
until docker inspect -f '{{.State.Health.Status}}' gabriel-csilva-20261sre-projeto-final-clickhouse-1 | grep -q healthy; do sleep 2; done

wait $PID
echo "Ingestão sobreviveu!"
