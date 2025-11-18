"""
Email service.
Handles email sending via SendGrid/SMTP and template rendering.
"""

import os
from datetime import datetime
from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings


class EmailService:
    """
    Servicio de envío de emails.

    Integra con SendGrid para envío de emails y usa Jinja2
    para rendering de templates HTML.

    Para desarrollo sin API key de SendGrid, simplemente loggea
    los emails en lugar de enviarlos.
    """

    def __init__(self):
        """Initialize email service with SendGrid client and Jinja2 environment."""
        # SendGrid client (opcional para desarrollo)
        self.sendgrid_client = None
        if hasattr(settings, 'SENDGRID_API_KEY') and settings.SENDGRID_API_KEY:
            try:
                from sendgrid import SendGridAPIClient
                self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
            except ImportError:
                print("[WARNING] SendGrid library not installed. Emails will be logged only.")

        # Jinja2 environment para templates
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        to_name: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Enviar email usando SendGrid.

        En modo desarrollo (sin SENDGRID_API_KEY), solo loggea el email.

        Args:
            to_email: Email del destinatario
            subject: Asunto del email
            html_content: Contenido HTML del email
            to_name: Nombre del destinatario (opcional)

        Returns:
            Tuple (success: bool, error_message: str | None)
        """
        # Modo desarrollo: solo log
        if not self.sendgrid_client:
            print(f"\n{'='*60}")
            print(f"[EMAIL] Development Mode - Email not sent")
            print(f"{'='*60}")
            print(f"To: {to_email} ({to_name or 'N/A'})")
            print(f"Subject: {subject}")
            print(f"{'='*60}\n")
            return True, None

        # Modo producción: enviar con SendGrid
        try:
            from sendgrid.helpers.mail import Mail

            from_email = getattr(settings, 'FROM_EMAIL', 'noreply@habilitat.com')
            from_name = getattr(settings, 'FROM_NAME', 'Habilitat')

            message = Mail(
                from_email=(from_email, from_name),
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )

            response = self.sendgrid_client.send(message)

            # SendGrid returns 202 for successful queue
            if response.status_code in [200, 201, 202]:
                return True, None
            else:
                error_msg = f"SendGrid error: {response.status_code}"
                print(f"[EMAIL ERROR] {error_msg}")
                return False, error_msg

        except Exception as e:
            error_msg = str(e)
            print(f"[EMAIL ERROR] {error_msg}")
            return False, error_msg

    def render_template(
        self,
        template_name: str,
        data: dict,
        tenant_branding: Optional[dict] = None
    ) -> str:
        """
        Renderizar template de email con datos y branding del tenant.

        Los templates pueden usar las siguientes variables:
        - Todas las variables en `data`
        - `branding`: diccionario con logo, colores, etc.
        - `app_name`: nombre de la aplicación
        - `current_year`: año actual

        Args:
            template_name: Nombre del archivo de template (ej: "welcome.html")
            data: Variables para pasar al template
            tenant_branding: Branding del tenant (logo, colores)

        Returns:
            HTML renderizado

        Raises:
            TemplateNotFound: Si el template no existe
        """
        # Construir contexto con datos, branding y variables globales
        context = {
            **data,
            "branding": tenant_branding or {},
            "app_name": settings.APP_NAME,
            "current_year": datetime.utcnow().year
        }

        # Renderizar template
        template = self.jinja_env.get_template(template_name)
        return template.render(**context)


# Singleton instance
email_service = EmailService()
