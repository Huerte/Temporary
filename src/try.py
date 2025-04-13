import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
django.setup()

from store.models import Product
product = Product.objects.get(id=1)
print(product.discount_percentage)
