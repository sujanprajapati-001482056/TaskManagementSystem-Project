from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta


def validate_future_date(value):
    """Validator to ensure due date is not in the past"""
    if value < timezone.now():
        raise ValidationError('Due date cannot be in the past')


def validate_reasonable_due_date(value):
    """Validator to ensure due date is not too far in the future"""
    max_future_date = timezone.now() + timedelta(days=365*2)  # 2 years
    if value > max_future_date:
        raise ValidationError('Due date cannot be more than 2 years in the future')

class User(AbstractUser):
    """Custom User model with role-based permissions"""
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'Regular User'),
    ]
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='user',
        help_text='User role determines permissions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_admin(self):
        """Check if user is an admin"""
        return self.role == 'admin'
    
    def is_regular_user(self):
        """Check if user is a regular user"""
        return self.role == 'user'
    
    def get_assigned_tasks_count(self):
        """Get count of tasks assigned to this user"""
        return self.assigned_tasks.count()
    
    def get_created_tasks_count(self):
        """Get count of tasks created by this user"""
        return self.created_tasks.count()
class Task(models.Model):
    """Task model for managing user tasks"""
    
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    title = models.CharField(
        max_length=200,
        help_text='Task title (max 200 characters)'
    )
    description = models.TextField(
        blank=True,
        max_length=2000,
        help_text='Detailed task description (max 2000 characters)'
    )
    due_date = models.DateTimeField(
        validators=[validate_future_date, validate_reasonable_due_date],
        help_text='When the task should be completed'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_started',
        db_index=True
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        db_index=True
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_tasks',
        help_text='User assigned to this task'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_tasks',
        help_text='User who created this task'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'due_date']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['priority', 'due_date']),
        ]
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    def is_overdue(self):
        """Check if task is overdue"""
        return self.due_date < timezone.now() and self.status != 'completed'
    
    def days_until_due(self):
        """Calculate days until due date"""
        if self.status == 'completed':
            return None
        delta = self.due_date - timezone.now()
        return delta.days
    
    def can_be_completed_by(self, user):
        """Check if user can mark this task as completed"""
        if user.is_admin():
            return True
        if self.assigned_to == user and not self.is_overdue():
            return True
        return False
    
    def clean(self):
        """Model validation"""
        super().clean()
        
        # Validate that assigned user exists and is active
        if self.assigned_to and not self.assigned_to.is_active:
            raise ValidationError({'assigned_to': 'Cannot assign task to inactive user'})
        
        # Validate status transitions for existing tasks
        if self.pk:
            old_task = Task.objects.get(pk=self.pk)
            if old_task.status != self.status:
                self._validate_status_transition(old_task.status, self.status)
    
    def _validate_status_transition(self, old_status, new_status):
        """Validate status transitions"""
        valid_transitions = {
            'not_started': ['in_progress', 'completed'],
            'in_progress': ['not_started', 'completed'],
            'completed': ['in_progress']
        }
        
        if new_status not in valid_transitions.get(old_status, []):
            raise ValidationError({
                'status': f'Invalid status transition from {old_status} to {new_status}'
            })
    
    def save(self, *args, **kwargs):
        """Override save to include validation"""
        self.full_clean()
        super().save(*args, **kwargs)


class TaskComment(models.Model):
    """Comments on tasks for better collaboration"""
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='task_comments'
    )
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Task Comment'
        verbose_name_plural = 'Task Comments'
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"


class TaskHistory(models.Model):
    """Track task changes for audit purposes"""
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('status_changed', 'Status Changed'),
        ('assigned', 'Assigned'),
        ('completed', 'Completed'),
    ]
    
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='history'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='task_actions'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(max_length=500)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Task History'
        verbose_name_plural = 'Task Histories'
    
    def __str__(self):
        return f"{self.action} - {self.task.title} by {self.user.username}"