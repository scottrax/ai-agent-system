# Quick Start Guide - 5 Minutes to Running

## For the Impatient 🚀

### 1. Get the Files to Your Ubuntu Server

**Download the folder to your computer first**, then:

```bash
scp -r ai-agent-system ubuntu@YOUR_SERVER_IP:~/
```

Replace `ubuntu` with your username and `YOUR_SERVER_IP` with your server's IP address.

### 2. SSH In

```bash
ssh ubuntu@YOUR_SERVER_IP
cd ~/ai-agent-system
```

### 3. Install

```bash
chmod +x install.sh
./install.sh
```

Wait 5-10 minutes for installation to complete.

### 4. Get API Key

1. Visit: <https://console.anthropic.com/>
2. Sign up/login
3. Create API key
4. Copy it (starts with `sk-ant-`)

### 5. Configure

```bash
cp .env.example .env
nano .env
```

Replace `your-api-key-here` with your actual key.\
Press `Ctrl+X`, then `Y`, then `Enter` to save.

### 6. Run It

```markdown
```

`file ./start.sh` 

### 7. Open Browser

Go to: `http://YOUR_SERVER_IP:8000`

**Done!** 🎉

Start chatting with your server:

- "What's the current date and time?"
- "Show me system memory usage"
- "Create a file called test.txt with 'Hello World'"

---

## Installing Packages (nginx, docker, etc.)

For the agent to install software, you need passwordless sudo:

```bash
sudo visudo
# Add at the end (replace 'username'):
username ALL=(ALL) NOPASSWD: ALL
```

Now you can ask: "Install nginx" and it will run `sudo apt install nginx -y` automatically.

**See [SUDO-SETUP.md](http://SUDO-SETUP.md) for security details and alternatives.**

---

## Need More Help?

- **Full details:** Read `file SETUP-GUIDE.md` 
- **Features & security:** Read `file README.md` 
- **Troubleshooting:** Check the troubleshooting sections in [README.md](http://README.md)

## Cost

- About $0.001-0.005 per command
- Typical monthly usage: $5-30

## To Run on Startup

```bash
sudo systemctl edit ai-agent
```

Add:

```markdown
[Service]
Environment="ANTHROPIC_API_KEY=sk-ant-your-key-here"
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-agent
sudo systemctl start ai-agent
```

Check status: `sudo systemctl status ai-agent`

## Common Issue: Can't Connect

```bash
# Open firewall
sudo ufw allow 8000/tcp

# Check if running
curl http://localhost:8000/health
```

Should return: `{"status":"healthy",...}`