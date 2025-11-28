"""
Notification service for managing email logs and notifications.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.notifications.models import EmailLog
from app.notifications import schemas


class NotificationService:
    """Service for managing notifications and email logs."""

    @staticmethod
    def get_email_logs(
        db: Session,
        tenant_id: int,
        page: int = 1,
        size: int = 20,
        email_type: str | None = None,
        is_sent: bool | None = None
    ) -> schemas.EmailLogListResponse:
        """Get paginated email logs for a tenant."""
        query = db.query(EmailLog).filter(EmailLog.tenant_id == tenant_id)

        if email_type:
            query = query.filter(EmailLog.email_type == email_type)

        if is_sent is not None:
            query = query.filter(EmailLog.is_sent == is_sent)

        # Count total
        total = query.count()

        # Paginate
        query = query.order_by(EmailLog.created_at.desc())
        query = query.offset((page - 1) * size).limit(size)

        items = query.all()

        return schemas.EmailLogListResponse(
            items=[
                schemas.EmailLogResponse(
                    id=log.id,
                    tenant_id=log.tenant_id,
                    to_email=log.to_email,
                    to_name=log.to_name,
                    subject=log.subject,
                    email_type=log.email_type,
                    template_name=log.template_name,
                    is_sent=log.is_sent,
                    sent_at=log.sent_at,
                    error_message=log.error_message,
                    external_id=log.external_id,
                    user_id=log.user_id,
                    created_at=log.created_at
                )
                for log in items
            ],
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )

    @staticmethod
    def get_email_log(db: Session, log_id: int, tenant_id: int) -> EmailLog | None:
        """Get a specific email log."""
        return db.query(EmailLog).filter(
            EmailLog.id == log_id,
            EmailLog.tenant_id == tenant_id
        ).first()

    @staticmethod
    def get_email_stats(db: Session, tenant_id: int) -> schemas.EmailStatsResponse:
        """Get email statistics for a tenant."""
        # Total sent
        total_sent = db.query(func.count(EmailLog.id)).filter(
            EmailLog.tenant_id == tenant_id,
            EmailLog.is_sent == True
        ).scalar() or 0

        # Total failed
        total_failed = db.query(func.count(EmailLog.id)).filter(
            EmailLog.tenant_id == tenant_id,
            EmailLog.is_sent == False
        ).scalar() or 0

        # Success rate
        total = total_sent + total_failed
        success_rate = (total_sent / total * 100) if total > 0 else 0

        # By type
        by_type_query = db.query(
            EmailLog.email_type,
            func.count(EmailLog.id).label('count')
        ).filter(
            EmailLog.tenant_id == tenant_id
        ).group_by(EmailLog.email_type).all()

        by_type = {row.email_type: row.count for row in by_type_query}

        return schemas.EmailStatsResponse(
            total_sent=total_sent,
            total_failed=total_failed,
            success_rate=round(success_rate, 2),
            by_type=by_type
        )

    @staticmethod
    def retry_failed_email(db: Session, log_id: int, tenant_id: int) -> EmailLog | None:
        """Retry sending a failed email."""
        from app.notifications.email_service import EmailService

        log = NotificationService.get_email_log(db, log_id, tenant_id)
        if not log or log.is_sent:
            return None

        # Create new email log with retry
        new_log = EmailService.send_email(
            db=db,
            to_email=log.to_email,
            to_name=log.to_name,
            subject=log.subject,
            email_type=log.email_type,
            template_name=log.template_name,
            template_data=log.template_data,
            tenant_id=log.tenant_id,
            user_id=log.user_id
        )

        return new_log

    @staticmethod
    def delete_old_logs(db: Session, tenant_id: int, days: int = 90) -> int:
        """Delete email logs older than specified days."""
        from datetime import timedelta as td
        cutoff = datetime.now(timezone.utc) - td(days=days)

        deleted = db.query(EmailLog).filter(
            EmailLog.tenant_id == tenant_id,
            EmailLog.created_at < cutoff
        ).delete()

        db.commit()
        return deleted
