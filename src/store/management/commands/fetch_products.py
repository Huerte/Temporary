from django.core.management.base import BaseCommand
import requests
from decimal import Decimal
from django.core.files.base import ContentFile
from django.core.files.temp import NamedTemporaryFile
from django.core.files import File
from django.utils.text import slugify
from store.models import Product, Category


def fetch_products():
    response = requests.get('https://api.escuelajs.co/api/v1/products')
    data = response.json()

    for item in data:
        cat_name = item['category']['name']
        category, _ = Category.objects.get_or_create(name=cat_name)

        product_name = item['title']
        price = Decimal(item['price'])
        description = item.get('description', '')
        image_url = item['images'][0] if item['images'] else None

        product, created = Product.objects.get_or_create(
            name=product_name,
            defaults={
                'category': category,
                'description': description,
                'price': price,
                'image': image_url,  # Store image URL
            }
        )

        if created:
            print(f"Product created: {product_name} with image URL: {image_url}")

class Command(BaseCommand):
    help = 'Fetch products from API and store in database'

    def handle(self, *args, **kwargs):
        fetch_products()
        self.stdout.write(self.style.SUCCESS('Products fetched successfully'))
