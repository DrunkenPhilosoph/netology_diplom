from rest_framework.permissions import BasePermission

class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to allow only the owner of an object to edit or delete it.
    """
    def has_object_permission(self, request, view, obj):
        # Разрешены безопасные методы (GET, HEAD, OPTIONS)
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True

        # Разрешено только владельцу объявления редактировать или удалять его
        return obj.created_by == request.user