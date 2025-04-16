from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, ForgotPassword
from django.contrib.auth.forms import SetPasswordForm
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from main import settings
from . import models
import pycountry


##################################################################################
def home(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                login(request, user)
                return redirect('store_home')
            else:
                messages.error(request, 'Incorrect password.')
        except User.DoesNotExist:
            messages.error(request, 'User does not exist.')

        return redirect('login-page')
    # products = models.Product.objects.filter(is_featured=True)[:6]
    products = models.Product.objects.all()[:6]
    return render(request, 'store/home.html', {'products': products})

@login_required(login_url='/login')
def about_view(request):
    return render(request, 'store/about.html')

@login_required(login_url='/login')
def contact_view(request):
    return render(request, 'store/contact.html')

##################################################################################
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
            
    return render(request, 'store/authentication-page/login_page.html')

def register_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login-page')
    else:
        form = CustomUserCreationForm()

    return render(request, 'store/authentication-page/register_page.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('store_home')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try: 
            # Check if the user exists
            user = User.objects.get(email__iexact=email)

            # Create a password reset record
            new_password_reset = models.PasswordReset(user=user)
            new_password_reset.save()

            # Generate password reset URL
            password_reset_url = reverse('reset-password', kwargs={'reset_id': str(new_password_reset.reset_id)})
            full_password_reset_url = f'{request.scheme}://{request.get_host()}{password_reset_url}'

            # Email body (can be plain text or HTML)
            email_body = f'''
                <p>Click the link below to reset your password:</p>
                <p><a href="{full_password_reset_url}">Reset your password</a></p>
                <p>The link will expire in 10 minutes.</p>
            '''

            # Send the email
            email_message = EmailMessage(
                'Reset your password',
                email_body,
                settings.EMAIL_HOST_USER,
                [email]  # Receiver's email
            )

            # Set content type to HTML for better formatting
            email_message.content_subtype = "html"

            # Send email and handle potential error
            email_message.send(fail_silently=False)

            # Redirect to a page notifying user that an email has been sent
            return redirect('password-reset-sent', reset_id=new_password_reset.reset_id)

        except User.DoesNotExist:
            messages.error(request, f"No user with email '{email}' found")
            return redirect('forgot-password')
        except Exception as e:
            # Catch other errors (e.g., email failure)
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('forgot-password')

    return render(request, 'store/authentication-page/reset-password/forgot-password.html')

def password_reset_sent(request, reset_id):

    if models.PasswordReset.objects.filter(reset_id=reset_id).exists():
        return render(request, 'store/authentication-page/reset-password/password-reset-sent.html')
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
    
    return render(request, 'store/authentication-page/reset-password/reset-password.html', {'reset_id': str(reset_entry.reset_id)})

@login_required(login_url='/login')
def change_password_view(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user
        if user.check_password(current_password):
            
            password_have_error = False

            if new_password != confirm_password:
                password_have_error = True
                messages.error(request, f"Password does not match")
            if len(new_password) < 8:
                password_have_error = True
                messages.error(request, f"Password must atleast 8 characters")

            if not password_have_error:
                user.set_password(new_password)
                user.save()
                login(request, user)
                return redirect('profile-page')
        else:
            messages.error(request, 'Incorrect password.')

    return render(request, 'store/authentication-page/reset-password/change-password.html')

##################################################################################
@login_required(login_url='/login')
def profile_view(request):
    user_address, created = models.ShippingAddress.objects.get_or_create(user=request.user)
    try:
        orders = models.Order.objects.filter(user=request.user)
    except models.Order.DoesNotExist:
        orders = None
    
    return render(request, 'store/profile-page.html', {'user_address': user_address, 'orders': orders})

@login_required(login_url='/login')
def edit_profile_view(request):
    user_address, created = models.ShippingAddress.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_address.full_name = request.POST.get('full_name')
        user_address.phone = request.POST.get('phone')
        user_address.address = request.POST.get('address')
        user_address.postal_code = request.POST.get('postal_code')
        user_address.country = request.POST.get('country')

        profile = request.FILES.get('profile_picture')
        if profile:
            user_address.user_profile = profile

        user_address.save()
        return redirect('profile-page')
    
    complete_countries = sorted([(c.alpha_2, c.name) for c in pycountry.countries], key=lambda x: x[1])

    context = {'user_address': user_address, 'countries': complete_countries}

    return render(request, 'store/edit-profile-page.html', context)

##################################################################################
@login_required(login_url='/login')
def product_view(request):
    category = models.Category.objects.all()
    selected_category = request.GET.get('category')
    products = models.Product.objects.filter(category__name=selected_category) if selected_category else models.Product.objects.all()

    #page view
    paginator = Paginator(products, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj.object_list, 
        'categories': category, 
        'selected_category': selected_category, 
        'page_obj': page_obj,
        'show_pagination': paginator.num_pages > 1,
    }

    return render(request, 'store/products.html', context)

@login_required(login_url='/login')
def product_details(request, product_id):
    product = models.Product.objects.get(id=product_id)
    cart_item_exist = models.CartItem.objects.filter(user=request.user, product=product).exists()

    context = {'product':product, 'cart_item_exist': cart_item_exist}
    return render(request, 'store/product-detail.html', context)

##################################################################################
@login_required(login_url='/login')
def cart_view(request):
    cart_items = models.CartItem.objects.filter(user=request.user)
    sub_total = 0
    for item in cart_items:
        sub_total += item.product.price * item.quantity
    shipping = 120 
    to_pay = sub_total + shipping

    context = {'cart_items': cart_items, 'sub_total': sub_total, 'to_pay': to_pay, 'shipping': shipping}
    return render(request, 'store/cart.html', context)

@login_required(login_url='/login')
def add_to_cart(request, product_id):
    if request.method == 'POST':
        quantity = request.POST.get('quantity', 1)
        product = models.Product.objects.get(id=product_id)
        cart_item, created = models.CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += 1
            cart_item.save()

    return redirect(request.META.get('HTTP_REFERER', 'default-redirect-url'))

@login_required(login_url='/login')
def remove_from_cart(request, product_id):
    if request.method == 'POST':
        item = models.CartItem.objects.filter(id=product_id, user=request.user).first()
        if item:
            item.delete()
    return redirect('cart-view')

@login_required(login_url='/login')
def update_cart(request, product_id):
    if request.method == 'POST':
        quantity = request.POST.get('quantity')

        product = models.Product.objects.get(id=product_id)
        cart_item = models.CartItem.objects.get(user=request.user, product=product)

        try:
            cart_item.quantity = quantity
            cart_item.save()
        except models.CartItem.DoesNotExist:
            pass
    return redirect('cart-view')

##################################################################################
@login_required(login_url='/login')
def checkout_view(request):
    cart_items = models.CartItem.objects.filter(user=request.user)
    user_address, created = models.ShippingAddress.objects.get_or_create(user=request.user)
    
    sub_total = 0
    for item in cart_items:
        sub_total += item.product.price * item.quantity
    shipping = 120 
    to_pay = sub_total + shipping

    if request.method == 'POST':
        if not user_address.full_name or not user_address.address:
            print('hello world')
            messages.error(request, "Please add a shipping address before placing your order.")
            return redirect('checkout-view')
        
        notes = request.POST.get('notes')
        order = models.Order.objects.create(
                user=request.user,
                user_note=notes,
        )

        total_price = 0
        for item in cart_items:
            models.OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
                total_price=item.quantity * item.product.price
            )
            total_price += item.product.price * item.quantity

        order.total_price = total_price
        order.save()

        cart_items.delete()

        return redirect('order-success-page')

    context = {'cart_items': cart_items, 'user_address': user_address, 'sub_total': sub_total, 'shipping': shipping, 'to_pay': to_pay}
    return render(request, 'store/checkout-page.html', context)

@login_required(login_url='/login')
def order_success_page(request):
    order = models.Order.objects.filter(user=request.user).order_by('-created_at').first()
    if not order:
        return redirect('store_home')
    
    return render(request, 'store/order-success-page.html', {'order': order})

@login_required(login_url='/login')
def order_details_view(request, order_id):
    order = get_object_or_404(models.Order, id=order_id, user=request.user)
    
    user_address = models.ShippingAddress.objects.get(user=request.user)
    
    context = {
        'order': order,
        'order_items': order.order_items.all(),
        'user_address': user_address
    }

    return render(request, 'store/order-details.html', context)

##################################################################################

@login_required(login_url='/login')
def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        email_subject = f"New Contact Form Submission: {subject}"
        email_body = (
            f"Dear Site Owner,\n\n"
            f"You have received a new message from your contact form.\n\n"
            f"Sender's Name: {name}\n"
            f"Sender's Email: {email}\n"
            f"Subject: {subject}\n\n"
            f"Message:\n{message}\n\n"
            f"Best regards,\n"
            f"Your Website Contact Form"
        )

        send_mail(
            email_subject,
            email_body,
            email,
            [settings.EMAIL_HOST_USER],
            fail_silently=False,
        )

        messages.success(request, "Thank you for contacting us. We will get back to you shortly!")
        return redirect('contact')

    return render(request, 'store/contact.html')

@login_required(login_url='/login')
def add_review(request, order_id):
    #ON WORK
    order = get_object_or_404(models.Order, id=order_id)
    if request.method == 'POST':
        review = request.POST.get('review')
        rating = request.POST.get('rating')
  
    return render(request, 'store/add-review-page.html', {'order': order})

def search_product(request):
    products = []
    query = ''

    if request.method == 'POST':
        query = request.POST.get('query', '')

        if query:
            name_matches = models.Product.objects.filter(name__icontains=query)
            if name_matches.exists():
                products = name_matches
            else:
                category = models.Category.objects.filter(name__iexact=query).first()
                if category:
                    products = models.Product.objects.filter(category=category)

    context = {'products': products, 'query': query}
    return render(request, 'store/search-results.html', context)
