from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import HabitViewSet

app_name = "habits"

router = DefaultRouter()  # https://www.django-rest-framework.org/api-guide/routers/
router.register(r"", HabitViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
