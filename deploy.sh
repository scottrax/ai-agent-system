#!/bin/bash

# AI Agent System - Master Deployment Script
# This script automates the entire installation process

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=========================================="
echo "AI Agent System - Master Deployment"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Error: Don't run this script as root/sudo${NC}"
    echo "Run it as your normal user: ./deploy.sh"
    exit 1
fi

CURRENT_USER=$(whoami)

echo -e "${BLUE}This script will:${NC}"
echo "1. Install all dependencies"
echo "2. Configure your API keys"
echo "3. Set up passwordless sudo (optional)"
echo "4. Install systemd services for auto-start"
echo "5. Configure firewall"
echo ""
read -p "Continue? (y/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# ======================
# Step 1: Install Dependencies
# ======================
echo ""
echo "=========================================="
echo "Step 1: Installing Dependencies"
echo "=========================================="
echo ""

if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    echo -e "${YELLOW}Virtual environment already exists, skipping...${NC}"
else
    echo "Installing Python and required packages..."
    
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
    
    echo "Creating virtual environment..."
    cd "$SCRIPT_DIR"
    python3 -m venv venv
    
    source venv/bin/activate
    
    echo "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo -e "${GREEN}Dependencies installed successfully!${NC}"
fi

# ======================
# Step 2: Configure API Keys
# ======================
echo ""
echo "=========================================="
echo "Step 2: Configuration"
echo "=========================================="
echo ""

if [ -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${YELLOW}.env file already exists.${NC}"
    read -p "Reconfigure? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping configuration..."
    else
        rm "$SCRIPT_DIR/.env"
    fi
fi

if [ ! -f "$SCRIPT_DIR/.env" ]; then
    if [ ! -f "$SCRIPT_DIR/.env.example" ]; then
        echo -e "${RED}Error: .env.example file not found in $SCRIPT_DIR${NC}"
        echo "Make sure you're running this script from the ai-agent-system directory"
        echo "Current directory: $(pwd)"
        echo "Script directory: $SCRIPT_DIR"
        exit 1
    fi
    
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    
    echo "Enter your Anthropic API key (get it from https://console.anthropic.com/):"
    read -p "API Key (starts with sk-ant-): " api_key
    
    if [ -z "$api_key" ]; then
        echo -e "${RED}Error: API key cannot be empty${NC}"
        exit 1
    fi
    
    # Update .env with API key
    sed -i "s/ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$api_key/" "$SCRIPT_DIR/.env"
    
    echo ""
    echo "Do you want to enable email control? (Send emails to control your server)"
    read -p "Enable email? (y/n): " -n 1 -r
    echo ""
    
    ENABLE_EMAIL=false
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ENABLE_EMAIL=true
        
        echo ""
        echo "Email Configuration:"
        echo "You'll need a Gmail account for the server to monitor."
        echo ""
        
        read -p "Server Gmail address: " email_addr
        read -p "Gmail App Password: " email_pass
        read -p "Your personal email (authorized to send commands): " auth_email
        
        # Update .env
        sed -i "s/EMAIL_ADDRESS=.*/EMAIL_ADDRESS=$email_addr/" "$SCRIPT_DIR/.env"
        sed -i "s/EMAIL_PASSWORD=.*/EMAIL_PASSWORD=$email_pass/" "$SCRIPT_DIR/.env"
        sed -i "s/AUTHORIZED_EMAILS=.*/AUTHORIZED_EMAILS=$auth_email/" "$SCRIPT_DIR/.env"
    fi
    
    echo -e "${GREEN}Configuration saved!${NC}"
fi

# ======================
# Step 3: Passwordless Sudo
# ======================
echo ""
echo "=========================================="
echo "Step 3: Sudo Configuration"
echo "=========================================="
echo ""

echo "The AI agent needs sudo access to install packages and manage services."
echo "This requires passwordless sudo for user: $CURRENT_USER"
echo ""
echo -e "${YELLOW}Warning: This gives the AI full sudo access on this server.${NC}"
echo "Only do this on servers you control."
echo ""
read -p "Configure passwordless sudo? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    SUDOERS_LINE="$CURRENT_USER ALL=(ALL) NOPASSWD: ALL"
    
    # Check if already configured
    if sudo grep -q "^$CURRENT_USER ALL=(ALL) NOPASSWD: ALL" /etc/sudoers.d/$CURRENT_USER 2>/dev/null; then
        echo -e "${GREEN}Passwordless sudo already configured!${NC}"
    else
        echo "$SUDOERS_LINE" | sudo tee /etc/sudoers.d/$CURRENT_USER > /dev/null
        sudo chmod 0440 /etc/sudoers.d/$CURRENT_USER
        echo -e "${GREEN}Passwordless sudo configured!${NC}"
    fi
else
    echo -e "${YELLOW}Skipping sudo configuration.${NC}"
    echo "The AI will ask you to run sudo commands manually."
fi

# ======================
# Step 4: Install Services
# ======================
echo ""
echo "=========================================="
echo "Step 4: Systemd Services"
echo "=========================================="
echo ""

echo "Set up services to auto-start on boot?"
echo "1) Yes - Web interface only"
echo "2) Yes - Web interface + Email"
echo "3) No - I'll run manually"
echo ""
read -p "Choice [1-3]: " service_choice

INSTALL_WEB=false
INSTALL_EMAIL=false

case $service_choice in
    1)
        INSTALL_WEB=true
        ;;
    2)
        INSTALL_WEB=true
        INSTALL_EMAIL=true
        ;;
    3)
        echo "Skipping service installation."
        ;;
    *)
        echo -e "${YELLOW}Invalid choice, skipping services.${NC}"
        ;;
esac

if [ "$INSTALL_WEB" = true ] || [ "$INSTALL_EMAIL" = true ]; then
    
    # Install web service
    if [ "$INSTALL_WEB" = true ]; then
        echo ""
        echo "Installing web service..."
        
        cat > /tmp/ai-agent-web.service << EOF
[Unit]
Description=AI Agent Web Interface
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$SCRIPT_DIR
Environment="PATH=$SCRIPT_DIR/venv/bin"
EnvironmentFile=$SCRIPT_DIR/.env
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        sudo mv /tmp/ai-agent-web.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable ai-agent-web
        sudo systemctl start ai-agent-web
        
        if systemctl is-active --quiet ai-agent-web; then
            echo -e "${GREEN}Web service started successfully!${NC}"
        else
            echo -e "${RED}Web service failed to start. Check logs: sudo journalctl -u ai-agent-web -n 50${NC}"
        fi
    fi
    
    # Install email service
    if [ "$INSTALL_EMAIL" = true ]; then
        echo ""
        echo "Installing email service..."
        
        cat > /tmp/ai-agent-email.service << EOF
[Unit]
Description=AI Agent Email Interface
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$SCRIPT_DIR
Environment="PATH=$SCRIPT_DIR/venv/bin"
EnvironmentFile=$SCRIPT_DIR/.env
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/email_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        sudo mv /tmp/ai-agent-email.service /etc/systemd/system/
        sudo systemctl daemon-reload
        sudo systemctl enable ai-agent-email
        sudo systemctl start ai-agent-email
        
        if systemctl is-active --quiet ai-agent-email; then
            echo -e "${GREEN}Email service started successfully!${NC}"
        else
            echo -e "${RED}Email service failed to start. Check logs: sudo journalctl -u ai-agent-email -n 50${NC}"
        fi
    fi
fi

# ======================
# Step 5: Firewall
# ======================
echo ""
echo "=========================================="
echo "Step 5: Firewall Configuration"
echo "=========================================="
echo ""

if command -v ufw &> /dev/null; then
    echo "Opening port 8000 for web interface..."
    sudo ufw allow 8000/tcp
    
    if ! sudo ufw status | grep -q "Status: active"; then
        read -p "Enable firewall? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo ufw enable
            echo -e "${GREEN}Firewall enabled!${NC}"
        fi
    else
        echo -e "${GREEN}Firewall already active!${NC}"
    fi
else
    echo -e "${YELLOW}ufw not installed, skipping firewall configuration.${NC}"
fi

# ======================
# Done!
# ======================
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

echo -e "${GREEN}Your AI Agent is ready!${NC}"
echo ""

if [ "$INSTALL_WEB" = true ]; then
    echo "Web Interface: http://$SERVER_IP:8000"
    echo "  Status: sudo systemctl status ai-agent-web"
    echo "  Logs:   sudo journalctl -u ai-agent-web -f"
    echo ""
fi

if [ "$INSTALL_EMAIL" = true ]; then
    echo "Email Interface: Active"
    echo "  Send emails from authorized addresses to control your server"
    echo "  Status: sudo systemctl status ai-agent-email"
    echo "  Logs:   sudo journalctl -u ai-agent-email -f"
    echo ""
fi

if [ "$service_choice" = "3" ]; then
    echo "To start manually:"
    echo "  cd $SCRIPT_DIR"
    echo "  ./start.sh           # Web interface"
    echo "  ./start-email.sh     # Email interface"
    echo ""
fi

echo "All conversation logs are saved to: ~/ai-agent-logs/"
echo ""
echo "Useful commands:"
echo "  sudo systemctl restart ai-agent-web    # Restart web service"
echo "  sudo systemctl stop ai-agent-web       # Stop web service"
echo "  tail -f ~/ai-agent-logs/web_*.log      # View conversation logs"
echo ""
echo "Documentation:"
echo "  README.md           # Main documentation"
echo "  LOGS.md             # Logging information"
echo "  SUDO-SETUP.md       # Sudo configuration details"
echo "  EMAIL-SETUP.md      # Email setup details"
echo ""
echo "Or just ask the ai to do any of this for you :)"
echo ""
echo "=========================================="
