#!/bin/bash

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "====================================================================="
echo "      GAGANDRISTHI V2 (SIH 26227) - PLATFORM LAUNCHER (BASH)"
echo "====================================================================="

echo "[*] Ensuring Docker infrastructure containers are running..."
if docker inspect gagandristhi-postgres &> /dev/null; then
    docker start gagandristhi-postgres gagandristhi-kafka gagandristhi-debezium gagandristhi-redis
else
    docker compose up -d
fi

echo "[*] Launching Python ML Engine (Port 8000)..."
(cd "$ROOT_DIR/processing" && uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload) &
PID_PY=$!

echo "[*] Launching Node.js Backend (Port 3000)..."
(cd "$ROOT_DIR/Backend" && npm run dev) &
PID_BE=$!

echo "[*] Launching Vue 3 Frontend (Port 5173)..."
(cd "$ROOT_DIR/Frontend" && npm run dev) &
PID_FE=$!

echo ""
echo "====================================================================="
echo "                ALL SERVICES RUNNING IN BACKGROUND"
echo "====================================================================="
echo "  * Frontend Dashboard:   http://localhost:5173"
echo "  * Backend API:          http://localhost:3000"
echo "  * Python ML Engine:     http://localhost:8000"
echo "  * ML API Docs:          http://localhost:8000/docs"
echo "====================================================================="
echo "Press Ctrl+C to terminate all services."

# Trap Ctrl+C to kill child background processes
trap "kill $PID_PY $PID_BE $PID_FE; exit" INT TERM
wait
