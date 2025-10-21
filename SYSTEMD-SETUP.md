# Systemd Setup - Auto-Start on Boot & Auto-Restart on Failure

This guide shows you how to set up your AI agent to:
- ✅ Start automatically on boot
- ✅ Restart automatically on failure
- ✅ Run in the background as a system service
- ✅ Manage with standard systemd commands

## Quick Setup (Recommended)

We've created an automated script that sets everything up for you:

```bash
cd ~/ai-agent-system
./setup-services.sh
```

This script will:
1. Ask which services you want to install (web, SMS Twilio, SMS email, or all)
2. Create systemd service files
3. Enable auto-start on boot
4. Start the services immediately
5. Configure auto-restart on failure

That's it! Your services are now running and will survive reboots and crashes.

## What Services Are Available?

You can install any combination of:

1. **ai-agent-web** - Web interface on port 8000
2. **ai-agent-sms-twilio** - SMS via Twilio (paid)
3. **ai-agent-sms-email** - SMS via email gateway (free)

All three can run simultaneously if you want multiple access methods.

## Manual Setup (If You Prefer)

If you want to understand what's happening or customize, here's the manual process:

### 1. Create Service File

For the **web interface**:

```bash
sudo nano /etc/systemd/system/ai-agent-web.service
```

Add this content (replace `USERNAME` with your username):

```ini
[Unit]
Description=AI Agent Web Interface
After=network.target

[Service]
Type=simple
User=USERNAME
WorkingDirectory=/home/USERNAME/ai-agent-system
Environment="PATH=/home/USERNAME/ai-agent-system/venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/home/USERNAME/ai-agent-system/.env
ExecStart=/home/USERNAME/ai-agent-system/venv/bin/python server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Key configuration explained:**
- `After=network.target` - Wait for network before starting
- `Restart=always` - Restart on any failure
- `RestartSec=10` - Wait 10 seconds before restarting
- `EnvironmentFile` - Load your .env configuration
- `StandardOutput=journal` - Send logs to systemd journal

### 2. Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-agent-web
sudo systemctl start ai-agent-web
```

### 3. Verify It's Running

```bash
sudo systemctl status ai-agent-web
```

You should see:
```
● ai-agent-web.service - AI Agent Web Interface
   Loaded: loaded (/etc/systemd/system/ai-agent-web.service; enabled)
   Active: active (running) since...
```

## Service Management Commands

### Check Status

```bash
# Web interface
sudo systemctl status ai-agent-web

# SMS Twilio
sudo systemctl status ai-agent-sms-twilio

# SMS Email
sudo systemctl status ai-agent-sms-email
```

### View Live Logs

```bash
# Web interface
sudo journalctl -u ai-agent-web -f

# SMS Twilio
sudo journalctl -u ai-agent-sms-twilio -f

# SMS Email
sudo journalctl -u ai-agent-sms-email -f

# All services combined
sudo journalctl -u ai-agent-* -f
```

### View Recent Logs

```bash
# Last 50 lines
sudo journalctl -u ai-agent-web -n 50

# Last hour
sudo journalctl -u ai-agent-web --since "1 hour ago"

# Today's logs
sudo journalctl -u ai-agent-web --since today

# Specific date range
sudo journalctl -u ai-agent-web --since "2025-10-15" --until "2025-10-16"
```

### Restart a Service

```bash
sudo systemctl restart ai-agent-web
```

### Stop a Service

```bash
sudo systemctl stop ai-agent-web
```

### Start a Service

```bash
sudo systemctl start ai-agent-web
```

### Disable Auto-Start (but don't stop now)

```bash
sudo systemctl disable ai-agent-web
```

### Enable Auto-Start (but don't start now)

```bash
sudo systemctl enable ai-agent-web
```

## Testing Auto-Restart

To verify auto-restart works, intentionally crash the service:

```bash
# Find the process ID
ps aux | grep "python server.py"

# Kill it
sudo kill -9 <PID>

# Watch it automatically restart
sudo journalctl -u ai-agent-web -f
```

You should see it restart within 10 seconds.

## Testing Auto-Start on Boot

```bash
# Reboot your server
sudo reboot

# After reboot, check if services are running
sudo systemctl status ai-agent-web
```

## Updating Configuration

If you change your `.env` file, restart the services:

```bash
sudo systemctl restart ai-agent-web
sudo systemctl restart ai-agent-sms-twilio
sudo systemctl restart ai-agent-sms-email
```

## Updating Code

When you update the Python files:

```bash
cd ~/ai-agent-system
git pull  # or however you update

# Restart services to load new code
sudo systemctl restart ai-agent-web
sudo systemctl restart ai-agent-sms-twilio
sudo systemctl restart ai-agent-sms-email
```

## Resource Limits (Optional)

To prevent the agent from using too much memory:

```bash
sudo systemctl edit ai-agent-web
```

Add:
```ini
[Service]
MemoryMax=1G
MemoryHigh=800M
```

This limits the service to 1GB RAM.

## Running Multiple Instances

If you want to run multiple instances on different ports:

```bash
# Copy the service file
sudo cp /etc/systemd/system/ai-agent-web.service /etc/systemd/system/ai-agent-web-2.service

# Edit it
sudo nano /etc/systemd/system/ai-agent-web-2.service

# Change the port in the Environment section
Environment="PORT=8001"

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable ai-agent-web-2
sudo systemctl start ai-agent-web-2
```

## Removing Services

If you want to remove the systemd services:

```bash
cd ~/ai-agent-system
./remove-services.sh
```

Or manually:

```bash
# Stop and disable
sudo systemctl stop ai-agent-web
sudo systemctl disable ai-agent-web

# Remove service file
sudo rm /etc/systemd/system/ai-agent-web.service

# Reload systemd
sudo systemctl daemon-reload
```

## Troubleshooting

### Service Won't Start

```bash
# Check detailed status
sudo systemctl status ai-agent-web -l

# Check logs
sudo journalctl -u ai-agent-web -n 100 --no-pager

# Common issues:
# 1. Wrong paths in service file
# 2. Missing .env file
# 3. Missing ANTHROPIC_API_KEY in .env
# 4. Port already in use
# 5. Permission issues
```

### Service Starts But Crashes Immediately

```bash
# Watch it crash in real-time
sudo journalctl -u ai-agent-web -f

# Then start the service in another terminal
sudo systemctl restart ai-agent-web
```

Look for Python errors in the logs.

### Port Already in Use

```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill it
sudo kill <PID>

# Or change your port in .env
echo "PORT=8001" >> .env
sudo systemctl restart ai-agent-web
```

### Permission Denied Errors

Make sure the service runs as your user, not root:

```bash
# Check the service file
sudo systemctl cat ai-agent-web | grep User=

# Should show your username, not root
```

### Environment Variables Not Loading

```bash
# Verify .env file exists and is readable
ls -la ~/ai-agent-system/.env

# Make sure EnvironmentFile path is correct in service
sudo systemctl cat ai-agent-web | grep EnvironmentFile=

# Test manually
cd ~/ai-agent-system
source venv/bin/activate
source .env
python server.py  # Should work
```

## Best Practices

1. **Always check logs** after enabling services
2. **Test manually first** before creating services
3. **Use setup-services.sh** for automated setup
4. **Monitor logs regularly** with `journalctl -f`
5. **Set up log rotation** (systemd does this automatically)
6. **Document your changes** if you customize service files

## Security Notes

- Services run as your user, not root (good!)
- Logs are stored in systemd journal (secure)
- .env file should have restricted permissions: `chmod 600 .env`
- Consider firewall rules: `sudo ufw allow 8000/tcp`

## Summary

**Quick setup:**
```bash
./setup-services.sh
```

**Check everything is running:**
```bash
sudo systemctl status ai-agent-*
```

**View logs:**
```bash
sudo journalctl -u ai-agent-* -f
```

**Remove everything:**
```bash
./remove-services.sh
```

That's it! Your AI agent now runs like any other system service.
