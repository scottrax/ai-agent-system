================================================================================
PI-HOLE HEALTH MONITORING SYSTEM
================================================================================

OVERVIEW
--------
Automated monitoring system that checks Pi-hole service health every 5 minutes
and sends email alerts when issues are detected.

CONFIGURATION
-------------
Monitor Email (from):  jupiterserver45@gmail.com
Alert Email (to):      skitles1994@gmail.com
Check Frequency:       Every 5 minutes
Hostname:              $(hostname)

FILES & LOCATIONS
-----------------
Health Check Script:   ~/ai-agent-system/pihole-health-check.sh
Log File:              ~/ai-agent-system/pihole-health.log
State File:            ~/ai-agent-system/pihole-alert-state
Gmail Setup Script:    ~/ai-agent-system/setup-gmail-password.sh
SMTP Config:           ~/.msmtprc (permissions: 600)
SMTP Log:              ~/.msmtp.log

CRON JOB
--------
Current crontab entry:
  */5 * * * * /home/scottrax/ai-agent-system/pihole-health-check.sh

This runs the health check every 5 minutes (at :00, :05, :10, etc.)

HEALTH CHECKS PERFORMED
-----------------------
1. pihole-FTL service status (systemd)
2. FTL listening on port 53 (DNS port)
3. DNS resolution functionality (query test)
4. pihole command responsiveness
5. Web interface availability (if lighttpd running)

ALERT BEHAVIOR
--------------
- First failure: Sends alert email immediately
- Subsequent failures: No additional emails (avoids spam)
- Recovery: Sends recovery notification when service returns to normal
- State tracking prevents duplicate alerts

EMAIL SETUP (IMPORTANT!)
------------------------
Gmail requires an "App Password" for SMTP authentication.

TO COMPLETE SETUP:
1. Go to: https://myaccount.google.com/apppasswords
2. Sign in to: jupiterserver45@gmail.com
3. Enable 2-factor authentication if not already enabled
4. Create new app password:
   - Name it "Pi-hole Monitor" or similar
   - Copy the 16-character password
5. Run the setup script:
   ~/ai-agent-system/setup-gmail-password.sh
6. Or manually edit ~/.msmtprc and replace:
   password       YOUR_GMAIL_APP_PASSWORD_HERE
   with your actual app password

TEST EMAIL:
After configuring, test with:
  echo "Test" | mail -s "Pi-hole Test" skitles1994@gmail.com

MANUAL COMMANDS
---------------
Run health check manually:
  ~/ai-agent-system/pihole-health-check.sh

View recent logs:
  tail -f ~/ai-agent-system/pihole-health.log

Check current state:
  cat ~/ai-agent-system/pihole-alert-state

View cron jobs:
  crontab -l

Edit cron jobs:
  crontab -e

Send test email:
  echo "Subject: Test
  
  This is a test" | msmtp -a gmail skitles1994@gmail.com

Check SMTP log:
  tail ~/.msmtp.log

TROUBLESHOOTING
---------------
If emails aren't sending:
1. Check ~/.msmtp.log for errors
2. Verify Gmail app password is set correctly in ~/.msmtprc
3. Ensure 2FA is enabled on jupiterserver45@gmail.com
4. Test SMTP: msmtp -a gmail --serverinfo
5. Check script has execute permissions: ls -l ~/ai-agent-system/pihole-health-check.sh

If health checks are failing incorrectly:
1. Run manually to see detailed output: ~/ai-agent-system/pihole-health-check.sh
2. Check pihole status: pihole status
3. Check FTL status: sudo systemctl status pihole-FTL
4. Check port 53: sudo ss -tulpen | grep :53

To disable monitoring temporarily:
  crontab -e
  # Comment out the line: #*/5 * * * * /home/scottrax/ai-agent-system/pihole-health-check.sh

To re-enable:
  crontab -e
  # Remove the # from the line

ALERT EMAIL EXAMPLE
-------------------
Subject: [ALERT] Pi-hole Service Issue Detected on [hostname]

Pi-hole health check has detected issues requiring attention!

Time: 2025-10-19 01:20:00
Server: [hostname]
Failed Checks: 2

Status Details:
❌ pihole-FTL service is NOT running
✓ FTL listening on port 53
❌ DNS resolution test FAILED
✓ pihole command responsive
✓ Web interface responding

Recommended Actions:
1. Check service status: sudo systemctl status pihole-FTL
2. View Pi-hole logs: pihole -t
3. Check system resources: df -h && free -h
4. Restart if needed: sudo systemctl restart pihole-FTL

NEXT STEPS
----------
1. Complete Gmail app password setup (see EMAIL SETUP section)
2. Run test to verify emails work
3. Monitor ~/ai-agent-system/pihole-health.log to confirm checks are running
4. Wait for or simulate a failure to test alerting

Created: $(date)
================================================================================
