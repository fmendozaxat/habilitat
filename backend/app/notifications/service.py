"""
Notification service.
Business logic for managing notifications and email sending.
"""

from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.notifications.models import EmailLog
from app.notifications.email_service import email_service
from app.notifications import schemas
from app.tenants.models import Tenant


class NotificationService:
    """
    Servicio de gestión de notificaciones.

    Proporciona métodos para enviar diferentes tipos de emails
    transaccionales y registrar logs de envío.
    """

    @staticmethod
    async def send_welcome_email(
        db: Session,
        user_email: str,
        user_name: str,
        tenant_id: int,
        tenant: Tenant,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Enviar email de bienvenida al tenant.

        Template: welcome.html

        Args:
            db: Database session
            user_email: Email del usuario
            user_name: Nombre del usuario
            tenant_id: ID del tenant
            tenant: Objeto tenant
            user_id: ID del usuario (opcional)

        Returns:
            True si el email se envió exitosamente
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

        # Crear log
        log = EmailLog(
            tenant_id=tenant_id,
            to_email=user_email,
            to_name=user_name,
            subject=f"Bienvenido a {tenant.name}",
            email_type="welcome",
            template_name="welcome.html",
            template_data={"user_name": user_name, "tenant_name": tenant.name},
            is_sent=success,
            sent_at=datetime.utcnow() if success else None,
            error_message=error,
            user_id=user_id
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
        Enviar email de invitación a nuevo usuario.

        Template: invitation.html

        Args:
            db: Database session
            invitation_email: Email del invitado
            invitation_token: Token de invitación
            inviter_name: Nombre de quien invita
            tenant_id: ID del tenant
            tenant: Objeto tenant

        Returns:
            True si el email se envió exitosamente
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
            template_data={
                "tenant_name": tenant.name,
                "inviter_name": inviter_name,
                "accept_url": accept_url
            },
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
        tenant_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Enviar email de reset de contraseña.

        Template: password_reset.html

        Args:
            db: Database session
            user_email: Email del usuario
            user_name: Nombre del usuario
            reset_token: Token de reset
            tenant_id: ID del tenant (opcional)
            user_id: ID del usuario (opcional)

        Returns:
            True si el email se envió exitosamente
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
            template_data={"user_name": user_name, "reset_url": reset_url},
            is_sent=success,
            sent_at=datetime.utcnow() if success else None,
            error_message=error,
            user_id=user_id
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
        tenant_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Enviar email de verificación de email.

        Template: email_verification.html

        Args:
            db: Database session
            user_email: Email del usuario
            user_name: Nombre del usuario
            verification_token: Token de verificación
            tenant_id: ID del tenant (opcional)
            user_id: ID del usuario (opcional)

        Returns:
            True si el email se envió exitosamente
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
            template_data={"user_name": user_name, "verify_url": verify_url},
            is_sent=success,
            sent_at=datetime.utcnow() if success else None,
            error_message=error,
            user_id=user_id
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
        tenant: Tenant,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Enviar email cuando se asigna un onboarding.

        Template: onboarding_assigned.html

        Args:
            db: Database session
            user_email: Email del usuario
            user_name: Nombre del usuario
            flow_title: Título del flujo de onboarding
            tenant_id: ID del tenant
            tenant: Objeto tenant
            user_id: ID del usuario (opcional)

        Returns:
            True si el email se envió exitosamente
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
            template_data={
                "user_name": user_name,
                "flow_title": flow_title,
                "tenant_name": tenant.name,
                "dashboard_url": dashboard_url
            },
            is_sent=success,
            sent_at=datetime.utcnow() if success else None,
            error_message=error,
            user_id=user_id
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
        tenant: Tenant,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Enviar recordatorio de onboarding pendiente.

        Template: onboarding_reminder.html

        Args:
            db: Database session
            user_email: Email del usuario
            user_name: Nombre del usuario
            flow_title: Título del flujo de onboarding
            progress_percentage: Porcentaje de progreso actual
            tenant_id: ID del tenant
            tenant: Objeto tenant
            user_id: ID del usuario (opcional)

        Returns:
            True si el email se envió exitosamente
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
            template_data={
                "user_name": user_name,
                "flow_title": flow_title,
                "progress_percentage": progress_percentage,
                "tenant_name": tenant.name,
                "dashboard_url": dashboard_url
            },
            is_sent=success,
            sent_at=datetime.utcnow() if success else None,
            error_message=error,
            user_id=user_id
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
        """
        Obtener logs de emails con filtros y paginación.

        Args:
            db: Database session
            tenant_id: ID del tenant
            filters: Parámetros de filtrado y paginación

        Returns:
            Tuple (logs, total_count)
        """
        query = db.query(EmailLog).filter(EmailLog.tenant_id == tenant_id)

        # Aplicar filtros
        if filters.email_type:
            query = query.filter(EmailLog.email_type == filters.email_type)

        if filters.is_sent is not None:
            query = query.filter(EmailLog.is_sent == filters.is_sent)

        if filters.to_email:
            query = query.filter(EmailLog.to_email.ilike(f"%{filters.to_email}%"))

        # Total count
        total = query.count()

        # Paginación y ordenamiento
        logs = query.order_by(
            EmailLog.created_at.desc()
        ).offset(filters.offset).limit(filters.page_size).all()

        return logs, total
