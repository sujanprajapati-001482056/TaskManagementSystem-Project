from rest_framework import permissions


class IsAdminOrTaskOwner(permissions.BasePermission):
    """
    Custom permission to only allow admins or task owners to view/edit tasks.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admins have full access
        if request.user.is_admin():
            return True
        
        # Regular users can only access their assigned tasks
        if hasattr(obj, 'assigned_to'):
            return obj.assigned_to == request.user
        
        return False


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admins.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin()


class CanUpdateTask(permissions.BasePermission):
    """
    Permission for task updates - admins can update any task,
    regular users can only update status of their assigned tasks.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admins can update any field of any task
        if request.user.is_admin():
            return True
        
        # Regular users can only update their assigned tasks
        if obj.assigned_to == request.user:
            # Check if they're only updating allowed fields
            if request.method == 'PATCH':
                allowed_fields = {'status'}
                update_fields = set(request.data.keys())
                return update_fields.issubset(allowed_fields)
            return True
        
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object.
        return obj.author == request.user


class CanViewTask(permissions.BasePermission):
    """
    Permission to view tasks based on user role and assignment.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admins can view all tasks
        if request.user.is_admin():
            return True
        
        # Users can view tasks assigned to them or created by them
        return (obj.assigned_to == request.user or 
                obj.created_by == request.user)
