import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from pathlib import Path
from jinja2 import Template
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.attorney_template_path = Path(__file__).parent / "email_attorney_template.html"
        self.lead_template_path = Path(__file__).parent / "email_lead_confirmation_template.html"

    async def send_lead_email(self, lead_data: dict) -> bool:
        """Send emails to both attorney and lead"""
        try:
            # Send to attorney
            attorney_success = await self._send_attorney_email(lead_data)
            
            # Send to lead
            lead_success = await self._send_lead_confirmation(lead_data)
            
            if attorney_success and lead_success:
                logger.info(f"Both emails sent for: {lead_data.get('email')}")
                return True
            else:
                logger.warning(f"Partial email success for: {lead_data.get('email')}")
                return False
            
        except Exception as e:
            logger.error(f"Email failed: {e}")
            return False
    
    async def _send_attorney_email(self, lead_data: dict) -> bool:
        """Send notification to attorney"""
        try:
            template_content = self.attorney_template_path.read_text(encoding='utf-8')
            template = Template(template_content)
            
            html_body = template.render(
                first_name=lead_data.get('first_name', ''),
                last_name=lead_data.get('last_name', ''),
                email=lead_data.get('email', ''),
                resume_path=lead_data.get('resume_path', 'Not provided'),
                created_at=lead_data.get('created_at', '')
            )
            
            message = MIMEMultipart("alternative")
            message["Subject"] = f"New Lead: {lead_data.get('first_name')} {lead_data.get('last_name')}"
            message["From"] = settings.FROM_EMAIL
            message["To"] = settings.ATTORNEY_EMAIL
            message.attach(MIMEText(html_body, "html"))
            
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                start_tls=True,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
            )
            
            logger.info(f"Attorney email sent to: {settings.ATTORNEY_EMAIL}")
            return True
            
        except Exception as e:
            logger.error(f"Attorney email failed: {e}")
            return False
    
    async def _send_lead_confirmation(self, lead_data: dict) -> bool:
        """Send confirmation to lead"""
        try:
            template_content = self.lead_template_path.read_text(encoding='utf-8')
            template = Template(template_content)
            
            html_body = template.render(
                first_name=lead_data.get('first_name', ''),
                last_name=lead_data.get('last_name', '')
            )
            
            message = MIMEMultipart("alternative")
            message["Subject"] = "Thank you for choosing Alma Legal"
            message["From"] = settings.FROM_EMAIL
            message["To"] = lead_data.get('email', '')
            message.attach(MIMEText(html_body, "html"))
            
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                start_tls=True,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
            )
            
            logger.info(f"Lead confirmation sent to: {lead_data.get('email')}")
            return True
            
        except Exception as e:
            logger.error(f"Lead confirmation failed: {e}")
            return False

email_service = EmailService()