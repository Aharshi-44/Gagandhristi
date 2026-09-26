#!/bin/bash
set -e

echo "====================================================================="
echo "      GAGANDRISTHI V2 (SIH 26227) - ONE-TIME SETUP WIZARD (BASH)"
echo "====================================================================="

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed or not in PATH!"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "[ERROR] Docker daemon is not running! Please start Docker first."
    exit 1
fi

echo "[*] Starting Docker infrastructure containers..."
if docker inspect gagandristhi-postgres &> /dev/null; then
    docker start gagandristhi-postgres gagandristhi-kafka gagandristhi-debezium gagandristhi-redis
else
    docker compose up -d
fi

echo "[*] Waiting for PostgreSQL database to be ready..."
until docker exec gagandristhi-postgres pg_isready -U postgres -d garuda &> /dev/null; do
    sleep 2
done
echo "[OK] PostgreSQL is ready."

echo "[*] Restoring database schema and seed data..."
docker exec -i gagandristhi-postgres psql -U postgres -d garuda < "$ROOT_DIR/Backend/schema.sql" > /dev/null
docker exec -i gagandristhi-postgres psql -U postgres -d garuda < "$ROOT_DIR/Backend/seed_channels.sql" > /dev/null
docker exec -i gagandristhi-postgres psql -U postgres -d garuda < "$ROOT_DIR/Backend/create_alert_reviews.sql" > /dev/null
echo "[OK] Database successfully configured."

echo "[*] Waiting for Debezium Kafka Connect to become ready..."
until curl -s http://localhost:8083/connectors &> /dev/null; do
    sleep 3
done

echo "[*] Registering Debezium CDC Connector..."
curl -s -X POST http://localhost:8083/connectors \
  -H "Content-Type: application/json" \
  -d '{
    "name": "gagandristhi-alerts-connector",
    "config": {
      "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
      "tasks.max": "1",
      "plugin.name": "pgoutput",
      "database.hostname": "gagandristhi-postgres",
      "database.port": "5432",
      "database.user": "postgres",
      "database.password": "Minar@123",
      "database.dbname": "garuda",
      "database.server.name": "garuda_server",
      "topic.prefix": "garuda_cdc",
      "table.include.list": "public.alerts",
      "publication.name": "dbz_publication",
      "publication.autocreate.mode": "filtered",
      "schema.history.internal.kafka.bootstrap.servers": "gagandristhi-kafka:29092",
      "schema.history.internal.kafka.topic": "schema-changes.garuda"
    }
  }' > /dev/null || true
echo "[OK] Debezium connector configured."

if [ ! -f "$ROOT_DIR/Backend/.env" ]; then
    echo "[*] Creating Backend/.env from template..."
    cp "$ROOT_DIR/Backend/.env.example" "$ROOT_DIR/Backend/.env"
fi

echo "[*] Installing Backend dependencies..."
(cd "$ROOT_DIR/Backend" && npm install)

echo "[*] Installing Frontend dependencies..."
(cd "$ROOT_DIR/Frontend" && npm install)

echo "[*] Installing Python processing dependencies..."
(cd "$ROOT_DIR/processing" && pip install -r requirements.txt)

echo "====================================================================="
echo "           SETUP COMPLETED SUCCESSFULLY!"
echo "====================================================================="
echo "You can now run: ./start.sh"
