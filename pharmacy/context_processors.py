from django.conf import settings
from django.utils import timezone

from .models import Medicine, UserRole


def pharmacy_context(request):
    ctx = {
        'PHARMACY_NAME': 'Аптека «Здоровый Мир»',
        'UserRole': UserRole,
    }
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        ctx['user_profile'] = profile
        if profile:
            ctx['user_role'] = profile.role
        elif request.user.is_superuser:
            ctx['user_role'] = UserRole.ADMIN
        else:
            ctx['user_role'] = UserRole.CASHIER
        threshold = getattr(settings, 'LOW_STOCK_THRESHOLD', 10)
        days = getattr(settings, 'EXPIRY_WARNING_DAYS', 30)
        warning_date = timezone.now().date() + timezone.timedelta(days=days)
        ctx['low_stock_count'] = Medicine.objects.filter(quantity__lte=threshold).count()
        ctx['expiring_count'] = Medicine.objects.filter(
            expiry_date__lte=warning_date,
            expiry_date__gte=timezone.now().date(),
        ).count()
    return ctx
