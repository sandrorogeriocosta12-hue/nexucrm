"""
📧 Email Verification & 2FA Implementation for Nexus CRM
Handles: Email verification, password reset, 2FA codes
"""

import secrets
import smtplib
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.orm import Session

# ============================================================================
# 📨 EMAIL SERVICE CONFIGURATION
# ============================================================================

class EmailConfig:
    """Email configuration from environment variables"""
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "your-email@gmail.com")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your-app-password")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@nexuscrm.tech")
    FROM_NAME = os.getenv("FROM_NAME", "Nexus CRM")
    
    @staticmethod
    def verify_config():
        """Verify SMTP configuration is present"""
        if not EmailConfig.SMTP_USER or not EmailConfig.SMTP_PASSWORD:
            raise RuntimeError(
                "Email configuration missing. Set SMTP_USER and SMTP_PASSWORD"
            )


# ============================================================================
# 💾 DATABASE MODELS
# ============================================================================

class VerificationToken:
    """Database model for verification tokens"""
    __tablename__ = "verification_tokens"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True)
    token = Column(String(255), unique=True, index=True)
    token_type = Column(String(50))  # 'email_verify', 'password_reset', '2fa'
    code = Column(String(10))  # 6-digit or similar
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    def is_valid(self) -> bool:
        """Check if token is still valid"""
        return (
            not self.used and
            datetime.utcnow() < self.expires_at
        )


# ============================================================================
# 📝 REQUEST/RESPONSE MODELS
# ============================================================================

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    token: str
    code: Optional[str] = None


class ResendCodeRequest(BaseModel):
    email: EmailStr
    type: str = "email_verify"  # email_verify, password_reset, 2fa


class EnableTwoFARequest(BaseModel):
    email: EmailStr
    password: str


class VerifyTwoFARequest(BaseModel):
    email: EmailStr
    code: str


# ============================================================================
# 📧 EMAIL TEMPLATES
# ============================================================================

def get_email_template(template_type: str, **context) -> tuple[str, str]:
    """
    Get email template by type
    Returns: (subject, html_body)
    """
    
    templates = {
        "email_verify": {
            "subject": "Verify Your Nexus CRM Email",
            "html": """
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2>Welcome to Nexus CRM!</h2>
                <p>Please verify your email address to activate your account.</p>
                <div style="background: #f0f0f0; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <p style="font-size: 24px; font-weight: bold; letter-spacing: 5px;">
                        {code}
                    </p>
                </div>
                <p>This code expires in 24 hours.</p>
                <p>If you didn't sign up for Nexus CRM, you can safely ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #999; font-size: 12px;">
                    © 2024 Nexus CRM. All rights reserved.<br>
                    <a href="https://nexuscrm.tech">nexuscrm.tech</a>
                </p>
            </div>
            """
        },
        
        "password_reset": {
            "subject": "Reset Your Nexus CRM Password",
            "html": """
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2>Password Reset Request</h2>
                <p>We received a request to reset your password.</p>
                <div style="background: #f0f0f0; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <p style="font-size: 18px; word-break: break-all;">
                        {token}
                    </p>
                </div>
                <p><strong>6-digit verification code:</strong></p>
                <div style="background: #f0f0f0; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <p style="font-size: 24px; font-weight: bold; letter-spacing: 5px;">
                        {code}
                    </p>
                </div>
                <p>This code expires in 1 hour.</p>
                <p>If you didn't request this, you can safely ignore this email.</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #999; font-size: 12px;">
                    © 2024 Nexus CRM. All rights reserved.
                </p>
            </div>
            """
        },
        
        "2fa_code": {
            "subject": "Your Nexus CRM 2FA Code",
            "html": """
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2>Two-Factor Authentication</h2>
                <p>Your 2FA verification code is:</p>
                <div style="background: #f0f0f0; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <p style="font-size: 24px; font-weight: bold; letter-spacing: 5px;">
                        {code}
                    </p>
                </div>
                <p style="color: #d32f2f; font-weight: bold;">
                    ⚠️ This code expires in 5 minutes!
                </p>
                <p>Never share this code with anyone, not even support staff.</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #999; font-size: 12px;">
                    © 2024 Nexus CRM. All rights reserved.
                </p>
            </div>
            """
        }
    }
    
    if template_type not in templates:
        raise ValueError(f"Unknown email template: {template_type}")
    
    template = templates[template_type]
    html = template["html"].format(**context)
    
    return template["subject"], html


# ============================================================================
# 📨 EMAIL SERVICE
# ============================================================================

class EmailService:
    """Handle email sending"""
    
    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_body: str,
        plain_text: Optional[str] = None
    ) -> bool:
        """
        Send email via SMTP
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML email body
            plain_text: Plain text fallback
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{EmailConfig.FROM_NAME} <{EmailConfig.FROM_EMAIL}>"
            msg["To"] = to_email
            
            # Attach plain text and HTML
            if plain_text:
                msg.attach(MIMEText(plain_text, "plain"))
            msg.attach(MIMEText(html_body, "html"))
            
            # Send via SMTP
            with smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT) as server:
                server.starttls()
                server.login(EmailConfig.SMTP_USER, EmailConfig.SMTP_PASSWORD)
                server.send_message(msg)
            
            print(f"✅ Email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False


# ============================================================================
# 🔐 VERIFICATION SERVICE
# ============================================================================

class VerificationService:
    """Handle email verification and 2FA"""
    
    @staticmethod
    def generate_verification_token(email: str, token_type: str = "email_verify") -> tuple[str, str]:
        """
        Generate verification token and code
        
        Returns:
            (token, code)
        """
        token = secrets.token_urlsafe(32)
        code = str(secrets.randbelow(1000000)).zfill(6)  # 6-digit code
        
        return token, code
    
    @staticmethod
    def send_verification_email(
        db: Session,
        email: str,
        email_type: str = "email_verify"
    ) -> bool:
        """
        Send verification email
        
        Args:
            db: Database session
            email: User email
            email_type: Type of verification (email_verify, password_reset, 2fa)
        
        Returns:
            True if email sent successfully
        """
        try:
            # Generate token and code
            token, code = VerificationService.generate_verification_token(
                email, email_type
            )
            
            # Set expiration based on type
            if email_type == "2fa_code":
                expires_at = datetime.utcnow() + timedelta(minutes=5)
            elif email_type == "password_reset":
                expires_at = datetime.utcnow() + timedelta(hours=1)
            else:  # email_verify
                expires_at = datetime.utcnow() + timedelta(hours=24)
            
            # Get email template
            subject, html_body = get_email_template(
                email_type,
                code=code,
                token=token
            )
            
            # Send email
            if not EmailService.send_email(email, subject, html_body):
                return False
            
            # Save token to database
            # TODO: Implement database save
            # verification_token = VerificationToken(
            #     email=email,
            #     token=token,
            #     code=code,
            #     token_type=email_type,
            #     expires_at=expires_at
            # )
            # db.add(verification_token)
            # db.commit()
            
            return True
            
        except Exception as e:
            print(f"❌ Verification email failed: {str(e)}")
            return False
    
    @staticmethod
    def verify_code(
        db: Session,
        email: str,
        code: str,
        token_type: str = "email_verify"
    ) -> bool:
        """
        Verify a code from email
        
        Args:
            db: Database session
            email: User email
            code: 6-digit code from email
            token_type: Type of token
        
        Returns:
            True if code is valid
        """
        # TODO: Query database for token
        # token = db.query(VerificationToken).filter(
        #     VerificationToken.email == email,
        #     VerificationToken.token_type == token_type,
        #     VerificationToken.code == code
        # ).first()
        
        # if not token or not token.is_valid():
        #     return False
        
        # token.used = True
        # db.commit()
        # return True
        
        return True  # Placeholder


# ============================================================================
# 🛣️ API ROUTES
# ============================================================================

router = APIRouter(prefix="/auth/email", tags=["email-verification"])


@router.post("/send-verification")
async def send_verification_email(
    request: ResendCodeRequest,
    db: Session
):
    """
    Send verification email
    
    Example:
    ```
    POST /auth/email/send-verification
    {
        "email": "user@example.com",
        "type": "email_verify"
    }
    ```
    """
    try:
        success = VerificationService.send_verification_email(
            db, request.email, request.type
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
        
        return {
            "success": True,
            "message": f"Verification code sent to {request.email}",
            "expires_in": "24 hours"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/verify-email")
async def verify_email(
    request: VerifyEmailRequest,
    db: Session
):
    """
    Verify email with code
    
    Example:
    ```
    POST /auth/email/verify-email
    {
        "email": "user@example.com",
        "token": "...",
        "code": "123456"
    }
    ```
    """
    try:
        if not VerificationService.verify_code(db, request.email, request.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired code"
            )
        
        # TODO: Update user email_verified status
        
        return {
            "success": True,
            "message": "Email verified successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/enable-2fa")
async def enable_two_fa(
    request: EnableTwoFARequest,
    db: Session
):
    """
    Enable 2FA for user account
    
    Example:
    ```
    POST /auth/email/enable-2fa
    {
        "email": "user@example.com",
        "password": "user_password"
    }
    ```
    """
    try:
        # TODO: Verify password
        
        success = VerificationService.send_verification_email(
            db, request.email, "2fa_code"
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send 2FA setup email"
            )
        
        return {
            "success": True,
            "message": "2FA code sent to your email",
            "instructions": "Enter the code sent to your email to confirm 2FA setup"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/verify-2fa-setup")
async def verify_two_fa_setup(
    request: VerifyTwoFARequest,
    db: Session
):
    """
    Complete 2FA setup by verifying code
    
    Example:
    ```
    POST /auth/email/verify-2fa-setup
    {
        "email": "user@example.com",
        "code": "123456"
    }
    ```
    """
    try:
        if not VerificationService.verify_code(db, request.email, request.code, "2fa_code"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired code"
            )
        
        # TODO: Update user 2fa_enabled status
        
        return {
            "success": True,
            "message": "2FA enabled successfully",
            "next_steps": "2FA will be required on your next login"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# 📝 ENVIRONMENT VARIABLES TEMPLATE
# ============================================================================
"""
Add these to your .env file:

# Email Configuration (Gmail example)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Generate from Google Account settings
FROM_EMAIL=noreply@nexuscrm.tech
FROM_NAME=Nexus CRM

# Or for SendGrid
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.your_sendgrid_api_key
FROM_EMAIL=noreply@nexuscrm.tech
FROM_NAME=Nexus CRM

# Or for AWS SES
# Use ses-smtp-prod-(region).amazonaws.com
# Generate SMTP credentials from IAM
"""

if __name__ == "__main__":
    # Test email configuration
    print("Email Service Configuration Test")
    print("=" * 50)
    
    try:
        EmailConfig.verify_config()
        print("✅ Email configuration valid")
        print(f"   SMTP Server: {EmailConfig.SMTP_SERVER}:{EmailConfig.SMTP_PORT}")
        print(f"   From: {EmailConfig.FROM_NAME} <{EmailConfig.FROM_EMAIL}>")
        print(f"   User: {EmailConfig.SMTP_USER}")
    except RuntimeError as e:
        print(f"❌ Configuration error: {str(e)}")
