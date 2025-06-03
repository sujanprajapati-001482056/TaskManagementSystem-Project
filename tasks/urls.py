"""
URL patterns for tasks app
"""
from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Basic API info endpoint
    path('', views.api_info, name='api_info'),
    
    # Authentication endpoints
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/profile/', views.profile, name='profile'),
    path('auth/profile/update/', views.update_profile, name='update_profile'),
    
    # Task endpoints
    path('tasks/', views.list_tasks, name='list_tasks'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/<int:task_id>/', views.get_task, name='get_task'),
    path('tasks/<int:task_id>/update/', views.update_task, name='update_task'),
    path('tasks/<int:task_id>/delete/', views.delete_task, name='delete_task'),
    path('tasks/<int:task_id>/status/', views.update_task_status, name='update_task_status'),
    
    # Task comments
    path('tasks/<int:task_id>/comments/', views.add_task_comment, name='add_task_comment'),
    
    # Dashboard and utility endpoints
    path('dashboard/', views.get_dashboard, name='dashboard'),
    
    # Admin endpoints
    path('admin/users/', views.get_all_users, name='all_users'),
    path('admin/statistics/', views.get_task_statistics, name='task_statistics'),
]