#!/bin/bash
#
# Gmail App Password Setup Script
# Run this to configure the Gmail app password for email alerts
#

echo "==================================================================="
echo "Gmail App Password Setup for Pi-hole Monitoring"
echo "==================================================================="
echo ""
echo "To send email alerts, you need a Gmail App Password."
echo ""
echo "Steps to generate one:"
echo "1. Go to https://myaccount.google.com/apppasswords"
echo "2. Sign in to jupiterserver45@gmail.com"
echo "3. Create a new app password (name it 'Pi-hole Monitor')"
echo "4. Copy the 16-character password"
echo ""
echo -n "Enter your Gmail App Password (or press Enter to skip): "
read -s APP_PASSWORD
echo ""

if [ -z "$APP_PASSWORD" ]; then
    echo "Skipped. You can run this script again later."
    exit 0
fi

# Update .msmtprc with the password
sed -i "s/password.*/password       $APP_PASSWORD/" ~/.msmtprc

echo ""
echo "Password configured!"
echo ""
echo "Testing email configuration..."
echo "Subject: Pi-hole Monitor Test Email
From: jupiterserver45@gmail.com
To: skitles1994@gmail.com

This is a test email from your Pi-hole monitoring system.

If you receive this, email alerts are working correctly!

Hostname: $(hostname)
Time: $(date)
" | msmtp -a gmail skitles1994@gmail.com

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Test email sent successfully!"
    echo "Check skitles1994@gmail.com for the test message."
else
    echo ""
    echo "✗ Failed to send test email."
    echo "Check ~/.msmtp.log for details"
    cat ~/.msmtp.log 2>/dev/null | tail -10
fi
