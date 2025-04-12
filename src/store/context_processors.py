from .models import CartItem, Product

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