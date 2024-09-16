from rest_framework.permissions import BasePermission

class IsShopUser(BasePermission):
    """
    Разрешение только для пользователей типа "магазин".
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'shop'


class IsOwnerOrReadOnly(BasePermission):
    """
    Разрешение для владельцев объектов. Только владельцы могут редактировать или удалять объект.
    """
    def has_object_permission(self, request, view, obj):
        # Разрешить чтение всем запросам
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        # Разрешить действия только владельцу объекта
        return obj.shop.user == request.user