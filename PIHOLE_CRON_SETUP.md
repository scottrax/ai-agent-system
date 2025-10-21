PIHOLE HEALTH MONITORING CRON JOB SETUP
========================================

OVERVIEW
--------
A cron job has been configured to run Pi-hole health checks every 5 minutes.
If any issues are detected, an automated email alert is sent to skitles1994@gmail.com
from jupiterserver45@gmail.com.

CURRENT CONFIGURATION
---------------------

Cron Job:
  Schedule: */5 * * * * (every 5 minutes)
  Script: /home/scottrax/ai-agent-system/pihole-health-check.sh
  User: scottrax
  Status: ACTIVE

Email Configuration:
  From: jupiterserver45@gmail.com
  To: skitles1994@gmail.com
  MTA: msmtp (configured with Gmail SMTP)
  Config: ~/.msmtprc (permissions: 600)

HEALTH CHECKS PERFORMED
-----------------------

1. pihole-FTL Service Status
   - Verifies the FTL service is running
   - Critical for DNS functionality

2. Port 53 Binding
   - Confirms FTL is listening on DNS port 53
   - Essential for DNS queries

3. DNS Resolution Test
   - Tests actual DNS resolution with: dig @127.0.0.1 google.com
   - Validates functional DNS service

4. Pi-hole Command
   - Runs: pihole status
   - Checks if pi-hole CLI tool is responsive

5. Web Interface (optional)
   - Tests HTTP response from http://localhost/admin/
   - Only if lighttpd is running

ALERT BEHAVIOR
--------------

- Alerts are sent ONLY when state changes from OK to FAILED
- This prevents alert spam from repetitive failures
- A recovery email is sent when service returns to normal
- State is tracked in: ~/ai-agent-system/pihole-alert-state
- Log entries are written to: ~/ai-agent-system/pihole-health.log

MONITORING THE JOB
------------------

View cron schedule:
  crontab -l

Check last execution in system logs:
  grep CRON /var/log/syslog | tail -20

View health check log:
  tail -f ~/ai-agent-system/pihole-health.log

View alert state:
  cat ~/ai-agent-system/pihole-alert-state

Check msmtp logs:
  tail -f ~/.msmtp.log

TROUBLESHOOTING
---------------

If alerts are not being sent:

1. Verify Gmail App Password is configured:
   grep "password" ~/.msmtprc
   (Should NOT show "NEEDS_APP_PASSWORD")

2. Test email manually:
   echo -e "Subject: Test\n\nTest message" | msmtp -a gmail skitles1994@gmail.com

3. Check msmtp log:
   cat ~/.msmtp.log

4. Verify pi-hole is actually running:
   systemctl status pihole-FTL.service

5. Test the health check script directly:
   ~/ai-agent-system/pihole-health-check.sh
   echo "Exit code: $?"

SETTING UP GMAIL APP PASSWORD
------------------------------

If you haven't set up the Gmail App Password yet:

1. Run the setup script:
   bash ~/ai-agent-system/setup-gmail-password.sh

2. Follow the prompts to enter your 16-character app password

3. A test email will be sent to verify configuration

GENERATING A GMAIL APP PASSWORD
--------------------------------

1. Go to: https://myaccount.google.com/apppasswords
2. Sign in with: jupiterserver45@gmail.com
3. Select "Mail" and "Linux" (or "Other")
4. Google will generate a 16-character password
5. Copy and use this in the setup script

IMPORTANT SECURITY NOTES
------------------------

- ~/.msmtprc contains your Gmail app password
- Permissions are set to 600 (readable only by your user)
- Never commit this file to version control
- App passwords are more secure than your actual Gmail password
- You can revoke app passwords at any time from your Google Account

FILES AND LOCATIONS
-------------------

Script: ~/ai-agent-system/pihole-health-check.sh
Log: ~/ai-agent-system/pihole-health.log
State: ~/ai-agent-system/pihole-alert-state
Mail Config: ~/.msmtprc
Mail Log: ~/.msmtp.log
Crontab: crontab -l

MANUAL TESTING
--------------

Run the health check manually:
  bash ~/ai-agent-system/pihole-health-check.sh

Test DNS resolution:
  dig @127.0.0.1 google.com

Check FTL service:
  systemctl status pihole-FTL.service

Check port 53:
  sudo ss -tulpen | grep :53

RECENT LOG ENTRIES
------------------

Check the most recent health check results:
  tail -10 ~/ai-agent-system/pihole-health.log

Pi-hole FTL Status:
  systemctl is-active pihole-FTL.service

Service Details:
  systemctl status pihole-FTL.service --no-pager

NEXT STEPS
----------

1. If alerts are not configured yet:
   bash ~/ai-agent-system/setup-gmail-password.sh

2. Monitor the health check log:
   tail -f ~/ai-agent-system/pihole-health.log

3. Test an alert by temporarily stopping pi-hole:
   sudo systemctl stop pihole-FTL.service
   # Wait for next cron execution (max 5 mins)
   # You should receive an alert email
   # Then restore:
   sudo systemctl start pihole-FTL.service

4. Verify recovery email is sent when service restores

For questions or troubleshooting, refer to the files in ~/ai-agent-system/
