"""Spremi HTTP request u thread-local da servisi znaju trenutni tenant.

`TenantMainMiddleware` već postavlja `request.tenant` i PostgreSQL `search_path`.
Ovaj sloj ne prebacuje schemu — samo izlaže request izvan viewa
(signali, Celery eager, pomoćne funkcije).
"""
import threading

_thread_locals = threading.local()


def get_request():
    return getattr(_thread_locals, 'request', None)


def set_request(request):
    _thread_locals.request = request


class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_request(request)
        try:
            response = self.get_response(request)
            if not response.get('Cache-Control'):
                response['Cache-Control'] = 'private, no-store'
            response['Vary'] = 'Host, Cookie'
            return response
        finally:
            set_request(None)
