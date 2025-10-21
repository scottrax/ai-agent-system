# Step-by-Step Setup Guide for Ubuntu Server

## Prerequisites

- Ubuntu Server 20.04 LTS or newer
- SSH access to your server
- Sudo privileges
- Internet connection

## Step 1: Copy Files to Server

### Option A: Using SCP (From Your Local Machine)

```bash
# From your local machine where you have the ai-agent-system folder
scp -r ai-agent-system username@your-server-ip:~/

# Example:
# scp -r ai-agent-system ubuntu@192.168.1.100:~/
```

### Option B: Using Git (On Server)

```bash
# SSH into your server first
ssh username@your-server-ip

# Clone or download the files
# (You would need to upload this to GitHub first, or use scp method above)
```

### Option C: Manual Upload via SFTP

Use an SFTP client like FileZilla or WinSCP to upload the folder.

## Step 2: Connect to Your Server

```bash
ssh username@your-server-ip

# Example:
# ssh ubuntu@192.168.1.100
```

## Step 3: Navigate to Directory

```bash
cd ~/ai-agent-system
ls -la

# You should see:
# agent.py
# server.py
# index.html
# requirements.txt
# install.sh
# README.md
```

## Step 4: Run the Installer

```bash
# Make the install script executable
chmod +x install.sh

# Run the installer
./install.sh
```

**What the installer does:**
1. Updates Ubuntu packages
2. Installs Python 3.10+ if needed
3. Creates a Python virtual environment
4. Installs all Python dependencies
5. Creates systemd service file
6. Configures firewall (if UFW is installed)
7. Creates startup scripts

This takes about 5-10 minutes depending on your server speed.

## Step 5: Get Your API Key

1. Open your web browser
2. Go to: https://console.anthropic.com/
3. Sign up or log in
4. Click on "API Keys" in the left sidebar
5. Click "Create Key"
6. Give it a name like "Ubuntu Server Agent"
7. Click "Create Key"
8. **Copy the key immediately** (you won't see it again!)

The key looks like: `sk-ant-api03-xxx...`

## Step 6: Configure Your API Key

```bash
# Copy the example environment file
cp .env.example .env

# Edit the file
nano .env
```

In the nano editor:
1. Replace `your-api-key-here` with your actual API key
2. Press `Ctrl + X` to exit
3. Press `Y` to save
4. Press `Enter` to confirm

Your `.env` file should look like:
```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
HOST=0.0.0.0
PORT=8000
```

## Step 7: Start the Agent

### Method 1: Quick Test (Web Server)

```bash
./start.sh
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Don't close this terminal!** Open a web browser and go to:
```
http://your-server-ip:8000
```

Example: `http://192.168.1.100:8000`

### Method 2: CLI Test

Open a new terminal, SSH into your server again:

```bash
cd ~/ai-agent-system
./start-cli.sh
```

You'll see a chat interface:
```
 AI AGENT STARTED
 You: 
```

Try typing: "What's the current date and time?"

### Method 3: System Service (Production)

For automatic startup on boot:

```bash
# Edit the service configuration
sudo systemctl edit ai-agent
```

This opens an editor. Add:
```
[Service]
Environment="ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here"
```

Save and exit, then:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Start the service
sudo systemctl start ai-agent

# Enable auto-start on boot
sudo systemctl enable ai-agent

# Check if it's running
sudo systemctl status ai-agent
```

You should see "active (running)" in green.

Access the web interface at: `http://your-server-ip:8000`

## Step 8: Test the Agent

### Web Interface Tests

Go to `http://your-server-ip:8000` and try:

1. **Simple command:**
   ```
   What's the current date and time?
   ```

2. **File operations:**
   ```
   Create a file called test.txt in my home directory with the text "Hello from AI"
   ```

3. **System info:**
   ```
   What's my server's CPU and memory usage?
   ```

4. **Directory listing:**
   ```
   List all files in the /etc directory
   ```

### CLI Tests

If using `./start-cli.sh`, type the same commands above.

## Step 9: Access from Outside Your Network (Optional)

### Option A: Port Forwarding (Home Network)

1. Log into your router's admin panel
2. Find "Port Forwarding" settings
3. Add a rule:
   - External Port: 8000
   - Internal IP: Your server's local IP (e.g., 192.168.1.100)
   - Internal Port: 8000
   - Protocol: TCP
4. Access via: `http://your-public-ip:8000`

Find your public IP: https://whatismyipaddress.com/

### Option B: Using Ngrok (Quick Testing)

```bash
# Install ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/

# Sign up at ngrok.com and get auth token
ngrok config add-authtoken YOUR_TOKEN

# Expose your agent
ngrok http 8000
```

Ngrok gives you a public URL like: `https://abc123.ngrok.io`

### Option C: Cloudflare Tunnel (Free & Secure)

```bash
# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Authenticate
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create ai-agent

# Run tunnel
cloudflared tunnel --url http://localhost:8000
```

## Common Issues & Solutions

### Issue: "Connection refused" in browser

**Solution:**
```bash
# Check if service is running
sudo systemctl status ai-agent

# Check if port is open
sudo netstat -tlnp | grep 8000

# Check firewall
sudo ufw status
sudo ufw allow 8000/tcp
```

### Issue: "ANTHROPIC_API_KEY not set"

**Solution:**
```bash
# Verify .env file exists
cat .env

# Make sure it has your key
# If using systemd, update the service:
sudo systemctl edit ai-agent
# Add the Environment line with your key
sudo systemctl daemon-reload
sudo systemctl restart ai-agent
```

### Issue: "Permission denied" errors

**Solution:**
```bash
# Make scripts executable
chmod +x install.sh start.sh start-cli.sh

# Check ownership
ls -la
# All files should be owned by your user
```

### Issue: Python version too old

**Solution:**
```bash
# Install Python 3.11
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv -y

# Re-run install
./install.sh
```

### Issue: Service keeps restarting

**Solution:**
```bash
# Check logs for errors
sudo journalctl -u ai-agent -n 50 --no-pager

# Common fixes:
# 1. Invalid API key - check your key
# 2. Port in use - change PORT in .env
# 3. Missing dependencies - re-run install.sh
```

## Verifying Installation

Run this checklist:

```bash
# 1. Check Python version
python3 --version
# Should be 3.10 or higher

# 2. Check virtual environment
ls -la venv/
# Should exist with bin/, lib/, etc.

# 3. Check dependencies
source venv/bin/activate
pip list | grep anthropic
pip list | grep fastapi
deactivate

# 4. Check API key
cat .env | grep ANTHROPIC_API_KEY
# Should show your key

# 5. Check service
sudo systemctl status ai-agent
# Should show "active (running)" if using service

# 6. Test web endpoint
curl http://localhost:8000/health
# Should return: {"status":"healthy","active_sessions":0}
```

## Next Steps

Now that it's working:

1. **Explore capabilities** - Try different commands
2. **Read README.md** - Learn about security and advanced features
3. **Add custom tools** - Extend the agent for your specific needs
4. **Set up HTTPS** - Follow the nginx section in README.md
5. **Monitor logs** - `sudo journalctl -u ai-agent -f`

## Getting Help

If you encounter issues:

1. Check logs: `sudo journalctl -u ai-agent -n 100`
2. Test manually: `./start.sh` (see errors directly)
3. Verify each step in this guide
4. Check the Troubleshooting section in README.md

## Example Session

Here's what a successful first session looks like:

```
 AI AGENT STARTED

 You: What's the current date and system uptime?

 Agent: The current date and time is [shows date]. 
Your system has been running for [uptime info].

 You: Create a file called hello.txt with "Hello World"

 Agent: I've created the file /home/username/hello.txt 
with the content "Hello World".

 You: Read that file back to me

 Agent: The file contains: Hello World

 You: What's my disk usage?

 Agent: Here's your disk usage:
Filesystem      Size  Used Avail Use% Mounted on
[disk info]
```

Congratulations! Your AI agent is now running and ready to help manage your server! 
