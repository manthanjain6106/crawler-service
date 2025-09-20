@echo off
REM Start script for the crawler microservice (Windows)

setlocal enabledelayedexpansion

REM Default values
set MODE=api
set LOG_LEVEL=INFO
set CONFIG_FILE=

REM Parse command line arguments
:parse_args
if "%~1"=="" goto start_service
if "%~1"=="--mode" (
    set MODE=%~2
    shift
    shift
    goto parse_args
)
if "%~1"=="--log-level" (
    set LOG_LEVEL=%~2
    shift
    shift
    goto parse_args
)
if "%~1"=="--config" (
    set CONFIG_FILE=%~2
    shift
    shift
    goto parse_args
)
if "%~1"=="--help" (
    echo Usage: %0 [--mode api^|worker] [--log-level LEVEL] [--config FILE]
    echo.
    echo Options:
    echo   --mode        Mode to run: 'api' for API server, 'worker' for background jobs
    echo   --log-level   Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    echo   --config      Path to configuration file
    echo   --help        Show this help message
    exit /b 0
)
echo Unknown option: %~1
exit /b 1

:start_service
REM Set environment variables
set LOG_LEVEL=%LOG_LEVEL%

REM Load configuration file if specified
if defined CONFIG_FILE (
    if exist "%CONFIG_FILE%" (
        echo Loading configuration from %CONFIG_FILE%
        for /f "usebackq tokens=1,2 delims==" %%a in ("%CONFIG_FILE%") do (
            if not "%%a"=="" if not "%%a:~0,1%"=="#" (
                set %%a=%%b
            )
        )
    ) else (
        echo Configuration file %CONFIG_FILE% not found
        exit /b 1
    )
)

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Start the service
echo Starting crawler microservice in %MODE% mode...
python start.py --mode %MODE% --log-level %LOG_LEVEL%
