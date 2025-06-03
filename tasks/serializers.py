from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from .models import Task, User, TaskComment, TaskHistory
import re
class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm', 'role']
        
    def validate_username(self, value):
        """Validate username"""
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long")
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError("Username can only contain letters, numbers, and underscores")
        return value
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value
    
    def validate_password(self, value):
        """Validate password strength"""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter")
        if not re.search(r'\\d', value):
            raise serializers.ValidationError("Password must contain at least one digit")
        return value
        
    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords don't match"})
        return attrs
    
    def create(self, validated_data):
        """Create new user"""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        """Validate login credentials"""
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    
    assigned_tasks_count = serializers.SerializerMethodField()
    created_tasks_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'role', 'date_joined', 'assigned_tasks_count', 'created_tasks_count'
        ]
        read_only_fields = ['id', 'date_joined']
    
    def get_assigned_tasks_count(self, obj):
        """Get count of assigned tasks"""
        return obj.get_assigned_tasks_count()
    
    def get_created_tasks_count(self, obj):
        """Get count of created tasks"""
        return obj.get_created_tasks_count()


class TaskCommentSerializer(serializers.ModelSerializer):
    """Serializer for task comments"""
    
    author_username = serializers.CharField(source='author.username', read_only=True)
    
    class Meta:
        model = TaskComment
        fields = ['id', 'content', 'author', 'author_username', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']


class TaskHistorySerializer(serializers.ModelSerializer):
    """Serializer for task history"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = TaskHistory
        fields = ['id', 'action', 'description', 'user', 'user_username', 'timestamp']
        read_only_fields = ['id', 'user', 'timestamp']


class TaskSerializer(serializers.ModelSerializer):
    """Main task serializer"""
    
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    days_until_due = serializers.SerializerMethodField()
    comments = TaskCommentSerializer(many=True, read_only=True)
    history = TaskHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'due_date', 'status', 'priority',
            'assigned_to', 'assigned_to_username', 'created_by', 
            'created_by_username', 'created_at', 'updated_at', 
            'is_overdue', 'days_until_due', 'comments', 'history'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_days_until_due(self, obj):
        """Get days until due date"""
        return obj.days_until_due()
    
    def validate_title(self, value):
        """Validate task title"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long")
        if len(value) > 200:
            raise serializers.ValidationError("Title cannot exceed 200 characters")
        return value.strip()
    
    def validate_description(self, value):
        """Validate task description"""
        if len(value) > 2000:
            raise serializers.ValidationError("Description cannot exceed 2000 characters")
        return value.strip()
    
    def validate_due_date(self, value):
        """Validate due date"""
        if value < timezone.now():
            raise serializers.ValidationError("Due date cannot be in the past")
        
        max_future_date = timezone.now() + timedelta(days=365*2)
        if value > max_future_date:
            raise serializers.ValidationError("Due date cannot be more than 2 years in the future")
        
        return value
    
    def validate_assigned_to(self, value):
        """Validate assigned user"""
        if not value.is_active:
            raise serializers.ValidationError("Cannot assign task to inactive user")
        return value


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tasks"""
    
    assigned_to_username = serializers.CharField(write_only=True)
    
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'priority', 'assigned_to_username']
    
    def validate_assigned_to_username(self, value):
        """Validate assigned user exists"""
        try:
            user = User.objects.get(username=value, is_active=True)
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this username does not exist or is inactive")
    
    def validate_title(self, value):
        """Validate title"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long")
        return value.strip()
    
    def validate_due_date(self, value):
        """Validate due date"""
        if value < timezone.now():
            raise serializers.ValidationError("Due date cannot be in the past")
        return value
    
    def create(self, validated_data):
        """Create new task"""
        assigned_to = validated_data.pop('assigned_to_username')
        validated_data['assigned_to'] = assigned_to
        validated_data['created_by'] = self.context['request'].user
        return Task.objects.create(**validated_data)


class TaskListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for task lists"""
    
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    days_until_due = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'due_date', 'status', 'priority',
            'assigned_to_username', 'is_overdue', 'days_until_due'
        ]
    
    def get_days_until_due(self, obj):
        """Get days until due date"""
        return obj.days_until_due()


class TaskStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating task status"""
    
    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES)
    
    def validate_status(self, value):
        """Validate status transition"""
        task = self.context.get('task')
        if not task:
            return value
        
        # Validate status transitions
        valid_transitions = {
            'not_started': ['in_progress', 'completed'],
            'in_progress': ['not_started', 'completed'],
            'completed': ['in_progress']
        }
        
        current_status = task.status
        if value != current_status and value not in valid_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f'Invalid status transition from {current_status} to {value}'
            )
        
        return value


class BulkStatusUpdateSerializer(serializers.Serializer):
    """Serializer for bulk status updates"""
    
    task_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100
    )
    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES)
    
    def validate_task_ids(self, value):
        """Validate task IDs"""
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Duplicate task IDs found")
        return value


