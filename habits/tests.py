import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from habits.models import Habit

User = get_user_model()


@pytest.mark.django_db
class TestHabitModelValidation:
    """Класс для тестирования модели Habit"""

    def setup_method(self):
        """Создаем пользователя и приятную привычку"""
        self.user = User.objects.create_user(
            email="user@example.com", password="testpass"
        )
        self.pleasant_habit = Habit.objects.create(
            user=self.user,
            place="Park",
            time="10:00",
            action="Walk",
            is_pleasant=True,
            duration=60,
            frequency=1,
        )

    def test_valid_habit(self):
        """Тестирование корректности создания приятной привычки"""
        habit = Habit(
            user=self.user,
            place="Gym",
            time="08:00",
            action="Workout",
            duration=90,
            frequency=3,
        )
        habit.clean()  # Should not raise

    def test_reward_and_linked_habit_error(self):
        """Тестирование ошибки при одновременном указании вознаграждения и связанной привычки"""
        habit = Habit(
            user=self.user,
            place="Home",
            time="09:00",
            action="Meditate",
            duration=60,
            frequency=1,
            reward="Tea",
            linked_habit=self.pleasant_habit,
        )
        with pytest.raises(
            ValidationError, match="Нельзя одновременно указать вознаграждение"
        ):
            habit.clean()

    def test_duration_too_long(self):
        """Тестирование ошибки при превышении времени выполнения привычки"""
        habit = Habit(
            user=self.user,
            place="Home",
            time="07:00",
            action="Yoga",
            duration=130,
            frequency=1,
        )
        with pytest.raises(
            ValidationError, match="Время выполнения не может превышать 120 секунд"
        ):
            habit.clean()

    def test_linked_habit_not_pleasant(self):
        """Тестирование ошибки при связанной неприятной привычке"""
        not_pleasant = Habit.objects.create(
            user=self.user,
            place="Office",
            time="06:00",
            action="Work",
            is_pleasant=False,
            duration=30,
            frequency=1,
        )
        habit = Habit(
            user=self.user,
            place="Home",
            time="09:00",
            action="Read",
            duration=60,
            frequency=1,
            linked_habit=not_pleasant,
        )
        with pytest.raises(
            ValidationError, match="Связанная привычка должна быть приятной"
        ):
            habit.clean()

    def test_pleasant_with_reward_or_linked(self):
        """Тестирование ошибки при приятной привычке с вознаграждением или связанной привычкой"""
        habit = Habit(
            user=self.user,
            place="Park",
            time="10:00",
            action="Smile",
            is_pleasant=True,
            duration=30,
            frequency=1,
            reward="Candy",
        )
        with pytest.raises(ValidationError, match="Приятная привычка не может иметь"):
            habit.clean()

    def test_frequency_too_high(self):
        """Тестирование ошибки при превышении частоты выполнения привычки"""
        habit = Habit(
            user=self.user,
            place="Park",
            time="12:00",
            action="Run",
            duration=60,
            frequency=10,
        )
        with pytest.raises(
            ValidationError, match="Нельзя выполнять привычку реже одного раза"
        ):
            habit.clean()


@pytest.mark.django_db
class TestHabitAPI:
    """Класс для тестирования API привычек"""

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="habituser@example.com", password="password123"
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse("habits:habit-list")

    def test_create_valid_habit(self):
        """Тестирование создания корректной привычки"""
        data = {
            "place": "Gym",
            "time": "08:00:00",
            "action": "Workout",
            "is_pleasant": False,
            "duration": 60,
            "frequency": 3,
            "is_public": True,
        }
        response = self.client.post(self.url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Habit.objects.filter(user=self.user, action="Workout").exists()

    def test_get_only_public_or_own_habits(self):
        """Тестирование получения только публичных привычек или своих привычек"""
        other_user = User.objects.create_user(
            email="other@example.com", password="otherpass"
        )

        # Приватная привычка другого пользователя — не должна быть доступна
        Habit.objects.create(
            user=other_user,
            place="Office",
            time="09:00",
            action="Check mail",
            is_pleasant=False,
            duration=30,
            frequency=1,
            is_public=False,
        )

        # Публичная привычка другого пользователя — должна быть доступна
        Habit.objects.create(
            user=other_user,
            place="Park",
            time="07:00",
            action="Run",
            is_pleasant=False,
            duration=20,
            frequency=2,
            is_public=True,
        )

        # Привычка текущего пользователя
        Habit.objects.create(
            user=self.user,
            place="Home",
            time="10:00",
            action="Read",
            is_pleasant=True,
            duration=15,
            frequency=1,
            is_public=False,
        )

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        actions = [habit["action"] for habit in response.data["results"]]
        assert "Run" in actions
        assert "Read" in actions
        assert "Check mail" not in actions
