# TaskManagementSystem-Project
 Django REST API-based task management system with user authentication, role-based permissions, and admin interface for team collaboration.
# Task Management System
A comprehensive Django REST API for managing tasks with role-based permissions, JWT authentication, and real-time task tracking.

# Features
A.User Authentication & Authorization
1.JWT-based authentication
2.Role-based permissions (Admin/User)
3.User registration and profile management

B.Task Management
1.Create, read, update, and delete tasks
2.Task status tracking (Not Started, In Progress, Completed)
3.Priority levels (Low, Medium, High, Urgent)
4.Due date validation and overdue detection
5.Task assignment and reassignment

C. Advanced Features
1.Task comments for collaboration
2.Task history tracking for audit trails
3.Dashboard with statistics and insights
4.Filtering and search functionality

D. Admin Features
1.User management
2.System-wide task statistics
3.Advanced task management capabilities

# Technology Stack
1.Backend: Django 4.2, Django REST Framework
2.Authentication: JWT (Simple JWT)
3.Database: SQLite (development), PostgreSQL (production ready)
4.API Documentation: RESTful API design
5.Security: CORS headers, password validation, role-based permissions

# Prerequisites
1.Python 3.8+
2.pip (Python package manager)
3.Virtual environment (recommended)

# Quick Start
Set Up Virtual Environment

# Create virtual environment
python -m venv task_management_env

# Activate virtual environment
A.On Windows:
task_management_env\\Scripts\\activate
B.On macOS/Linux:
source task_management_env/bin/activate

# Install Dependencies
1.pip install Django==4.2.0
2.pip install djangorestframework==3.14.0
3.pip install djangorestframework-simplejwt==5.2.2
4.pip install python-decouple==3.8
5.pip install django-cors-headers==4.3.1

# Environment Configuration
Create a .env file in the project root:
SECRET_KEY=your-super-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Setup
# Create and apply migrations
python manage.py makemigrations tasks
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run the Development Server
python manage.py runserver
The API will be available at http://localhost:8000/api/v1/

# API Endpoints
# Authentication Endpoints
1.User Registration:POST	/api/v1/auth/register/
2.User Login:POST	/api/v1/auth/login/	
3.User Profile:GET	/api/v1/auth/profile/	
4.Update User Profile:PUT/PATCH	/api/v1/auth/profile/update/	
# Tasks Endpoints
1.List tasks (with filtering):GET	/api/v1/tasks/
2.Create new task (Admin only):POST	/api/v1/tasks/create/	
3.Get specific task:GET	/api/v1/tasks/{id}/	
4.Update task:PUT/PATCH	/api/v1/tasks/{id}/update/	
5.Delete task (Admin only):DELETE	/api/v1/tasks/{id}/delete/	
6.Update task status:PATCH	/api/v1/tasks/{id}/status/	
# Dashboard & Admin
1.Get dashboard data:GET	/api/v1/dashboard/	
2.Get all users (Admin only):GET	/api/v1/admin/users/	
3.Get system statistics (Admin only):GET	/api/v1/admin/statistics/	
 
# API Usage Examples
# User Registration
curl -X POST http://localhost:8000/api/v1/auth/register/ \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "sujanprajapati",
    "email": "sujan@company.com",
    "password": "********",
    "password_confirm": "********",
    "first_name": "Sujan",
    "last_name": "Prajapati",
    "role": "Regular_user"
  }'
# User Login
curl -X POST http://localhost:8000/api/v1/auth/login/ \\
  -H "Content-Type: application/json" \\
  -d '{
    "username": "sujanprajapati",
    "password": "********"
  }'
 
 # Create Task (Admin only)
curl -X POST http://localhost:8000/api/v1/tasks/create/ \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -d '{
    "title": "Complete project documentation",
    "description": "Write comprehensive README and API documentation",
    "due_date": "2024-12-31T23:59:59Z",
    "priority": "high",
    "assigned_to_username": "sujanprajapati"
  }'

 # Project Structure
task_management_system/
├── task_management_system/
│   ├── __init__.py
│   ├── settings.py          # Django settings with REST framework config
│   ├── urls.py              # Main URL configuration
│   ├── wsgi.py              # WSGI configuration
│   └── asgi.py              # ASGI configuration
├── tasks/                   # Main application
│   ├── models.py            # User, Task, TaskComment, TaskHistory models
│   ├── serializers.py       # DRF serializers
│   ├── views.py             # API views
│   ├── permissions.py       # Custom permissions
│   ├── admin.py             # Django admin configuration
│   ├── signals.py           # Django signals for task tracking
│   └── urls.py              # App URL patterns
├── static/                  # Static files
├── media/                   # Media files
├── logs/                    # Application logs
├── manage.py
└── README.md

# Security Features
1.JWT Authentication: Secure token-based authentication
2.Role-based Permissions: Admin and User roles with different capabilities
3.Password Validation: Strong password requirements
4.CORS Configuration: Secure cross-origin requests
5.Input Validation: Comprehensive data validation

# Database Models
# User Model
1.Custom user model extending Django's AbstractUser
2.Role-based permissions (admin/user)
3.Profile information and timestamps
# Task Model
1.Comprehensive task management with validation
2.Status tracking and priority levels
3.Assignment and due date management
4.Overdue detection and business rules
# TaskComment Model
1.Collaboration through task comments
2.Author tracking and timestamps
# TaskHistory Model
1.Audit trail for all task changes
2.Action tracking and descriptions

# Deployment
# Environment Variables for Production
1.SECRET_KEY=your-production-secret-key
2.DEBUG=False
3.ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
4.DATABASE_URL=postgresql://user:password@localhost:5432/taskdb

# Production Setup
1.Database: Configure PostgreSQL
2.Static Files: Set up static file serving
3.Security: Configure HTTPS and security headers
4.Logging: Set up production logging
5.Monitoring: Implement health checks

# Testing
# Run tests
python manage.py test

# Test API endpoints
curl -X GET http://localhost:8000/api/v1/

# License
This project is licensed under the MIT License.

# Performance Features
1.Database Indexing: Optimized queries with proper indexes
2.Pagination: Efficient data loading with pagination
3.Filtering: Advanced filtering capabilities
4.Caching: Ready for Redis caching implementation

# Contributing
1.Fork the repository
2.Create a feature branch (git checkout -b feature/amazing-feature)
3.Commit your changes (git commit -m 'Add amazing feature')
4.Push to the branch (git push origin feature/amazing-feature)
5.Open a Pull Request

# License
This project is licensed under the MIT License - see the LICENSE file for details.

# Support
If you encounter any issues or have questions:
1.Check the Issues page
2.Create a new issue with detailed information
3.Contact the maintainers

# Acknowledgments
1.Django and Django REST Framework communities
2.Contributors and testers
3.Open source libraries used in this project


