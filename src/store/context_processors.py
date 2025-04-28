from .models import CartItem
import hashlib
from . import models

def cart_quantity(request):
    if request.user.is_authenticated:
        count = CartItem.objects.filter(user=request.user).count()
    else:
        count = 0
    return {'cart_item_quantity': count}

def product_in_cart(request):
    in_cart = {}

    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user).select_related('product')
        in_cart = {item.product.id for item in cart_items}
    
    return {'products_in_cart': in_cart}

def categories_context(request):
    all_categories = list(models.Category.objects.all())
    
    # Split into chunks of 4
    category_chunks = [all_categories[i:i+4] for i in range(0, len(all_categories), 4)]
    
    return {'category_chunks': category_chunks}

def get_color(username):
    colors = ["primary", "success", "danger", "warning", "info", "secondary"]
    hash_val = int(hashlib.md5(username.encode()).hexdigest(), 16)
    return colors[hash_val % len(colors)]

def avatar_color(request):
    if request.user.is_authenticated:
        color = get_color(request.user.username)
        return {"avatar_color": color}
    return {}
