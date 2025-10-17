#!/bin/bash

# Setup systemd services for AI Agent
# This script creates systemd service files and enables them

set -e

# Get the current user and home directory
CURRENT_USER=$(whoami)
CURRENT_HOME=$(eval echo ~$CURRENT_USER)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "AI Agent - Systemd Services Setup"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}❌ Don't run this script as root/sudo${NC}"
    echo "Run it as your normal user: ./setup-services.sh"
    exit 1
fi

# Check if .env exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Create .env first (copy from .env.example)"
    exit 1
fi

# Check if venv exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo -e "${RED}❌ Error: Virtual environment not found${NC}"
    echo "Run ./install.sh first"
    exit 1
fi

# Load .env to check what's configured
source "$SCRIPT_DIR/.env"

echo "Current configuration:"
echo "  User: $CURRENT_USER"
echo "  Install directory: $SCRIPT_DIR"
echo ""

# Function to create service file
create_service() {
    local service_name=$1
    local description=$2
    local exec_command=$3
    local service_file="/etc/systemd/system/${service_name}.service"
    
    echo -e "${YELLOW}Creating service: ${service_name}${NC}"
    
    # Create service file content
    local service_content="[Unit]
Description=${description}
After=network.target

[Service]
Type=simple
User=${CURRENT_USER}
WorkingDirectory=${SCRIPT_DIR}
Environment=\"PATH=${SCRIPT_DIR}/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\"
EnvironmentFile=${SCRIPT_DIR}/.env
ExecStart=${SCRIPT_DIR}/venv/bin/python ${exec_command}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"
    
    # Write service file
    echo "$service_content" | sudo tee "$service_file" > /dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Service file created: ${service_file}${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to create service file${NC}"
        return 1
    fi
}

# Function to enable and start service
enable_service() {
    local service_name=$1
    
    echo -e "${YELLOW}Enabling ${service_name}...${NC}"
    
    sudo systemctl daemon-reload
    sudo systemctl enable "${service_name}.service"
    
    echo -e "${YELLOW}Starting ${service_name}...${NC}"
    sudo systemctl start "${service_name}.service"
    
    # Wait a moment for service to start
    sleep 2
    
    # Check status
    if sudo systemctl is-active --quiet "${service_name}.service"; then
        echo -e "${GREEN}✓ ${service_name} is running${NC}"
        return 0
    else
        echo -e "${RED}✗ ${service_name} failed to start${NC}"
        echo "Check logs with: sudo journalctl -u ${service_name} -n 50"
        return 1
    fi
}

# Ask which services to install
echo "Which services would you like to install?"
echo "1) Web interface only"
echo "2) Web + SMS (Twilio)"
echo "3) Web + Email"
echo "4) All services (Web + SMS + Email)"
read -p "Enter choice [1-4]: " choice

INSTALL_WEB=false
INSTALL_SMS_TWILIO=false
INSTALL_EMAIL=false

case $choice in
    1)
        INSTALL_WEB=true
        ;;
    2)
        INSTALL_WEB=true
        INSTALL_SMS_TWILIO=true
        ;;
    3)
        INSTALL_WEB=true
        INSTALL_EMAIL=true
        ;;
    4)
        INSTALL_WEB=true
        INSTALL_SMS_TWILIO=true
        INSTALL_EMAIL=true
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Installing services..."
echo "=========================================="
echo ""

# Install Web Interface
if [ "$INSTALL_WEB" = true ]; then
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo -e "${RED}✗ ANTHROPIC_API_KEY not set in .env${NC}"
        exit 1
    fi
    
    create_service "ai-agent-web" \
        "AI Agent Web Interface" \
        "server.py"
    
    enable_service "ai-agent-web"
    echo ""
fi

# Install Email Agent
if [ "$INSTALL_EMAIL" = true ]; then
    if [ -z "$EMAIL_ADDRESS" ] || [ -z "$EMAIL_PASSWORD" ] || [ -z "$AUTHORIZED_EMAILS" ]; then
        echo -e "${YELLOW}⚠ Warning: Email credentials not found in .env${NC}"
        echo "Skipping Email service"
    else
        create_service "ai-agent-email" \
            "AI Agent Email Interface" \
            "email_server.py"
        
        enable_service "ai-agent-email"
        echo ""
    fi
fi

echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Your services are now:"
echo "  • Running"
echo "  • Will auto-start on boot"
echo "  • Will auto-restart on failure"
echo ""
echo "Useful commands:"
echo ""
echo "  # Check status"
if [ "$INSTALL_WEB" = true ]; then
    echo "  sudo systemctl status ai-agent-web"
fi
if [ "$INSTALL_EMAIL" = true ]; then
    echo "  sudo systemctl status ai-agent-email"
fi
echo ""
echo "  # View logs"
if [ "$INSTALL_WEB" = true ]; then
    echo "  sudo journalctl -u ai-agent-web -f"
fi
if [ "$INSTALL_EMAIL" = true ]; then
    echo "  sudo journalctl -u ai-agent-email -f"
fi
echo ""
echo "  # Restart a service"
if [ "$INSTALL_WEB" = true ]; then
    echo "  sudo systemctl restart ai-agent-web"
fi
if [ "$INSTALL_EMAIL" = true ]; then
    echo "  sudo systemctl restart ai-agent-email"
fi
echo ""
echo "  # Stop a service"
if [ "$INSTALL_WEB" = true ]; then
    echo "  sudo systemctl stop ai-agent-web"
fi
if [ "$INSTALL_EMAIL" = true ]; then
    echo "  sudo systemctl stop ai-agent-email"
fi
echo ""
echo "  # Disable auto-start"
if [ "$INSTALL_WEB" = true ]; then
    echo "  sudo systemctl disable ai-agent-web"
fi
if [ "$INSTALL_EMAIL" = true ]; then
    echo "  sudo systemctl disable ai-agent-email"
fi
echo ""

if [ "$INSTALL_WEB" = true ]; then
    echo "Web interface: http://$(hostname -I | awk '{print $1}'):8000"
fi

echo ""
echo "=========================================="
