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
from django.db.models.signals import pre_save
from django.utils import timezone
from django.conf import settings
from .whatsapp_service import whatsapp_service

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


# -- Complaint specific signals for assignment, status changes and SLA tracking
Complaint = apps.get_model('hotel_app', 'Complaint')


@receiver(pre_save, sender=Complaint)
def complaint_pre_save(sender, instance, **kwargs):
    """Capture previous state before save."""
    try:
        if not instance.pk:
            instance._pre_save_instance = None
            return
        previous = Complaint._default_manager.filter(pk=instance.pk).first()
        instance._pre_save_instance = previous
    except Exception:
        instance._pre_save_instance = None


@receiver(post_save, sender=Complaint)
def complaint_post_save(sender, instance, created, **kwargs):
    """After complaint is saved, detect assignment and status changes and notify.

    Also update SLA breach flag if due_at passed and not resolved.
    """
    try:
        prev = getattr(instance, '_pre_save_instance', None)
        # Assignment changed
        if prev is None and instance.assigned_to:
            # new assignment
            msg = f"You have been assigned a complaint: {instance.subject}"
            # Try phone on assigned user profile
            phone = None
            try:
                profile = instance.assigned_to.userprofile
                phone = profile.phone
            except Exception:
                phone = None
            if phone:
                whatsapp_service.send_text(phone, msg)

        elif prev and prev.assigned_to != instance.assigned_to:
            # assignment changed
            if instance.assigned_to:
                msg = f"You have been assigned a complaint: {instance.subject}"
                phone = None
                try:
                    profile = instance.assigned_to.userprofile
                    phone = profile.phone
                except Exception:
                    phone = None
                if phone:
                    whatsapp_service.send_text(phone, msg)

        # Status change handling
        if prev is None and instance.status == 'in_progress':
            instance.started_at = timezone.now()
            instance.save()
        elif prev and prev.status != instance.status:
            # moved to in_progress
            if instance.status == 'in_progress' and not instance.started_at:
                instance.started_at = timezone.now()
                instance.save()
            # moved to resolved
            if instance.status == 'resolved' and not instance.resolved_at:
                instance.resolved_at = timezone.now()
                # compute sla breach
                if instance.due_at and instance.resolved_at > instance.due_at:
                    instance.sla_breached = True
                instance.save()

        # SLA breach check for unresolved complaints
        if not instance.resolved_at and instance.due_at and timezone.now() > instance.due_at:
            if not instance.sla_breached:
                instance.sla_breached = True
                instance.save()

    except Exception:
        # don't allow notification failures to interrupt request
        pass