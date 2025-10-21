#!/bin/bash

echo "======================================================================"
echo "Pi-hole Monitoring Cron Job Status Check"
echo "======================================================================"
echo ""

# Check 1: Cron job exists
echo "[1] Checking cron job configuration..."
if crontab -l 2>/dev/null | grep -q "pihole-health-check.sh"; then
    echo "    ✓ Cron job found in crontab"
    echo "    $(crontab -l 2>/dev/null | grep pihole-health-check.sh)"
else
    echo "    ✗ Cron job NOT found in crontab"
fi
echo ""

# Check 2: Script exists and is executable
echo "[2] Checking script file..."
if [ -x ~/ai-agent-system/pihole-health-check.sh ]; then
    echo "    ✓ Script exists and is executable"
    ls -lh ~/ai-agent-system/pihole-health-check.sh
else
    echo "    ✗ Script not found or not executable"
fi
echo ""

# Check 3: Pi-hole service running
echo "[3] Checking Pi-hole FTL service..."
if systemctl is-active --quiet pihole-FTL.service; then
    echo "    ✓ Pi-hole FTL service is RUNNING"
    systemctl status pihole-FTL.service --no-pager | head -3
else
    echo "    ✗ Pi-hole FTL service is NOT running"
fi
echo ""

# Check 4: Port 53 listening
echo "[4] Checking DNS port 53..."
if sudo ss -tulpen 2>/dev/null | grep -q ':53'; then
    echo "    ✓ Port 53 is listening"
    sudo ss -tulpen 2>/dev/null | grep ':53'
else
    echo "    ✗ Port 53 is NOT listening"
fi
echo ""

# Check 5: msmtp configuration
echo "[5] Checking email configuration..."
if [ -f ~/.msmtprc ]; then
    echo "    ✓ msmtp config file exists"
    if grep -q "NEEDS_APP_PASSWORD" ~/.msmtprc; then
        echo "    ⚠ WARNING: Gmail App Password not configured!"
        echo "    Run: bash ~/ai-agent-system/setup-gmail-password.sh"
    else
        echo "    ✓ Gmail App Password appears to be configured"
    fi
    echo "    From: $(grep '^from' ~/.msmtprc | head -1)"
else
    echo "    ✗ msmtp config file not found"
fi
echo ""

# Check 6: Health check log
echo "[6] Checking health check log..."
if [ -f ~/ai-agent-system/pihole-health.log ]; then
    echo "    ✓ Log file exists"
    echo "    Recent entries:"
    tail -3 ~/ai-agent-system/pihole-health.log | sed 's/^/        /'
else
    echo "    ✗ Log file not found"
fi
echo ""

# Check 7: Alert state
echo "[7] Checking alert state..."
if [ -f ~/ai-agent-system/pihole-alert-state ]; then
    STATE=$(cat ~/ai-agent-system/pihole-alert-state)
    echo "    Current state: $STATE"
else
    echo "    ✗ Alert state file not found"
fi
echo ""

# Check 8: DNS resolution test
echo "[8] Testing DNS resolution..."
if timeout 5 dig @127.0.0.1 google.com +short > /dev/null 2>&1; then
    echo "    ✓ DNS resolution is working"
else
    echo "    ✗ DNS resolution test failed"
fi
echo ""

# Check 9: Next cron execution
echo "[9] Next scheduled execution..."
NEXT_MINUTE=$(( ($(date +%M) / 5 + 1) * 5 ))
if [ $NEXT_MINUTE -ge 60 ]; then
    NEXT_MINUTE=$(( NEXT_MINUTE - 60 ))
    NEXT_HOUR=$(( $(date +%H) + 1 ))
    echo "    Approximately in $((60 - $(date +%M) + NEXT_MINUTE)) seconds"
    echo "    at $(date +%H):$NEXT_MINUTE (roughly)"
else
    echo "    Approximately in $((NEXT_MINUTE - $(date +%M))) minutes"
    echo "    at $(date +%H):$NEXT_MINUTE (roughly)"
fi
echo ""

echo "======================================================================"
echo "Summary:"
echo "======================================================================"
echo ""
echo "The Pi-hole monitoring cron job is configured to run every 5 minutes."
echo ""
echo "If you see ✗ marks above, refer to PIHOLE_CRON_SETUP.md for fixes."
echo ""
echo "To view the full setup documentation:"
echo "  cat ~/ai-agent-system/PIHOLE_CRON_SETUP.md"
echo ""
echo "To manually test the health check:"
echo "  bash ~/ai-agent-system/pihole-health-check.sh"
echo ""
echo "To configure Gmail app password (if not done):"
echo "  bash ~/ai-agent-system/setup-gmail-password.sh"
echo ""
