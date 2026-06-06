@echo off
:: Usage: indexer.bat <output-dir>
:: Example: indexer.bat processed

set OUTPUT_DIR=%1
if "%OUTPUT_DIR%"=="" set OUTPUT_DIR=processed

:: Check for Docker
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not running or not installed.
    echo WARNING: Install Docker Desktop from https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

:: Check processed directory exists
if not exist "%OUTPUT_DIR%\" (
    echo Directory '%OUTPUT_DIR%' not found. Run main.py first to collect posts.
    pause
    exit /b 1
)

:: Check for .jsonl files
dir /b "%OUTPUT_DIR%\*.jsonl" >nul 2>&1
if %errorlevel% neq 0 (
    echo No .jsonl files found in '%OUTPUT_DIR%'. Run main.py first.
    pause
    exit /b 1
)

echo Building Docker image...
docker compose build
if %errorlevel% neq 0 (
    echo Docker build failed. Check your Dockerfile.
    pause
    exit /b 1
)

echo.
echo Starting indexer with data from '%OUTPUT_DIR%'...
echo Index will be saved to bluesky_index\

docker compose run --rm -e DATA_DIR=%OUTPUT_DIR% app python3 pylucene.py

if %errorlevel% equ 0 (
    echo.
    echo Done. Index saved to bluesky_index\
    echo Executing the Web UI for searcher...
    docker compose up
) else (
    echo.
    echo Indexer failed. Check the error above.
    pause
    exit /b 1
)
pause