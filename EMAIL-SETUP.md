# Email AI Agent Setup

Control your Ubuntu server by sending emails! The AI monitors an inbox and responds only to authorized email addresses.

## How It Works

1. **You send email** to `server-email@gmail.com` from your authorized address
2. **Server monitors inbox** every 15 seconds
3. **AI processes your request** and executes commands
4. **You get email back** with the results

## Security

- Only emails from addresses in `AUTHORIZED_EMAILS` are processed
- Unauthorized emails are ignored and marked as read
- Each conversation is isolated per sender

## Setup Guide (10 Minutes)

### 1. Create Gmail Account for Your Server

Go to: https://gmail.com and create a new account like `myserver2025@gmail.com`

### 2. Enable 2-Factor Authentication

1. Go to: https://myaccount.google.com/security
2. Enable **2-Step Verification**
3. Complete setup

### 3. Create App Password

1. Go to: https://myaccount.google.com/apppasswords
2. Select app: **Mail**
3. Select device: **Other** (type "AI Agent")
4. Click **Generate**
5. Copy the 16-character password (no spaces)

### 4. Configure .env File

```bash
cd ~/ai-agent-system
nano .env
```

Add these lines:

```bash
# Email server configuration
EMAIL_ADDRESS=myserver2025@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop  # Your 16-char app password
AUTHORIZED_EMAILS=your.personal@gmail.com,work@company.com

# AI configuration (same as before)
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Important:**
- `EMAIL_ADDRESS` = The Gmail account your server monitors
- `EMAIL_PASSWORD` = The 16-character app password (with or without spaces)
- `AUTHORIZED_EMAILS` = Comma-separated list of YOUR email addresses that can control the server

### 5. Install & Start

```bash
cd ~/ai-agent-system
source venv/bin/activate

# Install if needed
pip install python-dotenv

# Start the email server
python email_server.py
```

You should see:
```
Starting email AI server...
Monitoring inbox: myserver2025@gmail.com
Authorized emails: your.personal@gmail.com
```

### 6. Test It!

**From your authorized email** (your.personal@gmail.com), send an email to your server:

```
To: myserver2025@gmail.com
Subject: Test
Body: what's the date
```

Wait 15-30 seconds, and you'll get an email back with the result!

## Usage Examples

Send emails with commands in the body:

```
To: myserver2025@gmail.com
Subject: Check disk space
Body: show me disk usage
```

```
To: myserver2025@gmail.com
Subject: Install nginx
Body: install nginx web server
```

```
To: myserver2025@gmail.com
Subject: Reset
Body: reset
```

## Run as System Service

To make it start on boot and restart on failure:

```bash
cd ~/ai-agent-system
./setup-services.sh
# Choose option 4 or "All services"
```

The email server will run as `ai-agent-email` service:

```bash
# Check status
sudo systemctl status ai-agent-email

# View logs
sudo journalctl -u ai-agent-email -f

# Restart
sudo systemctl restart ai-agent-email
```

## Multiple Authorized Users

You can authorize multiple email addresses:

```bash
AUTHORIZED_EMAILS=alice@gmail.com,bob@work.com,charlie@email.org
```

Each user gets their own conversation history with the AI.

## Troubleshooting

**"Login failed"**
- Make sure 2FA is enabled on the Gmail account
- Use an App Password, not your regular Gmail password
- Check for typos in EMAIL_ADDRESS or EMAIL_PASSWORD

**"No response"**
- Check you're sending from an AUTHORIZED_EMAIL address
- Check the server logs: `journalctl -u ai-agent-email -f`
- Gmail may delay emails by a few seconds

**"Permission denied" errors**
- Configure passwordless sudo (see SUDO-SETUP.md)

## Cost

- Gmail: **FREE**
- Anthropic API: **$5-30/month** depending on usage
- Total: **$5-30/month**

## Security Notes

- Your Gmail app password gives full access to that account - keep it secret
- Unauthorized emails are ignored but still arrive in the inbox
- Consider using a dedicated Gmail account just for the server
- Enable Gmail's "Less secure app access" if app passwords don't work

## Next Steps

- Run web interface AND email server simultaneously
- Set up automated email alerts
- Add more authorized users
- Configure custom email filters in Gmail
