@echo off
REM Deployment script for the crawler service (Windows)
REM Supports development and production environments

set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=development

set COMPOSE_FILE=docker-compose.yml
if "%ENVIRONMENT%"=="production" (
    set COMPOSE_FILE=docker-compose.prod.yml
    echo Deploying to PRODUCTION environment
) else (
    echo Deploying to DEVELOPMENT environment
)

echo Using compose file: %COMPOSE_FILE%

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not running
    exit /b 1
)

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: docker-compose is not installed
    exit /b 1
)

REM Create necessary directories
echo Creating necessary directories...
if not exist logs mkdir logs
if not exist data mkdir data
if not exist ssl mkdir ssl

REM Pull latest images (for production)
if "%ENVIRONMENT%"=="production" (
    echo Pulling latest images...
    docker-compose -f %COMPOSE_FILE% pull
)

REM Build and start services
echo Building and starting services...
docker-compose -f %COMPOSE_FILE% up --build -d

REM Wait for services to be healthy
echo Waiting for services to be healthy...
timeout /t 10 /nobreak >nul

REM Check service health
echo Checking service health...
curl -f http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Crawler service is healthy
) else (
    echo ❌ Crawler service is not responding
    echo Checking logs...
    docker-compose -f %COMPOSE_FILE% logs crawler-service
    exit /b 1
)

REM Check Redis health
docker-compose -f %COMPOSE_FILE% exec redis redis-cli ping >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Redis is healthy
) else (
    echo ❌ Redis is not responding
    exit /b 1
)

REM Show running services
echo Running services:
docker-compose -f %COMPOSE_FILE% ps

echo.
echo 🚀 Deployment completed successfully!
echo.
echo Service URLs:
echo   - API: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo   - Health Check: http://localhost:8000/health
echo.
echo To view logs:
echo   docker-compose -f %COMPOSE_FILE% logs -f
echo.
echo To stop services:
echo   docker-compose -f %COMPOSE_FILE% down
echo.
echo To scale workers (production only):
echo   docker-compose -f %COMPOSE_FILE% up --scale crawler-worker=5 -d
