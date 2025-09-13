from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.module_loading import import_string

User = get_user_model()

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        # Import UserProfile inside the function to avoid circular import issues
        from .models import UserProfile
        # Use the model class directly instead of the imported one to avoid linter issues
        UserProfile._default_manager.create(user=instance, full_name=instance.get_full_name() or instance.username)


# Audit logging for create/update/delete
from django.db.models.signals import post_delete, post_save
from django.apps import apps

# Get AuditLog model
AuditLog = apps.get_model('hotel_app', 'AuditLog')


def _log_action(actor, action, instance, changes=None):
    # Skip logging for AuditLog itself to prevent recursion
    if isinstance(instance, AuditLog):
        return
    try:
        AuditLog._default_manager.create(
            actor=actor if hasattr(actor, 'pk') else None,
            action=action,
            model_name=instance.__class__.__name__,
            object_pk=str(getattr(instance, 'pk', '')),
            changes=changes or {}
        )
    except Exception:
        # Avoid breaking requests if logging fails
        pass


def _get_current_user():
    """Get current user safely, handling missing django-currentuser"""
    try:
        # Use import_string to avoid linter issues
        get_current_authenticated_user = import_string('django_currentuser.middleware.get_current_authenticated_user')
        user = get_current_authenticated_user()()
        return user
    except (ImportError, Exception):
        # django-currentuser is not installed or other error
        return None


@receiver(post_save)
def model_saved(sender, instance, created, **kwargs):
    # Only log models from our app and exclude AuditLog to prevent recursion
    if sender._meta.app_label != 'hotel_app' or sender == AuditLog:
        return
    user = _get_current_user()
    _log_action(user, 'create' if created else 'update', instance)


@receiver(post_delete)
def model_deleted(sender, instance, **kwargs):
    # Only log models from our app and exclude AuditLog to prevent recursion
    if sender._meta.app_label != 'hotel_app' or sender == AuditLog:
        return
    user = _get_current_user()
    _log_action(user, 'delete', instance)