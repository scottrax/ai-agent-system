# Quick Deployment Guide

Deploy the AI Agent on a fresh Ubuntu server in 5 minutes.

## One-Command Deployment

```bash
./deploy.sh
```

That's it! The script will:
1. Install all dependencies
2. Ask for your API keys
3. Configure sudo (optional)
4. Set up auto-start services
5. Configure firewall
6. Start everything

## What You'll Need

- Anthropic API key (from https://console.anthropic.com/)
- Optional: Gmail account + app password for email control

## Interactive Prompts

The script will ask you:

### 1. Anthropic API Key
```
Enter your Anthropic API key: sk-ant-...
```

Get this from: https://console.anthropic.com/

### 2. Email Control (Optional)
```
Enable email? (y/n):
```

If yes:
- Server Gmail address
- Gmail app password
- Your personal email (authorized to send commands)

### 3. Passwordless Sudo
```
Configure passwordless sudo? (y/n):
```

Required for AI to install packages. Safe for personal servers.

### 4. Services
```
1) Yes - Web interface only
2) Yes - Web interface + Email
3) No - I'll run manually
```

Choose based on how you want to access the AI.

### 5. Firewall
```
Enable firewall? (y/n):
```

Opens port 8000 for web access.

## After Installation

Access your AI:
```
http://your-server-ip:8000
```

Check status:
```bash
sudo systemctl status ai-agent-web
```

View logs:
```bash
sudo journalctl -u ai-agent-web -f
```

## Manual Installation

If you prefer manual control, see README.md for step-by-step instructions.

## Troubleshooting

**Problem: Service won't start**
```bash
sudo journalctl -u ai-agent-web -n 50
```

**Problem: Can't access web interface**
```bash
sudo ufw allow 8000/tcp
sudo systemctl restart ai-agent-web
```

**Problem: AI can't run sudo commands**
```bash
sudo visudo
# Add: username ALL=(ALL) NOPASSWD: ALL
```

## Uninstall

```bash
./remove-services.sh
rm -rf ~/ai-agent-system
rm -rf ~/ai-agent-logs
```

## Support

See documentation:
- README.md - Complete guide
- LOGS.md - Logging details
- SUDO-SETUP.md - Sudo configuration
- EMAIL-SETUP.md - Email setup
