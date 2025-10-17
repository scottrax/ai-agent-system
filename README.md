# AI Agent System for Ubuntu Server

A complete AI-powered computer agent that lets you control your Ubuntu server through natural language. Talk to your server instead of typing commands!

## Features

- Natural language interface to your Linux server
- Web-based chat interface
- Email interface (control via email from your phone)
- Command-line interface option
- Execute bash commands, read/write files, search files
- Secure by default (authentication required)
- Easy deployment with systemd service
- Conversation history maintained
- Comprehensive logging of all interactions

---

## Table of Contents

1. [Quick Deployment](#quick-deployment)
2. [Manual Installation](#manual-installation)
3. [Configuration](#configuration)
4. [Email Agent Setup](#email-agent-setup)
5. [Logging](#logging)
6. [Sudo Configuration](#sudo-configuration)
7. [Service Management](#service-management)
8. [Usage](#usage)
9. [Troubleshooting](#troubleshooting)
10. [Security](#security)
11. [Files Overview](#files-overview)

---

## Quick Deployment

Deploy everything in one command on a fresh Ubuntu server:

Place all files into a folder named "ai-agent-system"

```bash
cd ~/ai-agent-system
./deploy.sh
```

This automated script will:
1. Install all dependencies (Python, packages, virtual environment)
2. Ask for your Anthropic API key
3. Configure email settings (optional)
4. Set up passwordless sudo (optional)
5. Install systemd services for auto-start
6. Configure firewall
7. Start everything

Done in 5 minutes!

---

## Manual Installation

If you prefer to install manually:

### Step 1: Upload Files

```bash
# From your computer
scp ai-agent-system.tar.gz user@server:~/

# On server
tar -xzf ai-agent-system.tar.gz
cd ai-agent-system
```

### Step 2: Run Installer

```bash
./install.sh
```

Installs Python dependencies and creates virtual environment.

### Step 3: Configure

```bash
cp .env.example .env
nano .env
```

Add your Anthropic API key and other settings (see [Configuration](#configuration) below).

### Step 4: Test

```bash
./start.sh
```

Access at `http://your-server-ip:8000`

### Step 5: Set Up Auto-Start (Optional)

```bash
./setup-services.sh
```

Choose which services to install (web, email, or both).

---

## Configuration

### Environment Variables (.env file)

All configuration is done in the `.env` file.

#### Required Settings

```bash
# Your Anthropic API key (required)
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Get your key from: https://console.anthropic.com/

#### AI Model Selection

```bash
# Change the AI model (optional, defaults to claude-sonnet-4-5)
AI_MODEL=claude-sonnet-4-5
```

**Available models:**
- `claude-sonnet-4-5` - Latest Claude Sonnet (recommended, best quality)
- `claude-sonnet-3-5` - Claude 3.5 Sonnet (stable)
- `claude-haiku-4-5` - Claude 4 Haiku (fastest, cheapest)

**To change the model:**
1. Edit `.env` file: `nano .env`
2. Change or add: `AI_MODEL=claude-haiku-4-5`
3. Restart: `sudo systemctl restart ai-agent-web`

#### Server Settings

```bash
# Host and port for web interface (optional)
HOST=0.0.0.0  # Listen on all interfaces
PORT=8000     # Web interface port
```

#### Email Agent Settings

```bash
# Email configuration for email-based control (optional)
EMAIL_ADDRESS=your-server-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
AUTHORIZED_EMAILS=your.personal@gmail.com,another@work.com
```

### System Prompt Customization

The AI's behavior is controlled by `system-prompt.txt`.

#### View Current Prompt

```bash
cat ~/ai-agent-system/system-prompt.txt
```

#### Edit System Prompt

```bash
cd ~/ai-agent-system
nano system-prompt.txt
```

#### Apply Changes

After editing `system-prompt.txt`:

```bash
sudo systemctl restart ai-agent-web
```

The new prompt takes effect immediately.

### Configuration Tips

**Cost Optimization** - Use cheaper models:
```bash
AI_MODEL=claude-haiku-4-5
```

**Test Configuration:**
```bash
cd ~/ai-agent-system
source venv/bin/activate
python agent.py  # CLI mode to test
```

---

## Email Agent Setup

Control your server by sending emails from your phone or computer:

```bash
# 1. Configure .env
nano ~/ai-agent-system/.env

# Add:
EMAIL_ADDRESS=myserver2025@gmail.com
EMAIL_PASSWORD=your-16-char-app-password
AUTHORIZED_EMAILS=your.real.email@gmail.com
ANTHROPIC_API_KEY=sk-ant-your-key

# 2. Start
cd ~/ai-agent-system
source venv/bin/activate
python email_server.py

# 3. Send test email to myserver2025@gmail.com from your.real.email@gmail.com
# Wait 15-30 seconds for reply
```
### Highly recommended to create a dedicated email address for your server!

### How It Works

1. **You send email** to `server-email@gmail.com` from your authorized address
2. **Server monitors inbox** every 15 seconds
3. **AI processes your request** and executes commands
4. **You get email back** with the results

### Security

- Only emails from addresses in `AUTHORIZED_EMAILS` are processed
- Unauthorized emails are ignored and marked as read
- Each conversation is isolated per sender

### Detailed Setup

#### 1. Create Gmail Account for Your Server

Go to https://gmail.com and create: `myserver2025@gmail.com`

#### 2. Enable 2-Factor Authentication

1. Go to: https://myaccount.google.com/security
2. Enable **2-Step Verification**
3. Complete setup

#### 3. Create App Password

1. Go to: https://myaccount.google.com/apppasswords
2. App name: "AI Agent Server"
3. Click **Create**
4. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

#### 4. Configure .env

```bash
cd ~/ai-agent-system
nano .env
```

Add:
```bash
EMAIL_ADDRESS=myserver2025@gmail.com
EMAIL_PASSWORD=abcdefghijklmnop  # No spaces
AUTHORIZED_EMAILS=your.personal@gmail.com
```

Multiple authorized emails:
```bash
AUTHORIZED_EMAILS=alice@gmail.com,bob@work.com,charlie@company.com
```

#### 5. Start Email Server

```bash
cd ~/ai-agent-system
source venv/bin/activate
python email_server.py
```

You should see:
```
Starting email AI server...
Monitoring inbox: myserver2025@gmail.com
Will respond to emails from: your.personal@gmail.com
AI Agent ready
```

#### 6. Send Test Email

From your phone or computer, send email to `myserver2025@gmail.com`:

```
Subject: Test
Body: what's the date
```

Wait 15-30 seconds. You'll get an email reply with the date!

#### 7. Make It Permanent

```bash
./setup-services.sh
# Choose option 3: Web + Email
```

Now it runs forever, starts on boot, restarts on failure.

### Email Examples

```
Subject: System Check
Body: what's the disk usage?

Subject: File Management
Body: list files in my home directory

Subject: Update Server
Body: update the system packages

Subject: Create File
Body: create a file called notes.txt with "Hello World"
```

### Troubleshooting Email

**Not receiving replies:**
- Check spam folder
- Verify `EMAIL_ADDRESS` is correct in .env
- Check logs: `tail -f ~/ai-agent-logs/email_*.log`
- Check server is running: `sudo systemctl status ai-agent-email`

**"Login failed" error:**
- Verify app password is correct (no spaces)
- Make sure 2FA is enabled on Gmail
- Try regenerating app password

**Slow responses:**
- Normal delay is 15-30 seconds (inbox polling interval)
- Check AI model - haiku is faster than sonnet/opus

---

## Logging

The AI agent automatically logs all interactions with timestamps.

### Log Location

All logs are saved to: `~/ai-agent-logs/`

```bash
cd ~/ai-agent-logs
ls -la
```

### Log Files

- **`web_<session_id>.log`** - Web interface conversations
- **`email_<timestamp>.log`** - Email agent conversations
- **`conversation_<timestamp>.log`** - CLI conversations

### Log Format

```
=== AI Agent Conversation Log Started at 2025-10-17 14:30:52 ===

[2025-10-17 14:31:05] USER: what's the disk usage?

[2025-10-17 14:31:06] TOOL: run_bash
  Input: {"command": "df -h"}
  Result: {"stdout": "...", "stderr": "", "exit_code": 0}

[2025-10-17 14:31:07] AGENT: Here's your disk usage:
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   12G   36G  25% /
```

### View Logs

```bash
# View latest web log
tail -f ~/ai-agent-logs/web_*.log

# View latest email log
tail -f ~/ai-agent-logs/email_*.log

# View all logs from today
ls -lt ~/ai-agent-logs/ | head -20

# Search logs
grep "USER:" ~/ai-agent-logs/*.log
grep "error" ~/ai-agent-logs/*.log -i
```

### Log Rotation

Logs grow over time. Clean them periodically:

```bash
# View total size
du -sh ~/ai-agent-logs/

# Delete logs older than 30 days
find ~/ai-agent-logs/ -name "*.log" -mtime +30 -delete

# Keep only last 100 logs
cd ~/ai-agent-logs
ls -t *.log | tail -n +101 | xargs rm -f
```

### Automated Log Cleanup

Add to crontab:

```bash
crontab -e
```

Add:
```
# Clean logs older than 30 days, every day at 3am
0 3 * * * find ~/ai-agent-logs/ -name "*.log" -mtime +30 -delete
```

### Privacy & Security

- Logs contain all commands and outputs
- Store securely - they may contain sensitive information
- Include logs in your backup strategy
- Consider encrypting log directory for sensitive environments

---

## Sudo Configuration

For the AI to install packages and manage services, it needs sudo access.

### Set Up Passwordless Sudo

```bash
sudo visudo
```

Add at the very end (replace `username` with your actual username):

```
username ALL=(ALL) NOPASSWD: ALL
```

Save and exit (Ctrl+X, Y, Enter).

**Test it:**
```bash
sudo apt update
```

Should run without asking for password.

### Security Considerations

**Development/Personal Server:**
- Passwordless sudo is convenient and generally safe
- AI can manage system without interruption

**Production Server:**
- Consider limiting sudo to specific commands
- Use sudo rules for fine-grained control
- Monitor logs carefully

### Restricted Sudo (Production)

Instead of full sudo access, limit to specific commands:

```bash
sudo visudo
```

Add:
```
username ALL=(ALL) NOPASSWD: /usr/bin/apt, /usr/bin/systemctl, /usr/bin/docker
```

This allows only apt, systemctl, and docker commands without password.

### Remove Passwordless Sudo

```bash
sudo visudo
```

Remove or comment out the NOPASSWD line, save and exit.

### Alternative: Manual Execution

If you don't configure passwordless sudo, the AI will:
1. Tell you it needs sudo
2. Show you the exact command to run
3. Ask you to run it manually

Example:
```
AI: "This requires sudo. Please run this command manually:
sudo apt update && sudo apt upgrade -y"
```

---

## Service Management

If you set up systemd services (via `./deploy.sh` or `./setup-services.sh`):

### Check Status

```bash
sudo systemctl status ai-agent-web
sudo systemctl status ai-agent-email
```

### Start/Stop

```bash
sudo systemctl start ai-agent-web
sudo systemctl stop ai-agent-web
```

### Restart After Config Changes

```bash
sudo systemctl restart ai-agent-web
```

### Enable/Disable Auto-Start on Boot

```bash
sudo systemctl enable ai-agent-web   # Auto-start on boot
sudo systemctl disable ai-agent-web  # Don't auto-start
```

### View Logs

```bash
# Follow live logs
sudo journalctl -u ai-agent-web -f

# View last 100 lines
sudo journalctl -u ai-agent-email -n 100

# View logs from today
sudo journalctl -u ai-agent-web --since today
```

### Remove Services

```bash
cd ~/ai-agent-system
./remove-services.sh
```

This stops and removes all systemd services. Code stays in place for manual use.

---

## Usage

### Web Interface

1. Start server: `./start.sh` or `sudo systemctl start ai-agent-web`
2. Open browser: `http://your-server-ip:8000`
3. Type natural language commands
4. View AI responses and command outputs

**Example commands:**
- "What's the current disk usage?"
- "Show me files in /var/log"
- "Install nginx"
- "Create a file called test.txt with Hello World"
- "What's my IP address?"

### Email Interface

1. Start email server: `python email_server.py` or `sudo systemctl start ai-agent-email`
2. Send email from authorized address to server email
3. Wait 15-30 seconds for reply

### CLI Interface

```bash
cd ~/ai-agent-system
source venv/bin/activate
python agent.py
```

Type commands directly in terminal. Type `exit` to quit.

### Available Tools

The AI has access to 5 tools:

1. **run_bash** - Execute any bash command
2. **read_file** - Read file contents
3. **write_file** - Create or overwrite files
4. **list_directory** - List directory contents
5. **search_files** - Find files by name or content

The AI decides which tools to use based on your request.

---

## Troubleshooting

### Web Interface Won't Load

**Check if service is running:**
```bash
sudo systemctl status ai-agent-web
```

**Check if port is open:**
```bash
sudo ufw allow 8000/tcp
sudo ss -tlnp | grep 8000
```

Should show: `0.0.0.0:8000`

**Check .env configuration:**
```bash
cat ~/ai-agent-system/.env | grep HOST
```

Should be: `HOST=0.0.0.0`

**Restart service:**
```bash
sudo systemctl restart ai-agent-web
```

### WebSocket Connection Failed

**Symptoms:** Page loads but shows "Disconnected" in top right.

**Fix:**
1. Hard refresh browser: Ctrl+Shift+R
2. Check browser console (F12) for errors
3. Verify API key is set in .env
4. Restart service: `sudo systemctl restart ai-agent-web`

### Model Not Available (404 Error)

**Symptoms:** Error about model not found.

**Fix:** Your API key doesn't have access to that model. Edit .env:
```bash
AI_MODEL=claude-3-5-sonnet-20240620
```

Restart: `sudo systemctl restart ai-agent-web`

### AI Says "This requires sudo"

You need to configure passwordless sudo. See [Sudo Configuration](#sudo-configuration).

### Email Not Working

**Not receiving replies:**
- Check spam folder
- Verify EMAIL_ADDRESS is correct
- Check logs: `tail -f ~/ai-agent-logs/email_*.log`
- Verify service is running: `sudo systemctl status ai-agent-email`

**"Login failed" error:**
- Check app password is correct (no spaces)
- Verify 2FA is enabled on Gmail
- Try regenerating app password

### Logs Not Appearing

Logs are saved to `~/ai-agent-logs/`. Check:

```bash
ls -la ~/ai-agent-logs/
```

If empty, check permissions:
```bash
ls -la ~ | grep ai-agent-logs
```

### List Directory Returns Empty

Was fixed in latest version. Update your installation:
```bash
cd ~/ai-agent-system
# Re-extract from tarball or pull latest code
sudo systemctl restart ai-agent-web
```

---

## Security

### Important Security Notes

1. **Full Server Access**: The AI has complete access to your server. Only expose to trusted networks.
2. **Firewall**: Use UFW to restrict access
3. **Sudo Access**: Be cautious with passwordless sudo on production servers
4. **API Keys**: Keep .env file secure, never commit to git
5. **Email Authorization**: Only authorized email addresses can send commands
6. **Logs**: Contain sensitive information, store securely
7. **Network Access**: The AI can download files and make network requests

### Production Recommendations

- **Reverse Proxy**: Put behind nginx with SSL/TLS
- **Authentication**: Add password protection to web interface
- **Firewall**: Only allow access from known IPs
- **Monitoring**: Set up alerts for unusual activity
- **Backups**: Regular backups of .env and configuration
- **Updates**: Keep system and dependencies updated

### Adding Authentication to Web Interface

Edit `server.py` to add basic auth:

```python
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from secrets import compare_digest

security = HTTPBasic()

@app.get("/")
async def get_index(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = compare_digest(credentials.username, "admin")
    correct_password = compare_digest(credentials.password, "your-password")
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401)
    return FileResponse("index.html")
```

---

## Files Overview

### Core Files

- `agent.py` - AI agent brain with 5 tools
- `server.py` - Web interface with WebSocket
- `email_server.py` - Email agent
- `index.html` - Web UI
- `requirements.txt` - Python dependencies
- `system-prompt.txt` - AI behavior configuration

### Scripts

- `deploy.sh` - Master deployment automation
- `install.sh` - Install dependencies
- `start.sh` - Start web interface
- `start-email.sh` - Start email interface
- `setup-services.sh` - Install systemd services
- `remove-services.sh` - Remove systemd services

### Configuration

- `.env` - Environment variables (API key, model, email settings)
- `.env.example` - Template for .env file
- `system-prompt.txt` - AI system prompt

### Documentation

- `README.md` - This file (complete documentation)
- `QUICK-START.md` - Quick reference card

---

## License

MIT License - Use freely for personal or commercial projects.
