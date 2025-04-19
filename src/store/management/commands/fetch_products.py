from django.core.management.base import BaseCommand
import requests
from decimal import Decimal
from django.core.files.base import ContentFile
from django.core.files.temp import NamedTemporaryFile
from django.core.files import File
from django.utils.text import slugify
from store.models import Product, Category
from decimal import Decimal, InvalidOperation


def fetch_products():
    response = requests.get('https://api.escuelajs.co/api/v1/products')
    data = response.json()

    for item in data:
        cat_name = item['category']['name']
        category, _ = Category.objects.get_or_create(name=cat_name)

        product_name = item['title']
        price = Decimal(item['price'])
        
        try:
          price = Decimal(str(raw)).quantize(Decimal('0.01'))
        except InvalidOperation:
            print(f"❌ Bad price for product {item.get('id')!r}: {raw!r}")
            continue
        
        description = item.get('description', '')
        image_urls = item['images'] if item['images'] else []

        # Separate the first image as main image
        main_image_url = image_urls[0] if image_urls else None
        additional_image_urls = image_urls[1:] if len(image_urls) > 1 else []

        # Create or get the product
        product, created = Product.objects.get_or_create(
            name=product_name,
            defaults={
                'category': category,
                'description': description,
                'price': price,
                'image': main_image_url,
                'additional_images': additional_image_urls,
            }
        )


class Command(BaseCommand):
    help = 'Fetch products from API and store in database'

    def handle(self, *args, **kwargs):
        fetch_products()
        self.stdout.write(self.style.SUCCESS('Products fetched successfully'))
