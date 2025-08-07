import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestUserRegistration:
    """Класс для тестирования регистрации пользователей."""

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("users:register")

    def test_register_user_success(self):
        """Тестирование успешной регистрации пользователя."""
        data = {
            "email": "testuser@example.com",
            "password": "strongpassword123",
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert "access" in response.data
        assert "refresh" in response.data
        assert User.objects.filter(email=data["email"]).exists()

    def test_register_user_existing_email(self):
        """Тестирование регистрации пользователя с существующим email."""
        User.objects.create_user(email="testuser@example.com", password="12345678")
        data = {
            "email": "testuser@example.com",
            "password": "anotherpassword",
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data


@pytest.mark.django_db
class TestUserLogin:
    """Класс для тестирования авторизации пользователей."""

    def setup_method(self):
        """Настройка тестирования."""
        self.client = APIClient()
        self.url = reverse("users:login")
        self.user = User.objects.create_user(
            email="loginuser@example.com", password="password123"
        )

    def test_login_success(self):
        """Тестирование успешной авторизации пользователя."""
        data = {
            "email": self.user.email,
            "password": "password123",
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_fail_wrong_password(self):
        """Тестирование авторизации пользователя с неправильным паролем."""
        data = {
            "email": self.user.email,
            "password": "wrongpassword",
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
