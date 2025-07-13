from rest_framework import permissions


class IsOwnerOrReadOnlyPublic(permissions.BasePermission):
    """
    Позволяет:
    - читать публичные привычки всем;
    - читать и изменять свои привычки владельцу;
    - запрещает редактировать чужие привычки.
    """

    def has_object_permission(self, request, view, obj):
        """Определяет права доступа по объекту."""
        if request.method in permissions.SAFE_METHODS:
            return obj.is_public or obj.user == request.user
        return obj.user == request.user
