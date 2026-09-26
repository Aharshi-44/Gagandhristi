@echo off
setlocal EnableDelayedExpansion
title Gagandristhi V2 - Environment Setup

echo =====================================================================
echo       GAGANDRISTHI V2 (SIH 26227) - ONE-TIME SETUP WIZARD
echo =====================================================================
echo.

set ROOT_DIR=%~dp0

:: 1. Check Docker
echo [*] Checking Docker installation...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH!
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

:: 2. Check if Docker is running
echo [*] Checking if Docker daemon is running...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker daemon is not running!
    echo Please start Docker Desktop and run this setup script again.
    pause
    exit /b 1
)
echo [OK] Docker is running.
echo.

:: 3. Start Docker Containers
echo [*] Starting Docker infrastructure containers (PostGIS, Kafka, Debezium, Redis)...
docker inspect gagandristhi-postgres >nul 2>&1
if %errorlevel% equ 0 (
    docker start gagandristhi-postgres gagandristhi-kafka gagandristhi-debezium gagandristhi-redis
) else (
    docker compose up -d
)
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start Docker containers.
    pause
    exit /b 1
)
echo [OK] Docker containers launched.
echo.

:: 4. Wait for PostgreSQL to be ready
echo [*] Waiting for PostgreSQL database to accept connections...
:WAIT_PG
docker exec gagandristhi-postgres pg_isready -U postgres -d garuda >nul 2>&1
if %errorlevel% neq 0 (
    timeout /t 2 /nobreak >nul
    goto WAIT_PG
)
echo [OK] PostgreSQL is ready.
echo.

:: 5. Initialize Schema & Seeds
echo [*] Restoring database schema and seed data...
docker exec -i gagandristhi-postgres psql -U postgres -d garuda < "%ROOT_DIR%Backend\schema.sql" >nul 2>&1
docker exec -i gagandristhi-postgres psql -U postgres -d garuda < "%ROOT_DIR%Backend\seed_channels.sql" >nul 2>&1
docker exec -i gagandristhi-postgres psql -U postgres -d garuda < "%ROOT_DIR%Backend\create_alert_reviews.sql" >nul 2>&1
echo [OK] PostGIS database tables and models successfully seeded.
echo.

:: 6. Register Debezium CDC Connector
echo [*] Registering Debezium CDC connector for real-time alerting...
powershell -ExecutionPolicy Bypass -File "%ROOT_DIR%Backend\register_debezium.ps1"
echo.

:: 7. Backend .env configuration
if not exist "%ROOT_DIR%Backend\.env" (
    echo [*] Generating Backend\.env from template...
    copy "%ROOT_DIR%Backend\.env.example" "%ROOT_DIR%Backend\.env" >nul
    echo [OK] Backend\.env created.
)

:: 8. Install Backend Dependencies
echo [*] Installing Node.js Backend dependencies...
cd /d "%ROOT_DIR%Backend"
call npm install
echo [OK] Backend dependencies installed.
echo.

:: 9. Install Frontend Dependencies
echo [*] Installing Vue 3 Frontend dependencies...
cd /d "%ROOT_DIR%Frontend"
call npm install
echo [OK] Frontend dependencies installed.
echo.

:: 10. Install Python Dependencies
echo [*] Installing Python processing dependencies...
cd /d "%ROOT_DIR%processing"
python -m pip install -r requirements.txt
echo [OK] Python dependencies installed.
echo.

cd /d "%ROOT_DIR%"

echo =====================================================================
echo           SETUP COMPLETED SUCCESSFULLY!
echo =====================================================================
echo.
echo You can now launch all platform microservices in 1-click by running:
echo     start.bat
echo.
pause
