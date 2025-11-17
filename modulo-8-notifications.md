# Módulo 8: Notifications (Sistema de Notificaciones)

## Descripción

El módulo Notifications maneja el envío de emails y notificaciones de la plataforma: bienvenida, invitaciones, recordatorios de onboarding, verificación de email, reset de contraseña, etc.

**Límite de líneas:** ~2000-3000 líneas

## Responsabilidades

1. Envío de emails transaccionales
2. Templates de emails con branding del tenant
3. Cola de notificaciones (background tasks)
4. Tracking de emails enviados
5. Tipos de notificación:
   - Bienvenida al tenant
   - Verificación de email
   - Reset de contraseña
   - Invitación de usuario
   - Asignación de onboarding
   - Recordatorios de onboarding pendiente
   - Completación de onboarding

## Estructura de Archivos

```
app/notifications/
├── __init__.py
├── models.py              # EmailLog
├── schemas.py             # Request/Response schemas
├── service.py             # Lógica de envío
├── router.py              # Endpoints (admin para ver logs)
├── email_service.py       # Integración con SendGrid/SMTP
├── templates/             # Email templates HTML
│   ├── base.html
│   ├── welcome.html
│   ├── invitation.html
│   ├── password_reset.html
│   ├── onboarding_assigned.html
│   └── onboarding_reminder.html
└── utils.py               # Template rendering
```

## 1. Modelos (models.py)

### EmailLog Model

```python
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.models import BaseModel, TimestampMixin, TenantMixin

class EmailLog(BaseModel, TimestampMixin, TenantMixin):
    """
    Log de emails enviados para tracking y debugging
    """
    __tablename__ = "email_logs"

    # Recipient
    to_email = Column(String(255), nullable=False, index=True)
    to_name = Column(String(200), nullable=True)

    # Subject & type
    subject = Column(String(500), nullable=False)
    email_type = Column(String(50), nullable=False)  # welcome, invitation, password_reset, etc.

    # Content
    template_name = Column(String(100), nullable=True)
    template_data = Column(JSON, nullable=True)  # Variables usadas en el template

    # Status
    is_sent = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # External ID (de SendGrid, etc.)
    external_id = Column(String(200), nullable=True)

    # Related entities (opcional)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<EmailLog {self.to_email} ({self.email_type})>"
```

## 2. Schemas (schemas.py)

### Request/Response Schemas

```python
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.core.schemas import BaseSchema, PaginationParams

class SendEmailRequest(BaseModel):
    """Request manual de envío de email (admin)"""
    to_email: EmailStr
    to_name: str | None = None
    subject: str
    template_name: str
    template_data: dict = {}

class EmailLogResponse(BaseSchema):
    id: int
    to_email: str
    to_name: str | None
    subject: str
    email_type: str
    is_sent: bool
    sent_at: datetime | None
    error_message: str | None
    created_at: datetime

class EmailLogFilterParams(PaginationParams):
    email_type: str | None = None
    is_sent: bool | None = None
    to_email: str | None = None
```

## 3. Email Service (email_service.py)

### EmailService Class

```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.core.config import settings
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os

class EmailService:
    """Servicio de envío de emails"""

    def __init__(self):
        self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY) if settings.SENDGRID_API_KEY else None

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
        to_name: str | None = None
    ) -> tuple[bool, str | None]:
        """
        Enviar email usando SendGrid

        Returns:
            (success, error_message)
        """
        if not self.sendgrid_client:
            # Development: solo log
            print(f"[EMAIL] To: {to_email}, Subject: {subject}")
            return True, None

        try:
            message = Mail(
                from_email=settings.FROM_EMAIL,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )

            response = self.sendgrid_client.send(message)

            if response.status_code in [200, 201, 202]:
                return True, None
            else:
                return False, f"SendGrid error: {response.status_code}"

        except Exception as e:
            return False, str(e)

    def render_template(self, template_name: str, data: dict, tenant_branding: dict | None = None) -> str:
        """
        Renderizar template de email con datos y branding del tenant

        Args:
            template_name: Nombre del archivo de template (e.g., "welcome.html")
            data: Variables para el template
            tenant_branding: Branding del tenant (logo, colores)

        Returns:
            HTML renderizado
        """
        # Agregar branding al contexto
        context = {
            **data,
            "branding": tenant_branding or {},
            "app_name": settings.APP_NAME,
            "current_year": datetime.utcnow().year
        }

        template = self.jinja_env.get_template(template_name)
        return template.render(**context)

email_service = EmailService()
```

## 4. Service (service.py)

### NotificationService Class

```python
from sqlalchemy.orm import Session
from app.notifications.models import EmailLog
from app.notifications.email_service import email_service
from app.tenants.models import Tenant
from datetime import datetime

class NotificationService:
    """Servicio de gestión de notificaciones"""

    @staticmethod
    async def send_welcome_email(
        db: Session,
        user_email: str,
        user_name: str,
        tenant_id: int,
        tenant: Tenant
    ) -> bool:
        """
        Enviar email de bienvenida al tenant

        Template: welcome.html
        """
        # Obtener branding del tenant
        branding = tenant.branding.to_theme_dict() if tenant.branding else None

        # Renderizar template
        html = email_service.render_template(
            "welcome.html",
            {
                "user_name": user_name,
                "tenant_name": tenant.name,
            },
            branding
        )

        # Enviar email
        success, error = await email_service.send_email(
            to_email=user_email,
            subject=f"Bienvenido a {tenant.name}",
            html_content=html,
            to_name=user_name
        )

        # Log
        log = EmailLog(
            tenant_id=tenant_id,
            to_email=user_email,
            to_name=user_name,
            subject=f"Bienvenido a {tenant.name}",
            email_type="welcome",
            template_name="welcome.html",
            is_sent=success,
            sent_at=datetime.utcnow() if success else None,
            error_message=error
        )
        db.add(log)
        db.commit()

        return success

    @staticmethod
    async def send_invitation_email(
        db: Session,
        invitation_email: str,
        invitation_token: str,
        inviter_name: str,
        tenant_id: int,
        tenant: Tenant
    ) -> bool:
        """
        Enviar email de invitación a nuevo usuario

        Template: invitation.html
        """
        branding = tenant.branding.to_theme_dict() if tenant.branding else None

        # Link de aceptación (debería apuntar al frontend)
        accept_url = f"https://app.habilitat.com/accept-invitation?token={invitation_token}"

        html = email_service.render_template(
            "invitation.html",
            {
                "tenant_name": tenant.name,
                "inviter_name": inviter_name,
                "accept_url": accept_url
            },
            branding
        )

        success, error = await email_service.send_email(
            to_email=invitation_email,
            subject=f"Invitación a {tenant.name}",
            html_content=html
        )

        log = EmailLog(
            tenant_id=tenant_id,
            to_email=invitation_email,
            subject=f"Invitación a {tenant.name}",
            email_type="invitation",
            template_name="invitation.html",
            is_sent=success,
            sent_at=datetime.utcnow() if success else None,
            error_message=error
        )
        db.add(log)
        db.commit()

        return success

    @staticmethod
    async def send_password_reset_email(
        db: Session,
        user_email: str,
        user_name: str,
        reset_token: str,
        tenant_id: int | None = None
    ) -> bool:
        """
        Enviar email de reset de contraseña

        Template: password_reset.html
        """
        # Link de reset
        reset_url = f"https://app.habilitat.com/reset-password?token={reset_token}"

        html = email_service.render_template(
            "password_reset.html",
            {
                "user_name": user_name,
                "reset_url": reset_url
            }
        )

        success, error = await email_service.send_email(
            to_email=user_email,
            subject="Recuperación de contraseña",
            html_content=html,
            to_name=user_name
        )

        log = EmailLog(
            tenant_id=tenant_id,
            to_email=user_email,
            to_name=user_name,
            subject="Recuperación de contraseña",
            email_type="password_reset",
            template_name="password_reset.html",
            is_sent=success,
            sent_at=datetime.utcnow() if success else None,
            error_message=error
        )
        db.add(log)
        db.commit()

        return success

    @staticmethod
    async def send_onboarding_assigned_email(
        db: Session,
        user_email: str,
        user_name: str,
        flow_title: str,
        tenant_id: int,
        tenant: Tenant
    ) -> bool:
        """
        Enviar email cuando se asigna un onboarding

        Template: onboarding_assigned.html
        """
        branding = tenant.branding.to_theme_dict() if tenant.branding else None

        dashboard_url = f"https://{tenant.subdomain}.habilitat.com/dashboard"

        html = email_service.render_template(
            "onboarding_assigned.html",
            {
                "user_name": user_name,
                "flow_title": flow_title,
                "tenant_name": tenant.name,
                "dashboard_url": dashboard_url
            },
            branding
        )

        success, error = await email_service.send_email(
            to_email=user_email,
            subject=f"Nuevo onboarding: {flow_title}",
            html_content=html,
            to_name=user_name
        )

        log = EmailLog(
            tenant_id=tenant_id,
            to_email=user_email,
            to_name=user_name,
            subject=f"Nuevo onboarding: {flow_title}",
            email_type="onboarding_assigned",
            template_name="onboarding_assigned.html",
            is_sent=success,
            sent_at=datetime.utcnow() if success else None,
            error_message=error
        )
        db.add(log)
        db.commit()

        return success

    @staticmethod
    async def send_onboarding_reminder_email(
        db: Session,
        user_email: str,
        user_name: str,
        flow_title: str,
        progress_percentage: int,
        tenant_id: int,
        tenant: Tenant
    ) -> bool:
        """
        Enviar recordatorio de onboarding pendiente

        Template: onboarding_reminder.html
        """
        branding = tenant.branding.to_theme_dict() if tenant.branding else None

        dashboard_url = f"https://{tenant.subdomain}.habilitat.com/dashboard"

        html = email_service.render_template(
            "onboarding_reminder.html",
            {
                "user_name": user_name,
                "flow_title": flow_title,
                "progress_percentage": progress_percentage,
                "tenant_name": tenant.name,
                "dashboard_url": dashboard_url
            },
            branding
        )

        success, error = await email_service.send_email(
            to_email=user_email,
            subject=f"Recordatorio: {flow_title}",
            html_content=html,
            to_name=user_name
        )

        log = EmailLog(
            tenant_id=tenant_id,
            to_email=user_email,
            to_name=user_name,
            subject=f"Recordatorio: {flow_title}",
            email_type="onboarding_reminder",
            template_name="onboarding_reminder.html",
            is_sent=success,
            sent_at=datetime.utcnow() if success else None,
            error_message=error
        )
        db.add(log)
        db.commit()

        return success

    @staticmethod
    async def send_email_verification(
        db: Session,
        user_email: str,
        user_name: str,
        verification_token: str,
        tenant_id: int | None = None
    ) -> bool:
        """
        Enviar email de verificación

        Template: email_verification.html
        """
        verify_url = f"https://app.habilitat.com/verify-email?token={verification_token}"

        html = email_service.render_template(
            "email_verification.html",
            {
                "user_name": user_name,
                "verify_url": verify_url
            }
        )

        success, error = await email_service.send_email(
            to_email=user_email,
            subject="Verifica tu email",
            html_content=html,
            to_name=user_name
        )

        log = EmailLog(
            tenant_id=tenant_id,
            to_email=user_email,
            to_name=user_name,
            subject="Verifica tu email",
            email_type="email_verification",
            template_name="email_verification.html",
            is_sent=success,
            sent_at=datetime.utcnow() if success else None,
            error_message=error
        )
        db.add(log)
        db.commit()

        return success

    @staticmethod
    def get_email_logs(
        db: Session,
        tenant_id: int,
        filters: schemas.EmailLogFilterParams
    ) -> tuple[list[EmailLog], int]:
        """Obtener logs de emails con filtros"""
        query = db.query(EmailLog).filter(EmailLog.tenant_id == tenant_id)

        if filters.email_type:
            query = query.filter(EmailLog.email_type == filters.email_type)

        if filters.is_sent is not None:
            query = query.filter(EmailLog.is_sent == filters.is_sent)

        if filters.to_email:
            query = query.filter(EmailLog.to_email.ilike(f"%{filters.to_email}%"))

        total = query.count()

        logs = query.order_by(EmailLog.created_at.desc()).offset(filters.offset).limit(filters.page_size).all()

        return logs, total
```

## 5. Router (router.py)

### Notification Endpoints

```python
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.schemas import PaginatedResponse
from app.core.enums import UserRole
from app.notifications import schemas, service
from app.auth.dependencies import require_role
from app.tenants.models import Tenant
from app.tenants.dependencies import get_current_tenant
from app.users.models import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("/email-logs", response_model=PaginatedResponse[schemas.EmailLogResponse])
async def get_email_logs(
    filters: schemas.EmailLogFilterParams = Depends(),
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Obtener logs de emails enviados

    - Solo TENANT_ADMIN
    """
    logs, total = service.NotificationService.get_email_logs(db, tenant.id, filters)

    return PaginatedResponse(
        data=logs,
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        total_pages=(total + filters.page_size - 1) // filters.page_size
    )

@router.post("/send-test-email")
async def send_test_email(
    data: schemas.SendEmailRequest,
    background_tasks: BackgroundTasks,
    tenant: Tenant = Depends(get_current_tenant),
    current_user: User = Depends(require_role(UserRole.TENANT_ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Enviar email de prueba (admin)

    - Solo TENANT_ADMIN
    - Útil para probar templates
    """
    from app.notifications.email_service import email_service

    html = email_service.render_template(
        data.template_name,
        data.template_data,
        tenant.branding.to_theme_dict() if tenant.branding else None
    )

    # Enviar en background
    background_tasks.add_task(
        email_service.send_email,
        data.to_email,
        data.subject,
        html,
        data.to_name
    )

    return {"message": "Email enviado"}
```

## 6. Email Templates

### base.html

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: {{ branding.colors.text or '#1F2937' }};
            background-color: #F3F4F6;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 600px;
            margin: 40px auto;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header {
            background: {{ branding.colors.primary or '#3B82F6' }};
            color: white;
            padding: 30px 20px;
            text-align: center;
        }
        .header img {
            max-height: 50px;
            margin-bottom: 10px;
        }
        .content {
            padding: 40px 30px;
        }
        .button {
            display: inline-block;
            background: {{ branding.colors.primary or '#3B82F6' }};
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
        }
        .footer {
            background: #F9FAFB;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #6B7280;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            {% if branding.logo %}
            <img src="{{ branding.logo }}" alt="Logo">
            {% endif %}
        </div>
        <div class="content">
            {% block content %}{% endblock %}
        </div>
        <div class="footer">
            <p>&copy; {{ current_year }} {{ app_name }}. Todos los derechos reservados.</p>
        </div>
    </div>
</body>
</html>
```

### welcome.html

```html
{% extends "base.html" %}

{% block content %}
<h2>¡Bienvenido a {{ tenant_name }}!</h2>

<p>Hola {{ user_name }},</p>

<p>Es un placer darte la bienvenida a nuestro equipo. Estamos emocionados de tenerte con nosotros.</p>

<p>En los próximos días recibirás información sobre tu proceso de onboarding. Mientras tanto, no dudes en contactarnos si tienes alguna pregunta.</p>

<p>Saludos,<br>El equipo de {{ tenant_name }}</p>
{% endblock %}
```

## Dependencias entre Módulos

**Depende de:**
- Core (config, database)
- Tenants (branding)

**Es usado por:**
- Auth (password reset, email verification)
- Users (invitaciones, bienvenida)
- Onboarding (asignaciones, recordatorios)

## Testing

Tests de envío de emails (mock SendGrid), rendering de templates, logging.

## Checklist

- [ ] Modelo EmailLog
- [ ] EmailService con SendGrid
- [ ] NotificationService con todos los tipos de email
- [ ] Templates HTML con branding
- [ ] Router para logs
- [ ] Background tasks para envíos
- [ ] Tests 80%+

## Notas

1. Implementar al final (usado por varios módulos)
2. Para desarrollo, usar logs en lugar de emails reales
3. Templates deben ser responsive
4. Usar background tasks para no bloquear requests
5. Post-MVP: sistema de cola (Celery, RabbitMQ)

## Dependencias

```txt
sendgrid>=6.10.0
jinja2>=3.1.0
```
