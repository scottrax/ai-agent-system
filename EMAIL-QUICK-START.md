# Email Agent - Quick Start (5 Minutes)

Control your server by sending emails from your phone or computer.

## Setup

### 1. Create Gmail for Server

Create: `myserver2025@gmail.com` at https://gmail.com

### 2. Get App Password

1. Enable 2FA: https://myaccount.google.com/security
2. Create app password: https://myaccount.google.com/apppasswords
3. Copy the 16-character password

### 3. Configure

```bash
cd ~/ai-agent-system
nano .env
```

Add:
```bash
EMAIL_ADDRESS=myserver2025@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop
AUTHORIZED_EMAILS=your.real.email@gmail.com
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 4. Start

```bash
cd ~/ai-agent-system
source venv/bin/activate
python email_server.py
```

### 5. Test

From your phone or computer, email `myserver2025@gmail.com`:

```
Subject: Test
Body: what's the date
```

Wait 15-30 seconds for email reply!

## How It Works

- **You email:** myserver2025@gmail.com
- **From:** your.real.email@gmail.com (must be in AUTHORIZED_EMAILS)
- **Server responds:** Via email back to you

## Make It Permanent

```bash
./setup-services.sh
# Choose option 3: Web + Email
```

Now it runs forever, starts on boot, restarts on failure.

## Security

Only emails from `AUTHORIZED_EMAILS` addresses work. Others are ignored.

Add multiple: `AUTHORIZED_EMAILS=alice@gmail.com,bob@work.com`

## Cost

- Gmail: FREE
- AI: $5-30/month
- Total: $5-30/month

See EMAIL-SETUP.md for full documentation.
