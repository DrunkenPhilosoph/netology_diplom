from django.urls import path, include
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, OrderViewSet, CartViewSet, AddressViewSet, CategoryViewSet, ShopViewSet, \
    CustomUserViewSet

router = DefaultRouter()
router.register(r'users', CustomUserViewSet)
router.register(r'shops', ShopViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)
router.register(r'carts', CartViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'addresses', AddressViewSet)


urlpatterns = [
    path('', include(router.urls)),
]