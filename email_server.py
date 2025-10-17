"""
Email-based AI Agent
Send emails to your server's inbox and get AI responses back via email
Only responds to whitelisted email addresses
"""

import asyncio
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import imaplib
import os
import logging
from agent import AIAgent
import time
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmailAIServer:
    def __init__(self):
        # Email credentials (Gmail recommended)
        self.email = os.getenv('EMAIL_ADDRESS')
        self.password = os.getenv('EMAIL_PASSWORD')  # App password for Gmail
        
        # Authorized email addresses (comma-separated list)
        authorized = os.getenv('AUTHORIZED_EMAILS', '')
        self.authorized_emails = [e.strip().lower() for e in authorized.split(',') if e.strip()]
        
        if not self.authorized_emails:
            raise ValueError("AUTHORIZED_EMAILS must contain at least one email address")
        
        # Email servers (Gmail by default, but configurable)
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
        self.imap_port = int(os.getenv('IMAP_PORT', '993'))
        
        # Agent instance
        api_key = os.getenv('ANTHROPIC_API_KEY')
        
        # Create log file for email interactions
        log_dir = Path.home() / "ai-agent-logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        self.agent = AIAgent(api_key=api_key, log_file=log_file)
        
        # Track processed message IDs
        self.processed_ids = set()
        
        logger.info(f"Email AI Server initialized")
        logger.info(f"Monitoring inbox: {self.email}")
        logger.info(f"Authorized emails: {', '.join(self.authorized_emails)}")
    
    def send_email(self, to_address, subject, message):
        """Send email response"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_address
            msg['Subject'] = f"Re: {subject}" if subject else "AI Agent Response"
            
            msg.attach(MIMEText(message, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to_address}: {message[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def extract_email_address(self, from_header):
        """Extract clean email address from 'From' header"""
        # Handle formats like "Name <email@domain.com>" or just "email@domain.com"
        if '<' in from_header and '>' in from_header:
            start = from_header.index('<') + 1
            end = from_header.index('>')
            return from_header[start:end].strip().lower()
        return from_header.strip().lower()
    
    def is_authorized(self, sender_email):
        """Check if sender is in authorized list"""
        sender = self.extract_email_address(sender_email)
        authorized = sender in self.authorized_emails
        
        if not authorized:
            logger.warning(f"Unauthorized email from: {sender}")
        
        return authorized
    
    def check_inbox(self):
        """Check for new emails from authorized senders"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email, self.password)
            mail.select('inbox')
            
            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')
            
            if status != 'OK':
                return []
            
            new_messages = []
            
            for num in messages[0].split():
                status, data = mail.fetch(num, '(RFC822)')
                if status != 'OK':
                    continue
                
                email_message = email.message_from_bytes(data[0][1])
                
                # Get sender
                sender = email_message['From']
                
                # Check authorization
                if not self.is_authorized(sender):
                    # Mark as read but don't process
                    mail.store(num, '+FLAGS', '\\Seen')
                    continue
                
                # Get message ID to avoid duplicates
                msg_id = email_message['Message-ID']
                if msg_id in self.processed_ids:
                    continue
                
                # Get subject
                subject = email_message['Subject'] or ''
                
                # Extract message body
                body = ''
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == 'text/plain':
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = email_message.get_payload(decode=True).decode()
                
                # Clean up the message
                body = body.strip()
                
                if body:
                    new_messages.append({
                        'id': msg_id,
                        'body': body,
                        'subject': subject,
                        'sender': self.extract_email_address(sender)
                    })
                    self.processed_ids.add(msg_id)
                    logger.info(f"Received email from {sender}: {body[:50]}...")
            
            mail.close()
            mail.logout()
            
            return new_messages
            
        except Exception as e:
            logger.error(f"Failed to check inbox: {e}")
            return []
    
    def process_message(self, message_text):
        """Process message with agent"""
        try:
            if message_text.lower().strip() == 'reset':
                self.agent.reset_conversation()
                return "✓ Conversation reset"
            
            response = self.agent.chat(message_text)
            return response
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"Error: {str(e)}"
    
    async def run(self):
        """Main loop - check inbox and respond"""
        logger.info("Starting email AI server...")
        logger.info("Send emails to this address from authorized accounts")
        logger.info("Press Ctrl+C to stop")
        
        while True:
            try:
                # Check for new messages
                messages = self.check_inbox()
                
                for msg in messages:
                    logger.info(f"Processing from {msg['sender']}: {msg['body'][:50]}...")
                    
                    # Get response from agent
                    response = self.process_message(msg['body'])
                    
                    # Send response via email
                    self.send_email(msg['sender'], msg['subject'], response)
                
                # Wait before checking again (don't spam the email server)
                await asyncio.sleep(15)  # Check every 15 seconds
                
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(30)  # Wait longer on error

if __name__ == "__main__":
    # Validate environment
    required_vars = [
        'EMAIL_ADDRESS',
        'EMAIL_PASSWORD',
        'AUTHORIZED_EMAILS',
        'ANTHROPIC_API_KEY'
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"❌ Error: Missing environment variables: {missing}")
        print("\nRequired configuration in .env:")
        print("  EMAIL_ADDRESS=your.email@gmail.com")
        print("  EMAIL_PASSWORD=your-app-password")
        print("  AUTHORIZED_EMAILS=your.personal@gmail.com,another@email.com")
        print("  ANTHROPIC_API_KEY=sk-ant-...")
        print("\nSee EMAIL-SETUP.md for instructions")
        exit(1)
    
    server = EmailAIServer()
    asyncio.run(server.run())
