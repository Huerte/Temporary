from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='store_home'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('products/', views.product_view, name='products'),
    path('contact_us/', views.contact, name='contact_us'),

    path('product-details/<str:product_id>/', views.product_details, name='product-details'),
    path('profile-page/', views.profile_view, name='profile-page'),
    path('edit-profile-page/', views.edit_profile_view, name='edit-profile-page'),
    path('cart-view/', views.cart_view, name='cart-view'),
    path('add-to-cart/<str:product_id>/', views.add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<str:product_id>/', views.remove_from_cart, name='remove-from-cart'),

    #Authentication Links
    path('login/', views.login_user, name='login-page'),
    path('register/', views.register_user, name='register-page'),
    path('logout/', views.logout_view, name='logout'),
    
    #Password Reset Links
    path('forgot-password/', views.forgot_password, name='forgot-password'),
    path('password-reset-sent/<str:reset_id>/', views.password_reset_sent, name='password-reset-sent'),
    path('reset-password/<str:reset_id>/', views.reset_password, name='reset-password'),

]
