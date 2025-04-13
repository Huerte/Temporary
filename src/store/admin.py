from django.contrib import admin
from .models import *

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'discount_percentage', 'is_on_sale', 'buyers_count', 'is_featured')
    fields = ('name', 'category', 'description', 'price', 'image', 'discount_percentage', 'buyers_count', 'is_featured')
    search_fields = ['name', 'category__name']

admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(ShippingAddress)
admin.site.register(PaymentMethod)
admin.site.register(PasswordReset)

class CartItemInline(admin.TabularInline):
    model = Order.items.through
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'is_paid', 'status', 'created_at']
    list_filter = ['status', 'is_paid', 'created_at']
    search_fields = ['user__username']
    inlines = [CartItemInline]