#!/bin/bash
#
# Pi-hole Health Check Script
# Monitors Pi-hole service health and sends email alerts on failure
# 

# Configuration
ALERT_EMAIL="skitles1994@gmail.com"
FROM_EMAIL="jupiterserver45@gmail.com"
HOSTNAME=$(hostname)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="$HOME/ai-agent-system/pihole-health.log"
STATE_FILE="$HOME/ai-agent-system/pihole-alert-state"

# Initialize state file if it doesn't exist
[ ! -f "$STATE_FILE" ] && echo "OK" > "$STATE_FILE"
LAST_STATE=$(cat "$STATE_FILE")

# Function to send alert email
send_alert() {
    local subject="$1"
    local body="$2"
    
    echo -e "Subject: $subject\nFrom: $FROM_EMAIL\nTo: $ALERT_EMAIL\n\n$body" | msmtp -a gmail "$ALERT_EMAIL"
    
    if [ $? -eq 0 ]; then
        echo "[$TIMESTAMP] Alert email sent successfully" >> "$LOG_FILE"
        return 0
    else
        echo "[$TIMESTAMP] ERROR: Failed to send alert email" >> "$LOG_FILE"
        return 1
    fi
}

# Function to send recovery email
send_recovery() {
    local subject="[RESOLVED] Pi-hole Service Recovered on $HOSTNAME"
    local body="Pi-hole service has recovered and is now functioning normally.

Time: $TIMESTAMP
Server: $HOSTNAME

All checks are now passing."
    
    send_alert "$subject" "$body"
}

# Health check variables
ISSUES=""
FAILED_CHECKS=0

# Check 1: pihole-FTL service status
if ! systemctl is-active --quiet pihole-FTL.service; then
    ISSUES="${ISSUES}❌ pihole-FTL service is NOT running\n"
    ((FAILED_CHECKS++))
else
    ISSUES="${ISSUES}✓ pihole-FTL service is running\n"
fi

# Check 2: FTL listening on port 53
if ! sudo ss -tulpen | grep -q ':53.*pihole-FTL'; then
    ISSUES="${ISSUES}❌ Pi-hole FTL is NOT listening on port 53\n"
    ((FAILED_CHECKS++))
else
    ISSUES="${ISSUES}✓ FTL listening on port 53\n"
fi

# Check 3: DNS resolution test
if ! timeout 5 dig @127.0.0.1 google.com +short > /dev/null 2>&1; then
    ISSUES="${ISSUES}❌ DNS resolution test FAILED\n"
    ((FAILED_CHECKS++))
else
    ISSUES="${ISSUES}✓ DNS resolution working\n"
fi

# Check 4: pihole command functional
if ! timeout 5 pihole status > /dev/null 2>&1; then
    ISSUES="${ISSUES}❌ pihole command FAILED\n"
    ((FAILED_CHECKS++))
else
    ISSUES="${ISSUES}✓ pihole command responsive\n"
fi

# Check 5: Web interface (if lighttpd is running)
if systemctl is-active --quiet lighttpd.service; then
    if ! curl -s -o /dev/null -w "%{http_code}" http://localhost/admin/ | grep -q "200\|301\|302"; then
        ISSUES="${ISSUES}⚠ Web interface may have issues\n"
        ((FAILED_CHECKS++))
    else
        ISSUES="${ISSUES}✓ Web interface responding\n"
    fi
fi

# Determine overall health status
if [ $FAILED_CHECKS -gt 0 ]; then
    CURRENT_STATE="FAILED"
    
    # Only send alert if state changed from OK to FAILED (avoid spam)
    if [ "$LAST_STATE" != "FAILED" ]; then
        SUBJECT="[ALERT] Pi-hole Service Issue Detected on $HOSTNAME"
        BODY="Pi-hole health check has detected issues requiring attention!

Time: $TIMESTAMP
Server: $HOSTNAME
Failed Checks: $FAILED_CHECKS

Status Details:
$(echo -e "$ISSUES")

Recommended Actions:
1. Check service status: sudo systemctl status pihole-FTL
2. View Pi-hole logs: pihole -t
3. Check system resources: df -h && free -h
4. Restart if needed: sudo systemctl restart pihole-FTL

This is an automated alert from the Pi-hole monitoring system."
        
        send_alert "$SUBJECT" "$BODY"
        echo "$CURRENT_STATE" > "$STATE_FILE"
    fi
    
    # Log the failed check
    echo "[$TIMESTAMP] HEALTH CHECK FAILED - $FAILED_CHECKS issues detected" >> "$LOG_FILE"
    exit 1
    
else
    CURRENT_STATE="OK"
    
    # Send recovery email if we just recovered
    if [ "$LAST_STATE" == "FAILED" ]; then
        send_recovery
    fi
    
    echo "$CURRENT_STATE" > "$STATE_FILE"
    echo "[$TIMESTAMP] Health check passed - all systems operational" >> "$LOG_FILE"
    exit 0
fi
