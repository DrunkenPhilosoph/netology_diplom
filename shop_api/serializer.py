from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Shop, Category, Product, Cart, CartItem, Order, OrderItem, Address, CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'user_type', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}  # Делаем поле email обязательным
        }

    def create(self, validated_data):
        user_type = validated_data.pop('user_type')
        user = CustomUser.objects.create_user(**validated_data)
        user.user_type = user_type
        user.save()
        return user

class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'name']  # Исключаем поле user, чтобы оно не требовалось в запросе

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        return super().create(validated_data)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']  # Исключаем поле shop, чтобы оно не требовалось в запросе

    def create(self, validated_data):
        request = self.context.get('request')
        shop = request.user.shop if request and hasattr(request, 'user') else None

        # Проверяем, существует ли категория с таким именем для данного магазина
        if Category.objects.filter(name=validated_data['name'], shop=shop).exists():
            raise ValidationError({"name": "Category with this name already exists for this shop."})

        validated_data['shop'] = shop
        return super().create(validated_data)


class ProductSerializer(serializers.ModelSerializer):
    shop = serializers.CharField(write_only=True)  # Принимаем название магазина как строку
    category = serializers.CharField(write_only=True)  # Принимаем название категории как строку

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'price_rrc', 'quantity', 'model', 'category', 'parameters', 'shop']

    def validate(self, data):
        # Получаем объект магазина по названию
        try:
            shop = Shop.objects.get(name=data['shop'])
        except Shop.DoesNotExist:
            raise serializers.ValidationError({"shop": "Shop with this name does not exist."})

        # Проверяем существование категории для данного магазина
        try:
            category = Category.objects.get(name=data['category'], shop=shop)
        except Category.DoesNotExist:
            # Если категория не существует, создаем новую категорию
            category = Category.objects.create(name=data['category'], shop=shop)

        # Устанавливаем объекты вместо строк
        data['shop'] = shop
        data['category'] = category
        return data

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = '__all__'


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = '__all__'


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items']


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'created_at', 'status', 'total_amount', 'address', 'items']