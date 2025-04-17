from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth.models import User
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Avg, Count
from django.utils import timezone
from django.conf import settings
from django.db import models
import uuid


class Category(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.URLField(max_length=500, blank=True, null=True)
    additional_images = models.JSONField(blank=True, null=True)

    is_featured = models.BooleanField(default=False)
    discount_percentage = models.PositiveIntegerField(default=0)
    buyers_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    @property
    def is_on_sale(self):
        return self.discount_percentage > 0

    @property
    def discounted_price(self):
        if self.is_on_sale:
            discounted = self.price * (Decimal(1) - Decimal(self.discount_percentage) / Decimal(100))
            return discounted.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return self.price

    @property
    def buyers_count_display(self):
        count = self.buyers_count
        if count >= 1_000_000:
            return f"{count / 1_000_000:.1f}M"
        elif count >= 1_000:
            return f"{count / 1_000:.1f}K"
        return str(count)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @property
    def review_count(self):
        return self.reviews.aggregate(count=Count('id'))['count'] or 0

    @property
    def average_rating(self):
        return self.reviews.aggregate(Avg('rating'))['rating__avg'] or 0

class PromoCodeUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    promo_code = models.ForeignKey('PromoCode', on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'promo_code')

class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percentage = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    active = models.BooleanField(default=True)
    expiration_date = models.DateTimeField(null=True, blank=True)
    max_uses_per_user = models.PositiveIntegerField(null=True, blank=True)  # Null = unlimited per user

    def is_valid_for_user(self, user):
        if self.expiration_date and self.expiration_date <= timezone.now():
            if self.active:
                self.active = False
                self.save(update_fields=["active"])
            return False

        # Count user uses
        used_count = PromoCodeUsage.objects.filter(user=user, promo_code=self).count()
        if self.max_uses_per_user is not None and used_count >= self.max_uses_per_user:
            return False

        return self.active

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    @property
    def get_total(self):
        return self.product.discounted_price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username} - {self.status}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=20, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x{self.quantity} for Order #{self.order.id}"

class PaymentMethod(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='Pending')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.payment_method} - {self.payment_id}"

class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reset_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_when = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Password reset for {self.user.username} at {self.created_when}'
    
class ShippingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    user_profile = models.ImageField(upload_to='images/', blank=True, null=True)

    def __str__(self):
        return f'{self.address}, {self.country}'

class ProductReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
    
    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name}"
    
