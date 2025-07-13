from django.db import models
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Habit
from .serializers import HabitSerializer


class IsOwnerOrReadOnlyPublic(permissions.BasePermission):
    """
    Позволяет:
    - читать публичные привычки всем;"""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return obj.is_public or obj.user == request.user
        return obj.user == request.user


class HabitViewSet(viewsets.ModelViewSet):
    """Представление привычек"""

    queryset = Habit.objects.all()
    serializer_class = HabitSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsOwnerOrReadOnlyPublic,
    ]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Habit.objects.filter(models.Q(is_public=True) | models.Q(user=user))
        else:
            return Habit.objects.filter(is_public=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"], url_path="public")
    def public_habits(self, request):
        public_habits = Habit.objects.filter(is_public=True)
        serializer = self.get_serializer(public_habits, many=True)
        return Response(serializer.data)
