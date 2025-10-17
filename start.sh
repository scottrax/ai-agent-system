#!/bin/bash

set -e

cd "$(dirname "$0")"

# Load environment variables (skip comments and empty lines)
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
else
    echo "❌ Error: .env file not found"
    echo "Copy .env.example to .env and configure it"
    exit 1
fi

# Check ANTHROPIC_API_KEY
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ Error: ANTHROPIC_API_KEY not set in .env"
    exit 1
fi

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Error: Virtual environment not found"
    echo "Run ./install.sh first"
    exit 1
fi

PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

echo "=========================================="
echo "AI Agent - Web Interface"
echo "=========================================="
echo ""
echo "Starting server on $HOST:$PORT"
echo ""
echo "Access the web interface at:"
echo "  http://localhost:$PORT"
echo "  http://$(hostname -I | awk '{print $1}'):$PORT"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

python server.py
