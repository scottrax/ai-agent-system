# AI Agent Logging

The AI agent automatically logs all interactions to help you track what it's doing.

## Log File Location

All logs are stored in: `~/ai-agent-logs/`

## Log File Types

### Web Interface Logs
- **Format**: `web_session_[session-id]_[timestamp].log`
- **Example**: `web_session_a1b2c3d4_20251016_143052.log`
- **Contains**: One log file per browser session

### Email Interface Logs
- **Format**: `email_[timestamp].log`
- **Example**: `email_20251016_143052.log`
- **Contains**: All email interactions

### CLI Logs
- **Format**: `conversation_[timestamp].log`
- **Example**: `conversation_20251016_143052.log`
- **Contains**: Command-line interface conversations

## What Gets Logged

Each log file contains:

1. **Timestamps** - Exact date and time of each interaction
2. **User Messages** - Everything you ask or send
3. **Tool Executions** - Commands the AI runs with inputs and outputs
4. **AI Responses** - Everything the AI says back to you

## Log Format Example

```
=== AI Agent Conversation Log Started at 2025-10-16 14:30:52 ===

[2025-10-16 14:31:05] USER: what's the disk usage?

[2025-10-16 14:31:06] TOOL: run_bash
  Input: {
    "command": "df -h"
  }
  Result: {
    "stdout": "Filesystem      Size  Used Avail Use% Mounted on\n...",
    "stderr": "",
    "exit_code": 0
  }

[2025-10-16 14:31:07] AGENT: Your disk usage is as follows:
- / partition: 45% used (23GB of 50GB)
- /home partition: 12% used (6GB of 50GB)

[2025-10-16 14:32:15] USER: install nginx

[2025-10-16 14:32:16] TOOL: run_bash
  Input: {
    "command": "sudo apt update && sudo apt install nginx -y"
  }
  Result: {
    "stdout": "Reading package lists...\nBuilding dependency tree...",
    "stderr": "",
    "exit_code": 0
  }

[2025-10-16 14:32:20] AGENT: Nginx has been successfully installed and started.
```

## Viewing Logs

### View Latest Log
```bash
ls -t ~/ai-agent-logs/ | head -1 | xargs -I {} tail -f ~/ai-agent-logs/{}
```

### View Specific Log
```bash
cat ~/ai-agent-logs/web_session_xyz_20251016_143052.log
```

### Search Logs
```bash
# Find all times a specific command was run
grep -r "install nginx" ~/ai-agent-logs/

# Find all errors
grep -r "exit_code.*[^0]" ~/ai-agent-logs/
```

### Monitor in Real-Time
```bash
# Watch the most recent log
tail -f ~/ai-agent-logs/$(ls -t ~/ai-agent-logs/ | head -1)
```

## Log Rotation

Logs are not automatically deleted. To manage disk space:

### Delete Old Logs
```bash
# Delete logs older than 30 days
find ~/ai-agent-logs/ -name "*.log" -mtime +30 -delete

# Delete logs older than 7 days
find ~/ai-agent-logs/ -name "*.log" -mtime +7 -delete
```

### Archive Old Logs
```bash
# Compress logs older than 7 days
find ~/ai-agent-logs/ -name "*.log" -mtime +7 -exec gzip {} \;
```

### Set Up Automatic Cleanup (Optional)

Create a cron job:
```bash
crontab -e
```

Add this line to delete logs older than 30 days daily at 2 AM:
```
0 2 * * * find ~/ai-agent-logs/ -name "*.log" -mtime +30 -delete
```

## Privacy & Security

- Log files contain **everything** the AI does and sees
- This includes commands, file contents, system information
- Protect log files like you would protect your server access
- Do not share logs publicly without reviewing them first
- Consider encrypting sensitive logs

## Disabling Logs

If you don't want logging, you can disable it by modifying the agent initialization:

In `server.py`, `email_server.py`, or where the agent is created, pass `log_file=None` will still create logs, but you can comment out the logging code in `agent.py`.

## Troubleshooting

### Log Directory Not Found
The directory `~/ai-agent-logs/` is created automatically on first run. If missing:
```bash
mkdir -p ~/ai-agent-logs
```

### Permission Denied
Ensure the user running the agent has write permissions:
```bash
chmod 755 ~/ai-agent-logs
```

### Disk Space Issues
Check log directory size:
```bash
du -sh ~/ai-agent-logs/
```

Clean up if needed using the deletion commands above.
