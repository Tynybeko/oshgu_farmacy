from .models import AuditLog


def log_action(user, action, model_name='', object_id='', details='', ip_address=None):
    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        model_name=model_name,
        object_id=str(object_id) if object_id else '',
        details=details,
        ip_address=ip_address,
    )
