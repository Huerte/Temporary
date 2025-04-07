from django.shortcuts import render
from django.urls import reverse

class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/') and not request.user.is_staff:
            return render(request, 'store/authentication-page/admin_access_denied.html')
        return self.get_response(request)
