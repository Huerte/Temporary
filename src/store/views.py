from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, ForgotPassword
from django.contrib.auth.forms import SetPasswordForm
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from main import settings
from . import models


@login_required(login_url='/login')
def home(request):
    return render(request, 'store/home.html')

def login_user(request):
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
           user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'User does not exists.')
            return redirect('login-page')
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('store_home')
        else:
            messages.error(request, 'Username or Password does not exists')
            
    return render(request, 'store/login_page.html')

def register_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login-page')
    else:
        form = CustomUserCreationForm()

    return render(request, 'store/register_page.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login-page')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try: 
            user = User.objects.get(email__iexact=email)

            new_password_reset = models.PasswordReset(user=user)
            new_password_reset.save()

            password_reset_url = reverse('reset-password', kwargs={'reset_id': str(new_password_reset.reset_id)})
            
            full_password_reset_url = f'{request.scheme}://{request.get_host()}{password_reset_url}'

            email_body = f'Reset your password using the link below:\n{full_password_reset_url}'

            email_message = EmailMessage(
                'Reset your password',
                email_body,
                settings.EMAIL_HOST_USER,
                [email] #email receiver
            )

            email_message.fail_silently = True
            email_message.send()

            return redirect('password-reset-sent', reset_id=new_password_reset.reset_id)

        except User.DoesNotExist:
            messages.error(request, f"No user with email '{email}' found")
            return redirect('forgot-password')

    return render(request, 'store/reset-password/forgot-password.html')

def password_reset_sent(request, reset_id):

    if models.PasswordReset.objects.filter(reset_id=reset_id).exists():
        return render(request, 'store/reset-password/password-reset-sent.html')
    else:
        messages.error(request, f"Invalid reset id")
        return redirect('forgot-password')


def reset_password(request, reset_id):
    try:
        reset_entry = models.PasswordReset.objects.get(reset_id=reset_id)

        if request.method == 'POST':
            password1 = request.POST.get('new_password1')
            password2 = request.POST.get('new_password2')

            password_have_error = False

            if password1 != password2:
                password_have_error = True
                messages.error(request, f"Password does not match")
            if len(password1) < 8:
                password_have_error = True
                messages.error(request, f"Password must atleast 8 characters")

            expiration_time = reset_entry.created_when + timezone.timedelta(minutes=10)
            if timezone.now() > expiration_time:
                password_have_error = True
                reset_entry.delete()
                messages.error(request, f"Reset Link has expired")
                
            if not password_have_error:
                user = reset_entry.user
                user.set_password(password1)
                user.save()
                reset_entry.delete()

                messages.success(request, f"Password successfully reset")
                return redirect('login-page')
            else:
                return redirect('reset-password', reset_id=str(reset_entry.reset_id))

    except models.PasswordReset.DoesNotExist:
        messages.error(request, f"Invalid reset id")
        return redirect('forgot-password')
    
    return render(request, 'store/reset-password/reset-password.html', {'reset_id': str(reset_entry.reset_id)})
