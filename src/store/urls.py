from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='store_home'),
    path('login/', views.login_user, name='login-page'),
    path('register/', views.register_user, name='register-page'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password', views.forgot_password, name='forgot-password-page'),
]
