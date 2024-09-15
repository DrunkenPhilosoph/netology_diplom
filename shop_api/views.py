from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token  # Импортируем модель токенов
from django.core.mail import send_mail
from .models import Shop, Category, Product, Cart, CartItem, Order, OrderItem, Address, CustomUser
from .serializer import (
    ShopSerializer, CategorySerializer, ProductSerializer,
    CartSerializer, CartItemSerializer, OrderSerializer, OrderItemSerializer, AddressSerializer, CustomUserSerializer
)


# Viewset для пользователей
class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    # Определяем разрешения для каждого действия
    def get_permissions(self):
        if self.action == 'create':
            # Разрешить доступ к методу create (регистрация) для всех
            permission_classes = [AllowAny]
        elif self.action == 'list':
            # Разрешить доступ к методу list только администраторам
            permission_classes = [IsAdminUser]
        else:
            # Для всех остальных действий требуется аутентификация
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
            return Response({'error': 'Only shops can create a shop'}, status=status.HTTP_403_FORBIDDEN)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.user_type == 'shop':
            shop = Shop.objects.get(user=self.request.user)
            serializer.save(shop=shop)
        else:
            return Response({'error': 'Only shops can create products'}, status=status.HTTP_403_FORBIDDEN)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def add_product(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)

        product = Product.objects.get(id=product_id)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        cart_item.quantity += int(quantity)
        cart_item.save()

        return Response({'status': 'Product added to cart'})

    @action(detail=True, methods=['post'])
    def remove_product(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get('product_id')

        product = Product.objects.get(id=product_id)
        cart_item = CartItem.objects.get(cart=cart, product=product)
        cart_item.delete()

        return Response({'status': 'Product removed from cart'})


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def confirm_order(self, request, pk=None):
        order = self.get_object()
        order.status = 'confirmed'
        order.save()

        # Отправка email пользователю
        send_mail(
            'Order Confirmation',
            f'Your order #{order.id} has been confirmed.',
            'admin@shop.com',
            [order.user.email],
            fail_silently=False,
        )

        return Response({'status': 'Order confirmed and email sent'})


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]