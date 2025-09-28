"""
SendGrid email service for PhotoVault
Based on the python_sendgrid blueprint integration
"""
import os
import sys
import logging
from typing import Optional

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    # Handle case where sendgrid is not installed
    SendGridAPIClient = None
    Mail = Email = To = Content = None
    SENDGRID_AVAILABLE = False

logger = logging.getLogger(__name__)


class SendGridEmailService:
    """SendGrid email service for PhotoVault"""
    
    def __init__(self):
        self.api_key = os.environ.get('SENDGRID_API_KEY')
        self.from_email = os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@photovault.com')
        
        if not self.api_key:
            logger.warning("SENDGRID_API_KEY not found in environment variables")
            self.client = None
        elif not SENDGRID_AVAILABLE:
            logger.error("SendGrid library not installed. Install with: pip install sendgrid")
            self.client = None
        else:
            try:
                if SendGridAPIClient:
                    self.client = SendGridAPIClient(self.api_key)
                    logger.info("SendGrid client initialized successfully")
                else:
                    logger.error("SendGridAPIClient class not available")
                    self.client = None
            except Exception as e:
                logger.error(f"Failed to initialize SendGrid client: {e}")
                self.client = None
    
    def is_available(self) -> bool:
        """Check if SendGrid service is available"""
        return self.client is not None
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> bool:
        """
        Send email using SendGrid
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content
            from_email: Sender email (defaults to configured from_email)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.is_available():
            logger.error("SendGrid service not available")
            return False
        
        if not (html_content or text_content):
            logger.error("Either html_content or text_content must be provided")
            return False
        
        try:
            sender_email = from_email or self.from_email
            
            # Create message with both HTML and text content
            if not SENDGRID_AVAILABLE or not Mail or not Email or not To:
                logger.error("SendGrid classes not available")
                return False
                
            message = Mail(
                from_email=Email(sender_email),
                to_emails=To(to_email),
                subject=subject,
                html_content=html_content,
                plain_text_content=text_content
            )
            
            # Send the email
            if not self.client:
                logger.error("SendGrid client not initialized")
                return False
                
            response = self.client.send(message)
            
            # Check response status
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email to {to_email}. Status: {response.status_code}")
                return False
                
        except Exception as e:
            error_msg = str(e)
            
            # Enhanced error reporting for common SendGrid issues
            if "403" in error_msg or "Forbidden" in error_msg:
                logger.error(f"SendGrid 403 Forbidden Error - Common fixes needed:")
                logger.error(f"1. Check API key permissions in SendGrid dashboard")
                logger.error(f"2. Verify sender email '{sender_email}' in SendGrid")
                logger.error(f"3. Ensure API key has 'Mail Send' permissions")
                logger.error(f"Original error: {error_msg}")
                
                # Additional Railway-specific diagnostics
                if os.environ.get('RAILWAY_ENVIRONMENT'):
                    logger.error("Railway deployment detected - verify environment variables:")
                    logger.error(f"- SENDGRID_API_KEY configured: {bool(self.api_key)}")
                    logger.error(f"- SENDGRID_FROM_EMAIL: {self.from_email}")
                    
            elif "401" in error_msg or "Unauthorized" in error_msg:
                logger.error(f"SendGrid 401 Unauthorized - API key invalid or missing")
                logger.error(f"Check SENDGRID_API_KEY environment variable")
                
            logger.error(f"Exception while sending email to {to_email}: {error_msg}")
            return False


# Global instance
sendgrid_service = SendGridEmailService()


def send_password_reset_email(user, token: str) -> bool:
    """Send password reset email using SendGrid"""
    from flask import url_for
    
    try:
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        
        subject = "PhotoVault - Password Reset Request"
        html_content = f"""
        <html>
        <body>
            <h2>PhotoVault - Password Reset</h2>
            <p>Hello {user.username},</p>
            
            <p>You have requested a password reset for your PhotoVault account.</p>
            
            <p><a href="{reset_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Your Password</a></p>
            
            <p>Or copy and paste this link: {reset_url}</p>
            
            <p><strong>This link will expire in 1 hour.</strong></p>
            
            <p>If you did not request this password reset, please ignore this email.</p>
            
            <hr>
            <p>Best regards,<br>PhotoVault Team</p>
        </body>
        </html>
        """
        
        text_content = f"""Hello {user.username},

You have requested a password reset for your PhotoVault account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you did not request this password reset, please ignore this email.

Best regards,
PhotoVault Team"""
        
        return sendgrid_service.send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False


def send_family_invitation_email(email: str, invitation_token: str, vault_name: str, inviter_name: str) -> bool:
    """Send family vault invitation email using SendGrid"""
    from flask import url_for
    
    try:
        invitation_url = url_for('family.accept_invitation', token=invitation_token, _external=True)
        
        subject = f"PhotoVault - Invitation to join '{vault_name}' family vault"
        html_content = f"""
        <html>
        <body>
            <h2>PhotoVault - Family Vault Invitation</h2>
            <p>Hello!</p>
            
            <p>{inviter_name} has invited you to join the family vault "<strong>{vault_name}</strong>" on PhotoVault.</p>
            
            <p>Family vaults allow you to share photos and memories with your loved ones in a secure, private space.</p>
            
            <p><a href="{invitation_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Accept Invitation</a></p>
            
            <p>Or copy and paste this link: {invitation_url}</p>
            
            <p><strong>This invitation will expire in 7 days.</strong></p>
            
            <p>If you don't have a PhotoVault account yet, you'll be able to create one when you click the link above.</p>
            
            <hr>
            <p>Best regards,<br>PhotoVault Team</p>
        </body>
        </html>
        """
        
        text_content = f"""Hello!

{inviter_name} has invited you to join the family vault "{vault_name}" on PhotoVault.

Family vaults allow you to share photos and memories with your loved ones in a secure, private space.

Click the link below to accept the invitation:
{invitation_url}

This invitation will expire in 7 days.

If you don't have a PhotoVault account yet, you'll be able to create one when you click the link above.

Best regards,
PhotoVault Team"""
        
        return sendgrid_service.send_email(
            to_email=email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        
    except Exception as e:
        logger.error(f"Failed to send family invitation email to {email}: {str(e)}")
        return False