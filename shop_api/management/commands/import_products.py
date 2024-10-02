from django.core.management.base import BaseCommand
import yaml
from django.contrib.auth import get_user_model
from shop_api.models import Product, Shop, Category

CustomUser = get_user_model()

class Command(BaseCommand):
    help = 'Import products from YAML file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the YAML file')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)

                if not isinstance(data, dict):
                    self.stdout.write(self.style.ERROR('Invalid YAML format. Expected a dictionary.'))
                    return

                shop_name = data.get('shop')
                if not shop_name:
                    self.stdout.write(self.style.ERROR('Shop name is missing in the YAML file.'))
                    return

                try:
                    user = CustomUser.objects.get(username='admin')
                except CustomUser.DoesNotExist:
                    self.stdout.write(self.style.ERROR('User for shop association does not exist.'))
                    return

                shop, created = Shop.objects.get_or_create(name=shop_name, user=user)
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Shop "{shop.name}" created.'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Shop "{shop.name}" already exists.'))

                categories = data.get('categories', [])
                for category_data in categories:
                    category_id = category_data.get('id')
                    category_name = category_data.get('name')
                    if category_id and category_name:
                        category, created = Category.objects.get_or_create(
                            id=category_id,
                            shop=shop,
                            defaults={'name': category_name}
                        )
                        if created:
                            self.stdout.write(self.style.SUCCESS(f'Category "{category.name}" (ID: {category_id}) created for shop "{shop.name}".'))
                        else:
                            self.stdout.write(self.style.SUCCESS(f'Category "{category.name}" (ID: {category_id}) already exists for shop "{shop.name}".'))

                goods = data.get('goods', [])
                for item in goods:
                    category_id = item.get('category')
                    try:
                        category = Category.objects.get(id=category_id, shop=shop)
                    except Category.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'Category with ID {category_id} does not exist for shop "{shop.name}". Skipping product {item.get("name")}.'))
                        continue

                    product_id = item.get('id')
                    defaults = {
                        'name': item.get('name'),
                        'price': item.get('price'),
                        'price_rrc': item.get('price_rrc'),
                        'quantity': item.get('quantity'),
                        'parameters': item.get('parameters'),
                        'shop': shop,
                        'category': category,
                        'model': item.get('model'),
                    }

                    product, created = Product.objects.update_or_create(id=product_id, defaults=defaults)
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Product "{product.name}" created.'))
                    else:
                        self.stdout.write(self.style.SUCCESS(f'Product "{product.name}" updated.'))

        except yaml.YAMLError as exc:
            self.stdout.write(self.style.ERROR(f'Error parsing YAML file: {exc}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {e}'))
