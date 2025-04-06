from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='store_home'),
    path('login/', views.login_user, name='login-page'),
    path('register/', views.register_user, name='register-page'),
    path('logout/', views.logout_view, name='logout'),
    
    #Password Reset Links
    path('forgot-password/', views.forgot_password, name='forgot-password'),
    path('password-reset-sent/<str:reset_id>/', views.password_reset_sent, name='password-reset-sent'),
    path('reset-password/<str:reset_id>/', views.reset_password, name='reset-password'),

]
