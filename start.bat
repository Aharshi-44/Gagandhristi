@echo off
setlocal EnableDelayedExpansion
title Gagandristhi V2 - Platform Launcher

echo =====================================================================
echo           GAGANDRISTHI V2 (SIH 26227) - PLATFORM LAUNCHER
echo =====================================================================
echo.

set ROOT_DIR=%~dp0

:: 1. Verify Docker Daemon
echo [*] Checking Docker status...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker daemon is not running!
    echo Please launch Docker Desktop first, then run start.bat again.
    pause
    exit /b 1
)

:: 2. Ensure Infrastructure Containers are Running
echo [*] Ensuring Docker containers (PostGIS, Kafka, Debezium, Redis) are running...
docker inspect gagandristhi-postgres >nul 2>&1
if %errorlevel% equ 0 (
    docker start gagandristhi-postgres gagandristhi-kafka gagandristhi-debezium gagandristhi-redis
) else (
    docker compose up -d
)
echo [OK] Infrastructure services active.
echo.

:: 3. Launch Python Processing Service
echo [*] Starting Python ML Engine on http://localhost:8000...
start "Gagandristhi - Python ML Engine (Port 8000)" cmd /k "cd /d ""%ROOT_DIR%processing"" && uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

:: 4. Launch Node.js Backend
echo [*] Starting Node.js Backend on http://localhost:3000...
start "Gagandristhi - Node.js Backend (Port 3000)" cmd /k "cd /d ""%ROOT_DIR%Backend"" && npm run dev"

:: 5. Launch Vue 3 Frontend
echo [*] Starting Vue 3 Frontend on http://localhost:5173...
start "Gagandristhi - Vue Frontend (Port 5173)" cmd /k "cd /d ""%ROOT_DIR%Frontend"" && npm run dev"

:: 6. Wait and Launch Browser
echo.
echo [*] Waiting 4 seconds for web services to initialize...
timeout /t 4 /nobreak >nul

echo [*] Opening Gagandristhi Analyst Dashboard in browser...
start http://localhost:5173

echo.
echo =====================================================================
echo                ALL SERVICES RUNNING SUCCESSFULLY!
echo =====================================================================
echo.
echo  * Analyst Dashboard:   http://localhost:5173
echo  * Backend API:         http://localhost:3000
echo  * Python ML Engine:    http://localhost:8000
echo  * ML API Docs:         http://localhost:8000/docs
echo  * Debezium Connect:    http://localhost:8083
echo.
echo Leave the 3 microservice terminal windows running while using the app.
echo To shut down all services cleanly, you can run: stop.bat
echo =====================================================================
echo.
pause
