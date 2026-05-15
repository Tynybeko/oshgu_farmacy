from .models import AuditLog
from .utils import log_action


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated and request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            if not request.path.startswith('/static/'):
                log_action(
                    request.user,
                    f'{request.method} {request.path}',
                    details=f'Статус: {response.status_code}',
                    ip_address=self._get_ip(request),
                )
        return response

    @staticmethod
    def _get_ip(request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
