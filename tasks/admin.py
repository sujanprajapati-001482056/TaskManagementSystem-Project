from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Task, TaskComment, TaskHistory


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin"""
    
    list_display = ('username', 'email', 'role', 'is_active', 'date_joined', 'task_counts')
    list_filter = ('role', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )
    
    def task_counts(self, obj):
        """Display task counts for user"""
        assigned = obj.get_assigned_tasks_count()
        created = obj.get_created_tasks_count()
        return format_html(
            '<span style="color: blue;">Assigned: {}</span><br>'
            '<span style="color: green;">Created: {}</span>',
            assigned, created
        )
    task_counts.short_description = 'Task Counts'


class TaskCommentInline(admin.TabularInline):
    """Inline admin for task comments"""
    model = TaskComment
    extra = 0
    readonly_fields = ('created_at', 'updated_at')


class TaskHistoryInline(admin.TabularInline):
    """Inline admin for task history"""
    model = TaskHistory
    extra = 0
    readonly_fields = ('timestamp',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Task admin configuration"""
    
    list_display = (
        'title', 'status', 'priority', 'assigned_to', 
        'created_by', 'due_date', 'is_overdue_display', 'created_at'
    )
    list_filter = ('status', 'priority', 'created_at', 'due_date')
    search_fields = ('title', 'description', 'assigned_to__username', 'created_by__username')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'due_date')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'created_by')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    inlines = [TaskCommentInline, TaskHistoryInline]
    
    def is_overdue_display(self, obj):
        """Display overdue status with color"""
        if obj.is_overdue():
            return format_html('<span style="color: red; font-weight: bold;">Yes</span>')
        return format_html('<span style="color: green;">No</span>')
    is_overdue_display.short_description = 'Overdue'
    
    def save_model(self, request, obj, form, change):
        """Override save to set created_by if not set"""
        if not change:  # Creating new task
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    """Task comment admin"""
    
    list_display = ('task', 'author', 'content_preview', 'created_at')
    list_filter = ('created_at', 'author')
    search_fields = ('content', 'task__title', 'author__username')
    ordering = ('-created_at',)
    
    def content_preview(self, obj):
        """Show preview of comment content"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(TaskHistory)
class TaskHistoryAdmin(admin.ModelAdmin):
    """Task history admin"""
    
    list_display = ('task', 'user', 'action', 'description_preview', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('task__title', 'user__username', 'description')
    ordering = ('-timestamp',)
    
    def description_preview(self, obj):
        """Show preview of description"""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description Preview'

