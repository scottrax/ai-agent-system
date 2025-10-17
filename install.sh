#!/bin/bash

set -e

echo "=========================================="
echo "AI Agent System - Installation Script"
echo "=========================================="
echo

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "⚠️  Please do not run this script as root"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install Python 3.11+ if not available
echo "🐍 Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "⚠️  Python 3.10+ required. Installing Python 3.11..."
    sudo apt install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install -y python3.11 python3.11-venv python3.11-dev
    PYTHON_CMD="python3.11"
else
    echo "✓ Python $PYTHON_VERSION is installed"
    PYTHON_CMD="python3"
fi

# Install pip if not available
echo "📦 Ensuring pip is installed..."
sudo apt install -y python3-pip

# Create virtual environment
echo "🔧 Creating virtual environment..."
$PYTHON_CMD -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Create systemd service file
echo "🔧 Creating systemd service..."
SERVICE_FILE="/etc/systemd/system/ai-agent.service"
INSTALL_DIR="$(pwd)"
USER="$(whoami)"

sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=AI Agent Web Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
Environment="ANTHROPIC_API_KEY="
ExecStart=$INSTALL_DIR/venv/bin/python server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Systemd service created at $SERVICE_FILE"

# Create .env.example file
echo "🔧 Creating .env.example file..."
cat > .env.example <<EOF
# Anthropic API Key (required)
# Get your key from: https://console.anthropic.com/
ANTHROPIC_API_KEY=your-api-key-here

# Server configuration (optional)
HOST=0.0.0.0
PORT=8000
EOF

# Create startup script
echo "🔧 Creating startup scripts..."
cat > start.sh <<'EOF'
#!/bin/bash
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Error: ANTHROPIC_API_KEY not set"
    echo "Please create a .env file with your API key"
    exit 1
fi

source venv/bin/activate
python server.py
EOF

chmod +x start.sh

cat > start-cli.sh <<'EOF'
#!/bin/bash
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Error: ANTHROPIC_API_KEY not set"
    echo "Please create a .env file with your API key"
    exit 1
fi

source venv/bin/activate
python agent.py
EOF

chmod +x start-cli.sh

# Setup firewall if ufw is installed
if command -v ufw &> /dev/null; then
    echo "🔒 Configuring firewall..."
    sudo ufw allow 8000/tcp
    echo "✓ Port 8000 opened in firewall"
fi

echo
echo "=========================================="
echo "✓ Installation Complete!"
echo "=========================================="
echo
echo "Next Steps:"
echo "1. Get your API key from: https://console.anthropic.com/"
echo "2. Create .env file: cp .env.example .env"
echo "3. Edit .env and add your ANTHROPIC_API_KEY"
echo
echo "To start the web server:"
echo "  ./start.sh"
echo
echo "To use CLI mode:"
echo "  ./start-cli.sh"
echo
echo "To run as system service:"
echo "  sudo systemctl edit ai-agent"
echo "  # Add: Environment=\"ANTHROPIC_API_KEY=your-key\""
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl start ai-agent"
echo "  sudo systemctl enable ai-agent"
echo
echo "Access web interface at: http://your-server-ip:8000"
echo "=========================================="
