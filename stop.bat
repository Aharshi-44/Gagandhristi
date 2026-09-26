@echo off
title Gagandristhi V2 - Stop Services

echo =====================================================================
echo                GAGANDRISTHI V2 - SHUT DOWN
echo =====================================================================
echo.
echo [*] Stopping Docker containers (PostgreSQL, Kafka, Debezium, Redis)...
docker stop gagandristhi-postgres gagandristhi-kafka gagandristhi-debezium gagandristhi-redis >nul 2>&1
docker compose stop >nul 2>&1
echo [OK] Docker containers stopped.
echo.
echo Note: Please close the 3 command prompt windows running Python,
echo Node.js, and Vite manually if they are still open.
echo.
echo Platform successfully shut down.
echo =====================================================================
pause
