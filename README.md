# AI Agent System for Ubuntu Server

A complete AI-powered computer agent that lets you control your Ubuntu server through natural language. Talk to your server instead of typing commands!

## Quick Deployment (Recommended)

Deploy everything in one command:

```bash
./deploy.sh
```

The interactive script handles installation, configuration, and setup automatically. See DEPLOY.md for details.

## Features

- Natural language interface to your Linux server
- Web-based chat interface
- Email interface (send emails to control your server!)
- Command-line interface option
- Execute bash commands, read/write files, search files
- Secure by default (email whitelist authentication)
- Easy deployment with systemd service
- Conversation history maintained
- **Comprehensive logging** - All interactions logged with timestamps

## Logging

The AI agent automatically logs everything to `~/ai-agent-logs/`:

- User messages and AI responses
- All tool executions (commands run, files accessed)
- Timestamps for every action
- Separate log files for each session

**View logs:**
```bash
# See all logs
ls ~/ai-agent-logs/

# View latest log
tail -f ~/ai-agent-logs/$(ls -t ~/ai-agent-logs/ | head -1)
```

See `LOGS.md` for complete logging documentation, including log format, rotation, and management.

## Documentation

- **[DEPLOY.md](DEPLOY.md)** - One-command deployment with interactive setup
- **[EMAIL-SETUP.md](EMAIL-SETUP.md)** - Email control configuration and setup
- **[LOGS.md](LOGS.md)** - Complete logging documentation and management
- **[SYSTEMD-SETUP.md](SYSTEMD-SETUP.md)** - System service configuration and management
- **[CHAT-HISTORY-FEATURE.md](CHAT-HISTORY-FEATURE.md)** - Chat history and sidebar functionality

## Quick Start

### 1. Upload to Your Ubuntu Server

```bash
# Copy the entire ai-agent-system directory to your Ubuntu server
scp -r ai-agent-system user@your-server-ip:~/
```

### 2. SSH into Your Server

```bash
ssh user@your-server-ip
cd ~/ai-agent-system
```

### 3. Run Installation Script

```bash
chmod +x install.sh
./install.sh
```

The installer will:
- Update system packages
- Install Python 3.10+ if needed
- Create virtual environment
- Install all dependencies
- Create systemd service
- Configure firewall

### 4. Get Your API Key

Visit [https://console.anthropic.com/](https://console.anthropic.com/) and:
1. Sign up or log in
2. Go to API Keys section
3. Create a new API key
4. Copy the key

### 5. Configure API Key

```bash
# Create environment file
cp .env.example .env

# Edit the file and add your API key
nano .env
```

Add your key:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
HOST=0.0.0.0
PORT=8000
```

### 6. Start the Agent

**Option A: Web Server Mode (Recommended)**
```bash
./start.sh
```

Access at: `http://your-server-ip:8000`

**Option B: CLI Mode**
```bash
./start-cli.sh
```

**Option C: System Service (Auto-start on boot)**
```bash
# Edit service to add API key
sudo systemctl edit ai-agent

# Add these lines:
# [Service]
# Environment="ANTHROPIC_API_KEY=sk-ant-your-key-here"

# Start and enable service
sudo systemctl daemon-reload
sudo systemctl start ai-agent
sudo systemctl enable ai-agent

# Check status
sudo systemctl status ai-agent

# View logs
sudo journalctl -u ai-agent -f
```

## Running as a System Service

To make your AI agent start automatically on boot and restart on failure:

```bash
cd ~/ai-agent-system
./setup-services.sh
```

This will:
- Create systemd service files
- Enable auto-start on boot
- Configure auto-restart on failure (10 second delay)
- Start the services immediately

See `SYSTEMD-SETUP.md` for details and management commands.

**Useful commands after setup:**
```bash
# Check status
sudo systemctl status ai-agent-web

# View logs
sudo journalctl -u ai-agent-web -f

# Restart
sudo systemctl restart ai-agent-web
```

## Usage Examples

Once running, you can ask your AI agent things like:

- "What's the current CPU and memory usage?"
- "List all files in /var/log"
- "Install nginx and start it"
- "Create a backup of my home directory"
- "Show me the last 20 lines of syslog"
- "Update all system packages"
- "Create a Python script that monitors disk space"
- "Find all files larger than 100MB"

## Architecture

```
┌─────────────────┐
│   Web Browser   │
│   (User)        │
└────────┬────────┘
         │ HTTP/WebSocket
         ↓
┌─────────────────┐
│  FastAPI Server │
│  (server.py)    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐      ┌──────────────┐
│   AI Agent      │ ←──→ │ Claude API   │
│   (agent.py)    │      │ (Anthropic)  │
└────────┬────────┘      └──────────────┘
         │
         ↓
┌─────────────────┐
│  Linux System   │
│  (bash, files)  │
└─────────────────┘
```

## Files Overview

- `agent.py` - Core AI agent with tool execution
- `server.py` - FastAPI web server with WebSocket support
- `index.html` - Web interface
- `requirements.txt` - Python dependencies
- `install.sh` - Automated installation script
- `start.sh` - Quick start for web server
- `start-cli.sh` - Quick start for CLI mode

## Security Considerations

**Important Security Notes:**

1. **API Key Protection**: Never commit your `.env` file to version control
2. **Network Access**: The agent has full access to your server. Only expose to trusted networks.
3. **Firewall**: Use firewall rules to restrict access to port 8000
4. **HTTPS**: For production, put behind nginx with SSL/TLS
5. **Authentication**: Consider adding authentication for multi-user environments

### Adding Basic Authentication

To add password protection, modify `server.py`:

```python
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from secrets import compare_digest

security = HTTPBasic()

@app.get("/")
async def get(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = compare_digest(credentials.username, "admin")
    correct_password = compare_digest(credentials.password, "your-password")
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401)
    # ... rest of code
```

### Setting Up HTTPS with Nginx

```bash
# Install nginx
sudo apt install nginx certbot python3-certbot-nginx

# Create nginx config
sudo nano /etc/nginx/sites-available/ai-agent

# Add configuration:
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/ai-agent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

## Troubleshooting

### Port Already in Use
```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill the process or change PORT in .env
```

### Permission Errors
```bash
# Make sure scripts are executable
chmod +x install.sh start.sh start-cli.sh
```

### API Key Invalid
- Check your key has no extra spaces
- Verify key is active at console.anthropic.com
- Make sure .env file is in the correct directory

### Service Won't Start
```bash
# Check logs
sudo journalctl -u ai-agent -n 50

# Verify service file
sudo systemctl cat ai-agent

# Test manually
./start.sh
```

### WebSocket Connection Failed
- Check firewall allows port 8000
- Verify server is running: `curl http://localhost:8000/health`
- Check browser console for errors

## Cost Estimates

Using Claude API (Sonnet 3.5):
- Input: ~$3 per million tokens
- Output: ~$15 per million tokens

Typical usage:
- Simple command: ~$0.001-0.005
- Complex task: ~$0.01-0.05
- Monthly (moderate use): $5-30

## Extending the Agent

### Adding New Tools

Edit `agent.py` and add to `self.tools`:

```python
{
    "name": "your_tool",
    "description": "What it does",
    "input_schema": {
        "type": "object",
        "properties": {
            "param": {"type": "string", "description": "Parameter description"}
        },
        "required": ["param"]
    }
}
```

Then add the execution logic in `execute_tool()`.

### Example: Add Docker Management

```python
# In tools list:
{
    "name": "docker_ps",
    "description": "List running Docker containers",
    "input_schema": {"type": "object", "properties": {}}
}

# In execute_tool():
elif tool_name == "docker_ps":
    result = subprocess.run("docker ps", shell=True, capture_output=True, text=True)
    return {"containers": result.stdout}
```

## Alternative: Using Local LLM (Free)

Instead of Claude API, use Ollama for free local inference:

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.1:70b

# Modify agent.py to use Ollama instead of Anthropic
# (Contact for detailed instructions)
```

**Requirements for local LLM:**
- 8B model: 16GB RAM
- 70B model: 64GB RAM or GPU with 48GB VRAM

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs: `sudo journalctl -u ai-agent -f`
3. Test with `./start-cli.sh` for direct feedback

## License

MIT License - Use freely for personal or commercial projects.

## Credits

Built with:
- [Anthropic Claude](https://www.anthropic.com/) - AI model
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Uvicorn](https://www.uvicorn.org/) - ASGI server
