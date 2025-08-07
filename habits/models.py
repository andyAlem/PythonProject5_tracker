from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Habit(models.Model):
    """Класс привычки."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    place = models.CharField(max_length=255)
    time = models.TimeField()
    action = models.CharField(max_length=255)
    is_pleasant = models.BooleanField(default=False)
    linked_habit = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL
    )
    reward = models.CharField(max_length=255, blank=True, null=True)
    duration = models.PositiveIntegerField(help_text="Duration in seconds")
    frequency = models.PositiveIntegerField(default=1)
    is_public = models.BooleanField(default=False)

    def clean(self):
        """Проверка валидности привычки."""
        if self.reward and self.linked_habit:
            raise ValidationError(
                "Нельзя одновременно указать вознаграждение и связанную привычку."
            )

        if self.duration is not None and self.duration > 120:
            raise ValidationError("Время выполнения не может превышать 120 секунд.")

        if self.linked_habit and not self.linked_habit.is_pleasant:
            raise ValidationError("Связанная привычка должна быть приятной.")

        if self.is_pleasant:
            if self.reward or self.linked_habit:
                raise ValidationError(
                    "Приятная привычка не может иметь вознаграждение или связанную привычку."
                )

        if self.frequency is not None and self.frequency > 7:
            raise ValidationError(
                "Нельзя выполнять привычку реже одного раза в 7 дней."
            )

    def __str__(self):
        return self.action
