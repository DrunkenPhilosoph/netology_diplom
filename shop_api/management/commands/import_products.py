import yaml
from django.core.management.base import BaseCommand
from shop_api.models import Shop, Category, Product  # Импортируйте ваши модели

class Command(BaseCommand):
    help = 'Import products from YAML file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the YAML file')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']

        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)

        # Получаем или создаем магазин
        shop_name = data.get('shop', '')
        shop, created = Shop.objects.get_or_create(name=shop_name)

        # Импортируем категории
        category_map = {}
        for category in data.get('categories', []):
            category_obj, created = Category.objects.get_or_create(
                id=category['id'], name=category['name'])
            category_map[category['id']] = category_obj

        # Импортируем товары
        for item in data.get('goods', []):
            product, created = Product.objects.update_or_create(
                id=item['id'],
                defaults={
                    'shop': shop,
                    'category': category_map.get(item['category']),
                    'model': item['model'],
                    'name': item['name'],
                    'price': item['price'],
                    'price_rrc': item['price_rrc'],
                    'quantity': item['quantity'],
                    'parameters': item['parameters']
                }
            )

        self.stdout.write(self.style.SUCCESS('Data imported successfully.'))