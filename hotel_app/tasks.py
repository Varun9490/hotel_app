from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from .models import ServiceRequest, ServiceRequestStep, WorkflowStep


@shared_task
def process_service_request(request_id):
    """
    Process a new service request through its workflow
    """
    try:
        service_request = ServiceRequest.objects.get(id=request_id)
        workflow = service_request.request_type.workflow

        if workflow:
            # Get the first workflow step
            first_step = workflow.workflowstep_set.order_by("step_order").first()
            if first_step:
                # Create initial service request step
                ServiceRequestStep.objects.create(
                    request=service_request,
                    step=first_step,
                    status="pending",
                )

                # Notify users if role_hint is defined
                if first_step.role_hint:
                    notify_step_assignment.delay(service_request.id, first_step.id)

    except ServiceRequest.DoesNotExist:
        # Log or handle gracefully
        return


@shared_task
def notify_step_assignment(request_id, step_id):
    """
    Notify assigned users about a new workflow step
    """
    try:
        service_request = ServiceRequest.objects.get(id=request_id)
        step = WorkflowStep.objects.get(id=step_id)

        recipients = []

        if step.role_hint == "admin":
            from django.contrib.auth.models import Group

            try:
                admin_group = Group.objects.get(name="Admins")
                recipients = admin_group.user_set.all()
            except Group.DoesNotExist:
                recipients = []
        else:
            # Default to assignee
            if service_request.assignee_user:
                recipients = [service_request.assignee_user]

        # Send email notifications
        for user in recipients:
            if user and user.email:
                send_mail(
                    subject=f"New Task: {service_request.request_type.name}",
                    message=f'You have been assigned a new task: "{step.name}"',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )

    except (ServiceRequest.DoesNotExist, WorkflowStep.DoesNotExist):
        return


@shared_task
def check_pending_requests():
    """
    Periodic task to check for stale pending requests
    """
    stale_threshold = timezone.now() - timedelta(hours=24)

    stale_steps = ServiceRequestStep.objects.filter(
        status="pending",
        started_at__lte=stale_threshold,
    )

    for step in stale_steps:
        notify_stale_request.delay(step.id)


@shared_task
def notify_stale_request(step_id):
    """
    Notify users about a stale service request step
    """
    try:
        step = ServiceRequestStep.objects.get(id=step_id)
        service_request = step.request

        recipients = []

        if service_request.assignee_user and service_request.assignee_user.email:
            recipients.append(service_request.assignee_user.email)
        else:
            from django.contrib.auth.models import Group

            try:
                admin_group = Group.objects.get(name="Admins")
                recipients += [
                    user.email
                    for user in admin_group.user_set.all()
                    if user.email
                ]
            except Group.DoesNotExist:
                pass

        if recipients:
            send_mail(
                subject=f"Service Request Step Pending: {service_request.request_type.name}",
                message=f'The step "{step.step.name}" has been pending for over 24 hours.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False,
            )

    except ServiceRequestStep.DoesNotExist:
        return
