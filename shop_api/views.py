from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from .models import Shop, Category, Product, Cart, CartItem, Order, OrderItem, Address, CustomUser
from .permissions import IsShopUser, IsOwnerOrReadOnly
from .serializer import (
    ShopSerializer, CategorySerializer, ProductSerializer,
    CartSerializer, CartItemSerializer, OrderSerializer, OrderItemSerializer, AddressSerializer, CustomUserSerializer
)

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]
        elif self.action == 'list':
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class ShopViewSet(viewsets.ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.user_type == 'shop':
            serializer.save(user=self.request.user)
        else:
            raise PermissionDenied({'Ошибка': 'Покупатель не может создать магазин'})


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated(), IsShopUser(), IsOwnerOrReadOnly()]

    def get_queryset(self):
        if self.request.method == 'GET':
            return Product.objects.all()
        elif self.request.user.user_type == 'shop':
            return Product.objects.filter(shop__user=self.request.user)
        return Product.objects.none()

    def perform_create(self, serializer):
        serializer.save(shop=self.request.user.shop)




class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsShopUser, IsOwnerOrReadOnly]

    def get_queryset(self):
        if self.request.user.user_type == 'shop':
            return Category.objects.filter(shop__user=self.request.user)
        return Category.objects.none()

    def perform_create(self, serializer):
        shop = self.request.user.shop
        if Category.objects.filter(name=serializer.validated_data['name'], shop=shop).exists():
            raise ValidationError({'Ошибка': 'Эта категория уже есть у магазина'})

        serializer.save(shop=shop)

    def get_queryset(self):
        if self.request.user.user_type == 'shop':
            return Category.objects.filter(shop__user=self.request.user)
        return Category.objects.none()

    def perform_create(self, serializer):

        if self.request.user.user_type == 'shop':
            serializer.save(shop=self.request.user.shop)
        else:
            return Response({'Ошибка': 'Только магазины могут создавать категорию'}, status=status.HTTP_403_FORBIDDEN)


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Создаем корзину для пользователя, если ее нет
        Cart.objects.get_or_create(user=self.request.user)
        return Cart.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def add_product(self, request):
        cart = self.get_object()
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'detail': 'Продукт не найден.'}, status=404)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        cart_item.quantity += int(quantity)
        cart_item.save()

        return Response({'status': 'Товар успешно добавлен в корзину'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def remove_product(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get('product_id')

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'detail': 'Товар не существует.'}, status=404)

        try:
            cart_item = CartItem.objects.get(cart=cart, product=product)
        except CartItem.DoesNotExist:
            return Response({'detail': 'Товар не найден в корзине.'}, status=404)

        cart_item.delete()

        return Response({'status': 'Товар удален из корзины'})


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def confirm_order(self, request):
        order = self.get_object()
        order.status = 'confirmed'
        order.save()
        print(order.user.email)
        send_mail(
            'Order Confirmation',
            f'Your order #{order.id} has been confirmed.',
            'admin@market.ru',
            [order.user.email],

            fail_silently=False,
        )

        return Response({'status': 'Заказ оформлен детали заказа отправлены на почту'})


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]