#!/bin/bash

# Start script for the crawler microservice

set -e

# Default values
MODE="api"
LOG_LEVEL="INFO"
CONFIG_FILE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--mode api|worker] [--log-level LEVEL] [--config FILE]"
            echo ""
            echo "Options:"
            echo "  --mode        Mode to run: 'api' for API server, 'worker' for background jobs"
            echo "  --log-level   Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
            echo "  --config      Path to configuration file"
            echo "  --help        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set environment variables
export LOG_LEVEL="$LOG_LEVEL"

# Load configuration file if specified
if [ -n "$CONFIG_FILE" ]; then
    if [ -f "$CONFIG_FILE" ]; then
        echo "Loading configuration from $CONFIG_FILE"
        export $(cat "$CONFIG_FILE" | grep -v '^#' | xargs)
    else
        echo "Configuration file $CONFIG_FILE not found"
        exit 1
    fi
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Start the service
echo "Starting crawler microservice in $MODE mode..."
python start.py --mode "$MODE" --log-level "$LOG_LEVEL"
