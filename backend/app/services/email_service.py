"""
Email service for AIRIES AI platform
Handles sending emails for verification, password reset, notifications, etc.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
import logging

from ..core.config import settings
from ..models.user import User

logger = logging.getLogger(__name__)


class EmailService:
    """Service class for email operations"""
    
    def __init__(self):
        self.smtp_server = getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', '')
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        self.from_email = getattr(settings, 'FROM_EMAIL', 'noreply@airies.ai')
        self.from_name = getattr(settings, 'FROM_NAME', 'AIRIES AI')
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    async def send_verification_email(self, user: User) -> bool:
        """Send email verification email"""
        if not user.verification_token:
            logger.error(f"No verification token for user {user.email}")
            return False
        
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{user.verification_token}"
        
        subject = "Verify your AIRIES AI account"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verify Your Account</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2563eb;">AIRIES AI</h1>
                </div>
                
                <h2>Welcome to AIRIES AI, {user.first_name}!</h2>
                
                <p>Thank you for signing up for AIRIES AI. To complete your registration and start building AI agents, please verify your email address by clicking the button below:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Verify Email Address
                    </a>
                </div>
                
                <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #666;">{verification_url}</p>
                
                <p>This verification link will expire in 24 hours.</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                
                <p style="font-size: 14px; color: #666;">
                    If you didn't create an account with AIRIES AI, you can safely ignore this email.
                </p>
                
                <p style="font-size: 14px; color: #666;">
                    Best regards,<br>
                    The AIRIES AI Team
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to AIRIES AI, {user.first_name}!
        
        Thank you for signing up for AIRIES AI. To complete your registration and start building AI agents, please verify your email address by visiting this link:
        
        {verification_url}
        
        This verification link will expire in 24 hours.
        
        If you didn't create an account with AIRIES AI, you can safely ignore this email.
        
        Best regards,
        The AIRIES AI Team
        """
        
        return await self.send_email(user.email, subject, html_content, text_content)
    
    async def send_password_reset_email(self, user: User) -> bool:
        """Send password reset email"""
        if not user.password_reset_token:
            logger.error(f"No password reset token for user {user.email}")
            return False
        
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{user.password_reset_token}"
        
        subject = "Reset your AIRIES AI password"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Reset Your Password</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2563eb;">AIRIES AI</h1>
                </div>
                
                <h2>Password Reset Request</h2>
                
                <p>Hi {user.first_name},</p>
                
                <p>We received a request to reset your password for your AIRIES AI account. Click the button below to create a new password:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background-color: #dc2626; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                
                <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #666;">{reset_url}</p>
                
                <p>This password reset link will expire in 1 hour.</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                
                <p style="font-size: 14px; color: #666;">
                    If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.
                </p>
                
                <p style="font-size: 14px; color: #666;">
                    Best regards,<br>
                    The AIRIES AI Team
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset Request
        
        Hi {user.first_name},
        
        We received a request to reset your password for your AIRIES AI account. Visit this link to create a new password:
        
        {reset_url}
        
        This password reset link will expire in 1 hour.
        
        If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.
        
        Best regards,
        The AIRIES AI Team
        """
        
        return await self.send_email(user.email, subject, html_content, text_content)
    
    async def send_welcome_email(self, user: User) -> bool:
        """Send welcome email after email verification"""
        subject = "Welcome to AIRIES AI - Let's build your first AI agent!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to AIRIES AI</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2563eb;">AIRIES AI</h1>
                </div>
                
                <h2>Welcome to AIRIES AI, {user.first_name}! 🎉</h2>
                
                <p>Your account has been successfully verified and you're now ready to start building intelligent AI agents!</p>
                
                <h3>What you can do with AIRIES AI:</h3>
                <ul>
                    <li>🤖 Create voice and chat AI agents</li>
                    <li>📞 Connect agents to phone systems</li>
                    <li>🧠 Build knowledge bases with RAG</li>
                    <li>📊 Monitor performance and analytics</li>
                    <li>🔧 Customize with advanced tools</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{settings.FRONTEND_URL}/dashboard" 
                       style="background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Go to Dashboard
                    </a>
                </div>
                
                <h3>Getting Started:</h3>
                <ol>
                    <li>Create your first AI agent</li>
                    <li>Configure voice and language settings</li>
                    <li>Test your agent in the playground</li>
                    <li>Deploy and start taking calls!</li>
                </ol>
                
                <p>You started with <strong>{user.credits} free credits</strong> to explore all features. Need help? Check out our documentation or contact support.</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                
                <p style="font-size: 14px; color: #666;">
                    Happy building!<br>
                    The AIRIES AI Team
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to AIRIES AI, {user.first_name}!
        
        Your account has been successfully verified and you're now ready to start building intelligent AI agents!
        
        What you can do with AIRIES AI:
        - Create voice and chat AI agents
        - Connect agents to phone systems  
        - Build knowledge bases with RAG
        - Monitor performance and analytics
        - Customize with advanced tools
        
        Getting Started:
        1. Create your first AI agent
        2. Configure voice and language settings
        3. Test your agent in the playground
        4. Deploy and start taking calls!
        
        You started with {user.credits} free credits to explore all features.
        
        Visit your dashboard: {settings.FRONTEND_URL}/dashboard
        
        Happy building!
        The AIRIES AI Team
        """
        
        return await self.send_email(user.email, subject, html_content, text_content)
    
    async def send_low_credits_warning(self, user: User, remaining_credits: int) -> bool:
        """Send low credits warning email"""
        subject = "AIRIES AI - Low Credits Warning"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Low Credits Warning</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #2563eb;">AIRIES AI</h1>
                </div>
                
                <h2>⚠️ Low Credits Warning</h2>
                
                <p>Hi {user.first_name},</p>
                
                <p>Your AIRIES AI account is running low on credits. You currently have <strong>{remaining_credits} credits</strong> remaining.</p>
                
                <p>To avoid service interruption, consider upgrading your plan or purchasing additional credits.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{settings.FRONTEND_URL}/billing" 
                       style="background-color: #2563eb; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                        Manage Billing
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666;">
                    Best regards,<br>
                    The AIRIES AI Team
                </p>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(user.email, subject, html_content)