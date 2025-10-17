#!/bin/bash

# Remove systemd services for AI Agent

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "AI Agent - Remove Services"
echo "=========================================="
echo ""

# List of services to remove
services=("ai-agent-web" "ai-agent-email")

echo "This will remove all AI Agent services:"
for service in "${services[@]}"; do
    if systemctl is-enabled --quiet "$service.service" 2>/dev/null; then
        echo -e "  • ${YELLOW}${service}${NC} (currently enabled)"
    elif systemctl list-unit-files | grep -q "$service.service"; then
        echo "  • ${service} (installed but not enabled)"
    fi
done
echo ""

read -p "Are you sure you want to remove these services? [y/N]: " confirm

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 0
fi

echo ""

for service in "${services[@]}"; do
    service_file="/etc/systemd/system/${service}.service"
    
    if [ -f "$service_file" ]; then
        echo -e "${YELLOW}Removing ${service}...${NC}"
        
        # Stop service
        if systemctl is-active --quiet "$service.service"; then
            echo "  Stopping..."
            sudo systemctl stop "$service.service"
        fi
        
        # Disable service
        if systemctl is-enabled --quiet "$service.service" 2>/dev/null; then
            echo "  Disabling..."
            sudo systemctl disable "$service.service"
        fi
        
        # Remove service file
        echo "  Removing service file..."
        sudo rm -f "$service_file"
        
        echo -e "${GREEN}✓ ${service} removed${NC}"
    else
        echo -e "${YELLOW}${service} not found, skipping${NC}"
    fi
    echo ""
done

# Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "=========================================="
echo -e "${GREEN}All services removed!${NC}"
echo "=========================================="
echo ""
echo "The AI Agent code is still in place."
echo "You can still run manually with:"
echo "  ./start.sh"
echo "  ./start-sms.sh"
echo "  ./start-sms-free.sh"
echo ""
