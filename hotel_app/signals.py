from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, full_name=instance.get_full_name() or instance.username)


# Audit logging for create/update/delete
from django.db.models.signals import post_delete
from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils.module_loading import import_string

AuditLog = apps.get_model('hotel_app', 'AuditLog')


def _log_action(actor, action, instance, changes=None):
    try:
        AuditLog.objects.create(
            actor=actor if hasattr(actor, 'pk') else None,
            action=action,
            model_name=instance.__class__.__name__,
            object_pk=str(getattr(instance, 'pk', '')),
            changes=changes or {}
        )
    except Exception:
        # Avoid breaking requests if logging fails
        pass


@receiver(post_save)
def model_saved(sender, instance, created, **kwargs):
    # Only log models from our app
    if sender._meta.app_label != 'hotel_app':
        return
    user = None
    try:
        # attempt to get current request user via threadlocals if available
        from django_currentuser.middleware import get_current_authenticated_user
        user = get_current_authenticated_user()()
    except Exception:
        user = None
    _log_action(user, 'create' if created else 'update', instance)


@receiver(post_delete)
def model_deleted(sender, instance, **kwargs):
    if sender._meta.app_label != 'hotel_app':
        return
    user = None
    try:
        from django_currentuser.middleware import get_current_authenticated_user
        user = get_current_authenticated_user()()
    except Exception:
        user = None
    _log_action(user, 'delete', instance)
