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

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Error: Virtual environment not found"
    echo "Run ./install.sh first"
    exit 1
fi

# Check required variables
missing=()
[ -z "$EMAIL_ADDRESS" ] && missing+=("EMAIL_ADDRESS")
[ -z "$EMAIL_PASSWORD" ] && missing+=("EMAIL_PASSWORD")
[ -z "$AUTHORIZED_EMAILS" ] && missing+=("AUTHORIZED_EMAILS")
[ -z "$ANTHROPIC_API_KEY" ] && missing+=("ANTHROPIC_API_KEY")

if [ ${#missing[@]} -gt 0 ]; then
    echo "❌ Error: Missing required environment variables:"
    printf '  %s\n' "${missing[@]}"
    echo ""
    echo "See EMAIL-SETUP.md for configuration instructions"
    exit 1
fi

echo "=========================================="
echo "AI Agent - Email Interface"
echo "=========================================="
echo ""
echo "Monitoring inbox: $EMAIL_ADDRESS"
echo "Authorized emails: $AUTHORIZED_EMAILS"
echo ""
echo "Send emails from authorized addresses to interact with the AI"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

python email_server.py
