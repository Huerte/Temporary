from django.contrib import admin
from .models import *

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'discount_percentage', 'is_on_sale', 'buyers_count', 'is_featured')
    fields = ('name', 'category', 'description', 'price', 'image', 'discount_percentage', 'buyers_count', 'is_featured')
    search_fields = ['name', 'category__name']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'is_paid', 'status', 'created_at']
    list_filter = ['status', 'is_paid', 'created_at']
    search_fields = ['user__username']
    inlines = [OrderItemInline]
    readonly_fields = ['created_at']

    fields = ('user', 'status', 'is_paid', 'user_note', 'created_at')


admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(CartItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(ShippingAddress)
admin.site.register(PaymentMethod)
admin.site.register(PasswordReset)
admin.site.register(ProductReview)