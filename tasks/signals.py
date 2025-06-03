from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from .models import Task, TaskHistory, User
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Task)
def create_task_history(sender, instance, created, **kwargs):
    """Create history entry when task is created or updated"""
    if created:
        TaskHistory.objects.create(
            task=instance,
            user=instance.created_by,
            action='created',
            description=f'Task created and assigned to {instance.assigned_to.username}'
        )
        logger.info(f'Task {instance.id} created by {instance.created_by.username}')


@receiver(pre_save, sender=Task)
def track_task_changes(sender, instance, **kwargs):
    """Track changes to task fields"""
    if instance.pk:  # Only for existing tasks
        try:
            old_task = Task.objects.get(pk=instance.pk)
            
            # Track assignment changes
            if old_task.assigned_to != instance.assigned_to:
                TaskHistory.objects.create(
                    task=instance,
                    user=instance.assigned_to,  # This will be set after save
                    action='assigned',
                    description=f'Task reassigned from {old_task.assigned_to.username} to {instance.assigned_to.username}'
                )
            
            # Track status changes
            if old_task.status != instance.status:
                TaskHistory.objects.create(
                    task=instance,
                    user=instance.assigned_to,  # This will be updated in the view
                    action='status_changed',
                    description=f'Status changed from {old_task.status} to {instance.status}'
                )
        
        except Task.DoesNotExist:
            pass


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log user login events"""
    logger.info(f'User {user.username} logged in from {request.META.get("REMOTE_ADDR", "unknown IP")}')