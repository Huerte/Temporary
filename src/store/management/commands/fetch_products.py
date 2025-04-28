from django.core.management.base import BaseCommand
import requests
from decimal import Decimal, InvalidOperation
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.utils.text import slugify
from store.models import Product, Category
from urllib.parse import urlparse
import os

def fetch_image(url):
    try:
        response = requests.get(url, verify=False, timeout=10) # Disable SSL verification
        response.raise_for_status()
        img_temp = NamedTemporaryFile(delete=True)
        img_temp.write(response.content)
        img_temp.flush()
        return img_temp
    except Exception as e:
        print(f"⚠️ Failed to download image {url}: {e}")
        return None

def fetch_products():
    urls = [
        'https://fakestoreapi.com/products',
        'https://dummyjson.com/products',
        'https://api.escuelajs.co/api/v1/products',
    ]

    for url in urls:
        try:
            response = requests.get(url, verify=False, timeout=10) # Disable SSL verification
            response.raise_for_status()
            data = response.json()
            items = data.get('products') or data
        except Exception as e:
            print(f"⚠️ Failed to fetch products from {url}: {e}")
            continue

        for item in items:
            cat_raw = item.get('category')
            cat_name = cat_raw['name'] if isinstance(cat_raw, dict) else str(cat_raw)
            cat_name = cat_name.strip().title()
            category, _ = Category.objects.get_or_create(name=cat_name)

            product_name = item.get('title') or item.get('name')
            description = item.get('description', '')
            raw_price = item.get('price')

            try:
                price = Decimal(str(raw_price)).quantize(Decimal('0.01'))
            except (InvalidOperation, TypeError, ValueError):
                print(f"❌ Skipping product {item.get('id')!r}: invalid price {raw_price!r}")
                continue

            raw_images = item.get('images') or item.get('image')
            images = raw_images if isinstance(raw_images, list) else [raw_images] if isinstance(raw_images, str) else []

            main_image_url = images[0] if images else None
            additional_image_urls = images[1:] if len(images) > 1 else []

            slug = slugify(product_name)[:50]  # Avoid very long slugs

            product, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': product_name,
                    'category': category,
                    'description': description,
                    'price': price,
                }
            )

            if created:
                if main_image_url:
                    img_temp = fetch_image(main_image_url)
                    if img_temp:
                        filename = os.path.basename(urlparse(main_image_url).path)
                        if not filename:
                            filename = f"{slug}.jpg"
                        product.image.save(filename, File(img_temp), save=True)
                        img_temp.close()

                # Save additional images if your Product model supports it
                if hasattr(product, 'additional_images') and additional_image_urls:
                    product.additional_images = additional_image_urls
                    product.save()

class Command(BaseCommand):
    help = 'Fetch products from API and store in database'

    def handle(self, *args, **kwargs):
        fetch_products()
        self.stdout.write(self.style.SUCCESS('✅ Products fetched successfully'))
