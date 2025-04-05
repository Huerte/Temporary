from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .forms import CustomUserCreationForm
from django.shortcuts import render, redirect
from django.contrib import messages
from . import models

@login_required(login_url='/login')
def home(request):
    return render(request, 'store/home.html')

def login_user(request):
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
           user = models.CustomUser.objects.get(username=username)
        except:
            messages.error(request, 'User does not exists.')
            return redirect('store_home')
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('login-page')
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
    return redirect('store_home')

def forgot_password(request):
    if request.method == 'POST':
        pass
    else:
        pass

    return render(request, 'store/password-reset.html')