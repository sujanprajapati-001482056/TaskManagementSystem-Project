from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q, Count
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from .models import Task, User, TaskComment, TaskHistory
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    TaskSerializer, TaskCreateSerializer, TaskListSerializer, 
    TaskStatusUpdateSerializer, BulkStatusUpdateSerializer,
    TaskCommentSerializer
)
from .permissions import IsAdminUser, IsAdminOrTaskOwner, CanUpdateTask

logger = logging.getLogger(__name__)
# API Info View
@api_view(['GET'])
@permission_classes([AllowAny])
def api_info(request):
    """API information endpoint"""
    return Response({
        'message': 'Task Management System API',
        'version': '1.0',
        'endpoints': {
            'authentication': {
                'register': '/api/v1/auth/register/',
                'login': '/api/v1/auth/login/',
                'profile': '/api/v1/auth/profile/',
            },
            'tasks': {
                'list': '/api/v1/tasks/',
                'create': '/api/v1/tasks/create/',
                'detail': '/api/v1/tasks/{id}/',
            },
            'dashboard': '/api/v1/dashboard/',
            'admin': {
                'users': '/api/v1/admin/users/',
                'statistics': '/api/v1/admin/statistics/',
            }
        }
    })
# Authentication Views
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """User registration endpoint"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        
        logger.info(f"New user registered: {user.username}")
        
        return Response({
            'success': True,
            'message': 'User created successfully',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'message': 'Registration failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """User login endpoint"""
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        logger.info(f"User logged in: {user.username}")
        
        return Response({
            'success': True,
            'message': 'Login successful',
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'message': 'Login failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """Get user profile"""
    serializer = UserProfileSerializer(request.user)
    return Response({
        'success': True,
        'user': serializer.data
    })


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Update user profile"""
    serializer = UserProfileSerializer(
        request.user, 
        data=request.data, 
        partial=True
    )
    if serializer.is_valid():
        serializer.save()
        return Response({
            'success': True,
            'message': 'Profile updated successfully',
            'user': serializer.data
        })
    
    return Response({
        'success': False,
        'message': 'Profile update failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


# Task Views
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def create_task(request):
    """Create a new task (Admin only)"""
    serializer = TaskCreateSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        try:
            with transaction.atomic():
                task = serializer.save()
                
                # Create history entry
                TaskHistory.objects.create(
                    task=task,
                    user=request.user,
                    action='created',
                    description=f'Task created and assigned to {task.assigned_to.username}'
                )
                
                logger.info(f"Task {task.id} created by {request.user.username}")
                
                return Response({
                    'success': True,
                    'message': 'Task created successfully',
                    'task': TaskSerializer(task).data
                }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return Response({
                'success': False,
                'message': 'Task creation failed',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': False,
        'message': 'Invalid task data',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_tasks(request):
    """List tasks with filtering and pagination"""
    # Base queryset depends on user role
    if request.user.is_admin():
        queryset = Task.objects.all()
    else:
        queryset = Task.objects.filter(assigned_to=request.user)
    
    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    priority_filter = request.GET.get('priority')
    if priority_filter:
        queryset = queryset.filter(priority=priority_filter)
    
    # Date filtering
    due_date_filter = request.GET.get('due_date')
    if due_date_filter:
        try:
            due_date = datetime.strptime(due_date_filter, '%Y-%m-%d').date()
            queryset = queryset.filter(due_date__date=due_date)
        except ValueError:
            return Response({
                'success': False,
                'message': 'Invalid date format. Use YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Date range filtering
    due_date_from = request.GET.get('due_date_from')
    due_date_to = request.GET.get('due_date_to')
    
    if due_date_from:
        try:
            from_date = datetime.strptime(due_date_from, '%Y-%m-%d')
            queryset = queryset.filter(due_date__gte=from_date)
        except ValueError:
            return Response({
                'success': False,
                'message': 'Invalid due_date_from format. Use YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    if due_date_to:
        try:
            to_date = datetime.strptime(due_date_to, '%Y-%m-%d')
            to_date = to_date.replace(hour=23, minute=59, second=59)
            queryset = queryset.filter(due_date__lte=to_date)
        except ValueError:
            return Response({
                'success': False,
                'message': 'Invalid due_date_to format. Use YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Overdue filter
    overdue_filter = request.GET.get('overdue')
    if overdue_filter and overdue_filter.lower() == 'true':
        queryset = queryset.filter(
            due_date__lt=timezone.now(),
            status__in=['not_started', 'in_progress']
        )
    
    # Search functionality
    search = request.GET.get('search')
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )
    
    # Assigned user filter (admin only)
    assigned_to_filter = request.GET.get('assigned_to')
    if assigned_to_filter and request.user.is_admin():
        try:
            assigned_user = User.objects.get(username=assigned_to_filter)
            queryset = queryset.filter(assigned_to=assigned_user)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Assigned user not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    # Sorting
    sort_by = request.GET.get('sort_by', '-created_at')
    valid_sort_fields = [
        'title', '-title', 'due_date', '-due_date', 
        'status', '-status', 'priority', '-priority',
        'created_at', '-created_at'
    ]
    if sort_by in valid_sort_fields:
        queryset = queryset.order_by(sort_by)
    
    # Pagination
    page_size = min(int(request.GET.get('page_size', 20)), 100)  # Max 100 items
    page = int(request.GET.get('page', 1))
    
    start = (page - 1) * page_size
    end = start + page_size
    
    total_count = queryset.count()
    tasks = queryset[start:end]
    
    serializer = TaskListSerializer(tasks, many=True)
    
    return Response({
        'success': True,
        'count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size,
        'tasks': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_task(request, task_id):
    """Get a specific task"""
    try:
        task = Task.objects.get(id=task_id)
        
        # Check permissions
        if not request.user.is_admin() and task.assigned_to != request.user:
            return Response({
                'success': False,
                'message': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = TaskSerializer(task)
        return Response({
            'success': True,
            'task': serializer.data
        })
    
    except Task.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Task not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_task(request, task_id):
    """Update a task"""
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Task not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check permissions
    if not request.user.is_admin() and task.assigned_to != request.user:
        return Response({
            'success': False,
            'message': 'Permission denied'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # For regular users, only allow status updates
    if not request.user.is_admin():
        allowed_fields = {'status'}
        update_fields = set(request.data.keys())
        if not update_fields.issubset(allowed_fields):
            return Response({
                'success': False,
                'message': 'Regular users can only update task status'
            }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = TaskSerializer(task, data=request.data, partial=True)
    if serializer.is_valid():
        try:
            with transaction.atomic():
                old_status = task.status
                updated_task = serializer.save()
                
                # Create history entry if status changed
                if 'status' in request.data and old_status != updated_task.status:
                    TaskHistory.objects.create(
                        task=updated_task,
                        user=request.user,
                        action='status_changed',
                        description=f'Status changed from {old_status} to {updated_task.status}'
                    )
                
                logger.info(f"Task {task.id} updated by {request.user.username}")
                
                return Response({
                    'success': True,
                    'message': 'Task updated successfully',
                    'task': TaskSerializer(updated_task).data
                })
        
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return Response({
                'success': False,
                'message': 'Task update failed',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': False,
        'message': 'Invalid task data',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdminUser])
def delete_task(request, task_id):
    """Delete a task (Admin only)"""
    try:
        task = Task.objects.get(id=task_id)
        task_title = task.title
        task.delete()
        
        logger.info(f"Task {task_id} ({task_title}) deleted by {request.user.username}")
        
        return Response({
            'success': True,
            'message': 'Task deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)
    
    except Task.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Task not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_task_status(request, task_id):
    """Update task status with validation"""
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Task not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check permissions
    if not request.user.is_admin() and task.assigned_to != request.user:
        return Response({
            'success': False,
            'message': 'Permission denied'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = TaskStatusUpdateSerializer(
        data=request.data, 
        context={'task': task, 'request': request}
    )
    
    if serializer.is_valid():
        new_status = serializer.validated_data['status']
        old_status = task.status
        
        # Business rule: Regular users cannot mark overdue tasks as completed
        if (new_status == 'completed' and 
            task.is_overdue() and 
            not request.user.is_admin()):
            return Response({
                'success': False,
                'message': 'Cannot mark overdue task as completed',
                'details': 'Contact an administrator to complete overdue tasks'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            with transaction.atomic():
                task.status = new_status
                task.save()
                
                # Create history entry
                TaskHistory.objects.create(
                    task=task,
                    user=request.user,
                    action='status_changed',
                    description=f'Status changed from {old_status} to {new_status}'
                )
                
                logger.info(f"Task {task.id} status changed from {old_status} to {new_status} by {request.user.username}")
                
                return Response({
                    'success': True,
                    'message': f'Task status updated from {old_status} to {new_status}',
                    'task': TaskSerializer(task).data
                })
        
        except Exception as e:
            logger.error(f"Error updating task status: {e}")
            return Response({
                'success': False,
                'message': 'Status update failed',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'success': False,
        'message': 'Invalid status update',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_dashboard(request):
    """Get dashboard data for the current user"""
    user = request.user
    
    if user.is_admin():
        # Admin dashboard
        total_tasks = Task.objects.count()
        my_tasks = Task.objects.filter(assigned_to=user)
        
        dashboard_data = {
            'user_info': {
                'username': user.username,
                'role': user.role,
                'is_admin': True
            },
            'overview': {
                'total_tasks': total_tasks,
                'my_tasks_count': my_tasks.count(),
                'overdue_tasks': Task.objects.filter(
                    due_date__lt=timezone.now(),
                    status__in=['not_started', 'in_progress']
                ).count(),
                'completed_today': Task.objects.filter(
                    status='completed',
                    updated_at__date=timezone.now().date()
                ).count()
            },
            'task_distribution': dict(
                Task.objects.values('status').annotate(
                    count=Count('status')
                ).values_list('status', 'count')
            ),
            'recent_tasks': TaskListSerializer(
                Task.objects.order_by('-created_at')[:5], 
                many=True
            ).data,
            'my_tasks': {
                'not_started': my_tasks.filter(status='not_started').count(),
                'in_progress': my_tasks.filter(status='in_progress').count(),
                'completed': my_tasks.filter(status='completed').count(),
                'overdue': my_tasks.filter(
                    due_date__lt=timezone.now(),
                    status__in=['not_started', 'in_progress']
                ).count()
            }
        }
    else:
        # Regular user dashboard
        my_tasks = Task.objects.filter(assigned_to=user)
        
        dashboard_data = {
            'user_info': {
                'username': user.username,
                'role': user.role,
                'is_admin': False
            },
            'my_tasks': {
                'total': my_tasks.count(),
                'not_started': my_tasks.filter(status='not_started').count(),
                'in_progress': my_tasks.filter(status='in_progress').count(),
                'completed': my_tasks.filter(status='completed').count(),
                'overdue': my_tasks.filter(
                    due_date__lt=timezone.now(),
                    status__in=['not_started', 'in_progress']
                ).count()
            },
            'upcoming_tasks': TaskListSerializer(
                my_tasks.filter(
                    due_date__gte=timezone.now(),
                    status__in=['not_started', 'in_progress']
                ).order_by('due_date')[:5], 
                many=True
            ).data,
            'recent_completed': TaskListSerializer(
                my_tasks.filter(status='completed').order_by('-updated_at')[:3], 
                many=True
            ).data
        }
    
    return Response({
        'success': True,
        'dashboard': dashboard_data
    })


# Admin Views
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_all_users(request):
    """Get all users (Admin only)"""
    users = User.objects.all()
    serializer = UserProfileSerializer(users, many=True)
    return Response({
        'success': True,
        'users': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_task_statistics(request):
    """Get task statistics (Admin only)"""
    stats = {
        'total_tasks': Task.objects.count(),
        'tasks_by_status': dict(
            Task.objects.values('status').annotate(count=Count('status')).values_list('status', 'count')
        ),
        'tasks_by_priority': dict(
            Task.objects.values('priority').annotate(count=Count('priority')).values_list('priority', 'count')
        ),
        'overdue_tasks': Task.objects.filter(
            due_date__lt=timezone.now(),
            status__in=['not_started', 'in_progress']
        ).count(),
        'completed_tasks': Task.objects.filter(status='completed').count(),
        'total_users': User.objects.count(),
        'admin_users': User.objects.filter(role='admin').count(),
        'active_users': User.objects.filter(is_active=True).count(),
    }
    
    return Response({
        'success': True,
        'statistics': stats
    })


# Task Comments
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_task_comment(request, task_id):
    """Add a comment to a task"""
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Task not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check permissions
    if not request.user.is_admin() and task.assigned_to != request.user:
        return Response({
            'success': False,
            'message': 'Permission denied'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = TaskCommentSerializer(data=request.data)
    if serializer.is_valid():
        comment = serializer.save(task=task, author=request.user)
        return Response({
            'success': True,
            'message': 'Comment added successfully',
            'comment': TaskCommentSerializer(comment).data
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'message': 'Invalid comment data',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)