from django.db.models import Sum, Avg, Q, F, Value, ExpressionWrapper, DecimalField
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, ForgotPassword
from django.contrib.auth.forms import SetPasswordForm
from django.views.decorators.http import require_POST
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.db.models.functions import Coalesce
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal
from main import settings
from . import models
import pycountry


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
    
    products = models.Product.objects.all()[:21] # products = models.Product.objects.filter(is_featured=True)[:6]

    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = models.ProductWishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
    
    return render(request, 'store/home.html', {'products': products, 'wishlist_product_ids': wishlist_product_ids})

def about_view(request):
    return render(request, 'store/about.html')

@login_required(login_url='/login')
def contact_view(request):
    return render(request, 'store/contact.html')

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

@login_required(login_url='/login')
def profile_view(request):
    user_address, created = models.ShippingAddress.objects.get_or_create(user=request.user)
    try:
        orders = models.Order.objects.filter(user=request.user)
        product_reviews = models.ProductReview.objects.filter(user=request.user)
        wishlist = models.ProductWishlist.objects.filter(user=request.user)
    except models.Order.DoesNotExist:
        orders = None
    
    return render(request, 'store/profile-page.html', {'user_address': user_address, 'orders': orders, 'product_reviews': product_reviews, 'wishlist': wishlist})

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

def product_view(request, category=None):
    products = models.Product.objects.all()
    categories = models.Category.objects.all()

    # Get filters
    selected_category = category or request.GET.get('category')
    search_query = request.GET.get('q')
    min_price = Decimal(request.GET.get('min_price', '0'))
    max_price = Decimal(request.GET.get('max_price', '1000'))
    sort_option = request.GET.get('sort', 'featured')

    # Base filters
    if selected_category and selected_category.lower() != 'all':
        products = products.filter(category__name=selected_category)

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Annotate discounted price & average rating
    discount_expr = ExpressionWrapper(
        F('price') * (Value(100) - F('discount_percentage')) / Value(100),
        output_field=DecimalField(max_digits=8, decimal_places=2)
    )
    products = products.annotate(
        discounted_price_db=discount_expr,
        avg_rating=Avg('reviews__rating')
    )

    # Price range filter
    products = products.filter(discounted_price_db__gte=min_price, discounted_price_db__lte=max_price)

    # Rating filters
    rating_q = Q()
    if 'five_star' in request.GET:
        rating_q |= Q(avg_rating__gte=5)
    if 'four_star' in request.GET:
        rating_q |= Q(avg_rating__gte=4)
    if 'three_star' in request.GET:
        rating_q |= Q(avg_rating__gte=3)

    if rating_q:
        products = products.filter(rating_q)

    # Sorting logic
    if sort_option == 'price-asc':
        products = products.order_by('discounted_price_db')
        sort_label = "Price: Low to High"
    elif sort_option == 'price-desc':
        products = products.order_by('-discounted_price_db')
        sort_label = "Price: High to Low"
    elif sort_option == 'rating':
        products = products.order_by('-avg_rating')
        sort_label = "Rating"
    elif sort_option == 'newest':
        products = products.order_by('-created_at')
        sort_label = "Newest"
    else:
        products = products.order_by('-is_featured')
        sort_label = "Featured"

    # Pagination
    paginator = Paginator(products, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    for product in page_obj:
        product.stars_range = range(1, 6)

    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = models.ProductWishlist.objects.filter(user=request.user).values_list('product_id', flat=True)

    context = {
        'products': page_obj.object_list,
        'categories': categories,
        'selected_category': selected_category,
        'page_obj': page_obj,
        'show_pagination': paginator.num_pages > 1,
        'min_price': min_price,
        'max_price': max_price,
        'sort_label': sort_label,
        'sort_option': sort_option,
        'wishlist_product_ids': wishlist_product_ids
    }

    return render(request, 'store/products.html', context)

def product_details(request, product_id):

    product = get_object_or_404(models.Product, id=product_id)
    product_reviews = models.ProductReview.objects.filter(product=product)

    wishlist_product_ids = []
    cart_item_exist = []
    can_review = []
    if request.user.is_authenticated:
        wishlist_product_ids = models.ProductWishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
        cart_item_exist = models.CartItem.objects.filter(user=request.user, product=product).exists()
        can_review = models.OrderItem.objects.filter(order__user=request.user, order__status='DELIVERED', product=product).exists()

    # Savings = original price - discounted price
    savings = product.price - product.discounted_price

    rounded_rating = round(product.average_ratings or 0, 1)
    full_stars = int(rounded_rating)
    half_star = 1 if (rounded_rating - full_stars) >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star

    related_products = models.Product.objects.filter(category=product.category).exclude(id=product.id)[:4]

    action = request.POST.get('action')
    if action == "add":
        add_to_wishlist(product_id)
    elif action == "remove":
        remove_from_wishlist(product_id)
        
    context = {
        'product': product,
        'product_reviews': product_reviews,
        'cart_item_exist': cart_item_exist,
        'savings': savings,
        'rounded_rating': rounded_rating,
        'full_stars': range(full_stars),
        'half_star': half_star,
        'empty_stars': range(empty_stars),
        'can_review': can_review,
        'related_products': related_products,
        'wishlist_product_ids': wishlist_product_ids
    }
    return render(request, 'store/product-detail.html', context)

@login_required(login_url='/login')
def cart_view(request):
    cart_items = models.CartItem.objects.filter(user=request.user)

    sub_total = sum(item.product.discounted_price * item.quantity for item in cart_items)

    promo_discount = request.session.get('promo_discount', 0)
    voucher_discount = (sub_total * promo_discount) // 100 if promo_discount else 0
    to_pay = sub_total - voucher_discount

    # Fetch user's shipping address
    try:
        user_address = models.ShippingAddress.objects.get(user=request.user)
    except models.ShippingAddress.DoesNotExist:
        user_address = None

    context = {
        'cart_items': cart_items if cart_items else [],
        'sub_total': sub_total,
        'to_pay': to_pay,
        'voucher_discount': voucher_discount,
        'user_address': user_address,
    }

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

        # AJAX request: return JSON to prevent full page reload
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            total_quantity = models.CartItem.objects.filter(user=request.user).aggregate(
                total=Sum('quantity')
            )['total'] or 0
            return JsonResponse({'success': True, 'quantity': cart_item.quantity, 'cart_total': total_quantity})


    return redirect(request.META.get('HTTP_REFERER', 'default-redirect-url'))

@login_required(login_url='/login')
def remove_from_cart(request, product_id):
    if request.method == 'POST':
        try:
            product = models.Product.objects.get(id=product_id)
            cart_item = models.CartItem.objects.get(user=request.user, product=product)
            cart_item.delete()
            return JsonResponse({'success': True})
        except models.CartItem.DoesNotExist:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})

@login_required(login_url='/login')
def update_cart(request, product_id):
    if request.method == 'POST':
        quantity = request.POST.get('quantity')
        try:
            product = models.Product.objects.get(id=product_id)
            cart_item = models.CartItem.objects.get(user=request.user, product=product)
            cart_item.quantity = quantity
            cart_item.save()
        except models.CartItem.DoesNotExist:
            pass

    if 'HTTP_REFERER' in request.META:
        request.session['last_page'] = request.META['HTTP_REFERER']
    
    return redirect(request.session.get('last_page', '/default-redirect-url'))

@require_POST
@login_required(login_url='/login')
def toggle_wishlist(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        try:
            product = models.Product.objects.get(id=product_id)
            wishlist_item, created = models.ProductWishlist.objects.get_or_create(user=request.user, product=product)
            if not created:
                wishlist_item.delete()
                in_wishlist = False
            else:
                in_wishlist = True
            return JsonResponse({'success': True, 'in_wishlist': in_wishlist})
        except models.Product.DoesNotExist:
            return JsonResponse({'success': False}, status=404)

@login_required(login_url='/login')
def add_to_wishlist(request, product_id):
    if request.method == 'POST':
        product = models.Product.objects.get(id=product_id)
        models.ProductWishlist.objects.get_or_create(user=request.user, product=product)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            in_wishlist = models.ProductWishlist.objects.filter(user=request.user, product=product).exists()
            return JsonResponse({'success': True, 'in_wishlist': in_wishlist})

    return redirect(request.META.get('HTTP_REFERER', 'default-redirect-url'))

@login_required(login_url='/login')
def remove_from_wishlist(request, product_id):
    if request.method == 'POST':
        models.ProductWishlist.objects.filter(user=request.user, product_id=product_id).delete()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            in_wishlist = models.ProductWishlist.objects.filter(user=request.user, product_id=product_id).exists()
            return JsonResponse({'success': True, 'in_wishlist': in_wishlist})

    return redirect(request.META.get('HTTP_REFERER', 'default-redirect-url'))

@login_required(login_url='/login')
def wishlist_view(request):
    wishlist_qs = models.ProductWishlist.objects.filter(user=request.user).select_related('product')
    products = [item.product for item in wishlist_qs]

    return render(request, 'store/wishlist-page.html', {'wishlist': products})

@login_required(login_url='/login')
def checkout_view(request):
    cart_items = models.CartItem.objects.filter(user=request.user)
    user_address, created = models.ShippingAddress.objects.get_or_create(user=request.user)
    promo_discount = request.session.get('promo_discount', 0)

    sub_total = sum(item.product.discounted_price * item.quantity for item in cart_items)

    shipping = 120 
    promo_discount = request.session.get('promo_discount', 0)
    voucher_discount = (sub_total * promo_discount) // 100 if promo_discount else 0

    to_pay = sub_total - voucher_discount + shipping

    if request.method == 'POST':
        if not user_address.full_name or not user_address.address:
            print('hello world')
            messages.error(request, "Please add a shipping address before placing your order.")
            return redirect('checkout-view')
        
        notes = request.POST.get('notes')

        promo_code_str = request.session.get('promo_code')
        promo_code = None

        if promo_code_str:
            try:
                promo_code = models.PromoCode.objects.get(code=promo_code_str, active=True)
            except models.PromoCode.DoesNotExist:
                promo_code = None


        order = models.Order.objects.create(
            user=request.user,
            user_note=notes,
            shipping_price=shipping,
            discount=voucher_discount,
            total_price=to_pay
        )

        if promo_code:
            models.PromoCodeUsage.objects.create(
                user=request.user,
                promo_code=promo_code,
                order=order
            )


        choosen_payment_method = request.POST.get('selected_payment')
        payment_method = models.PaymentMethod.objects.create(
            user=request.user, order=order,
            payment_method=choosen_payment_method,
            amount=to_pay, 
        )

        for item in cart_items:
            models.OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
                total_price=item.quantity * item.product.discounted_price
            )

        order.save()

        cart_items.delete()

        request.session['last_order_data'] = {
            'order_id': order.id,
            'voucher_discount': float(voucher_discount),
            'promo_code': request.session.get('promo_code'),
            'shipping': float(shipping),
            'to_pay': float(to_pay),
            'payment_method': payment_method.payment_method
        }


        request.session.pop('promo_discount', None)
        request.session.pop('promo_code', None)

        return redirect('order-success-page')

    context = {
        'cart_items': cart_items, 'user_address': user_address, 
        'sub_total': sub_total, 'shipping': shipping, 'to_pay': to_pay,
        'voucher_discount': voucher_discount
    }
    return render(request, 'store/checkout-page.html', context)

@login_required(login_url='/login')
def order_success_page(request):
    order_data = request.session.get('last_order_data', {})

    if not order_data:
        return redirect('store')

    order = get_object_or_404(models.Order, id=order_data.get('order_id'))

    order = get_object_or_404(models.Order, id=order_data.get('order_id'))

    payment = models.PaymentMethod.objects.filter(order=order).first()

    context = {
        'order': order,
        'order_items': order.order_items.all(),
        'voucher_discount': order_data.get('voucher_discount', 0),
        'promo_code': order_data.get('promo_code'),
        'shipping': order_data.get('shipping', 0),
        'total_price': order.total_price,
        'payment': payment,
    }

    return render(request, 'store/order-success-page.html', context)

@login_required(login_url='/login')
def order_details_view(request, order_id):
    order = get_object_or_404(models.Order, id=order_id, user=request.user)
    
    user_address = models.ShippingAddress.objects.get(user=request.user)
    payment_method = models.PaymentMethod.objects.get(order=order)

    promo_code_usage = models.PromoCodeUsage.objects.filter(order=order).first()
    promo_code = promo_code_usage.promo_code if promo_code_usage else None

    context = {
        'order': order,
        'order_items': order.order_items.all(),
        'user_address': user_address,
        'payment': payment_method,
        'promo_code': promo_code
    }

    return render(request, 'store/order-details.html', context)

@login_required(login_url='/login')
def apply_promo(request):
    if request.method == "POST":
        code = request.POST.get("promo_code", "").strip()

        if not code:
            request.session.pop('promo_code', None)
            request.session.pop('promo_discount', None)
            messages.info(request, "Promo code cleared.")
            return redirect(request.META.get('HTTP_REFERER', 'default-redirect-url'))

        try:
            promo = models.PromoCode.objects.get(code__iexact=code)
            
            # Check if promo code is valid
            if promo.is_valid_for_user(request.user):
                # Store promo code and discount percentage in session for cart view
                request.session['promo_code'] = promo.code
                request.session['promo_discount'] = promo.discount_percentage
                messages.success(request, f"Promo code '{promo.code}' applied successfully! You get a {promo.discount_percentage}% discount.")
            else:
                messages.error(request, "Promo code is expired, inactive, or you've exceeded the usage limit.")
        except models.PromoCode.DoesNotExist:
            messages.error(request, "Invalid promo code.")
    
    return redirect(request.META.get('HTTP_REFERER', 'default-redirect-url'))

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

@login_required(login_url='/login')
def product_review_view(request, order_id):
    order = get_object_or_404(models.Order, id=order_id)
    reviewed_products_id = models.ProductReview.objects.filter(
        user=request.user, 
        product__in=[item.product for item in order.order_items.all()]).values_list('product_id', flat=True)
    
    return render(request, 'store/product-review-page.html', {'order': order, 'reviewed_product_ids': reviewed_products_id})

@login_required(login_url='/login')
def add_review(request, product_id):
    if request.method == 'POST':
        rating = request.POST.get('rating')
        review = request.POST.get('review')

        product = models.Product.objects.get(id=product_id)

        product_review = models.ProductReview.objects.create(
            product=product, user = request.user,
            rating=rating, review=review
        )
        product_review.save()

    return redirect(request.META.get('HTTP_REFERER', 'default-redirect-url'))