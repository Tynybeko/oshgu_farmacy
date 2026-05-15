from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect

from .models import UserRole


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            profile = getattr(request.user, 'profile', None)
            if profile and profile.role in roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, 'У вас нет прав для выполнения этого действия.')
            return redirect('dashboard')
        return wrapper
    return decorator


ADMIN_ROLES = (UserRole.ADMIN,)
STAFF_ROLES = (UserRole.ADMIN, UserRole.PHARMACIST, UserRole.CASHIER, UserRole.WAREHOUSE)
SALES_ROLES = (UserRole.ADMIN, UserRole.PHARMACIST, UserRole.CASHIER)
WAREHOUSE_ROLES = (UserRole.ADMIN, UserRole.WAREHOUSE, UserRole.PHARMACIST)
MANAGE_ROLES = (UserRole.ADMIN, UserRole.PHARMACIST)
