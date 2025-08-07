import logging

import requests
from celery import shared_task
from django.conf import settings
from django.utils.timezone import localtime, now

from habits.models import Habit

logger = logging.getLogger(__name__)


@shared_task
def send_reminders():
    """Отправляет напоминания пользователю, если время совпадает с текущим временем"""
    current_time = localtime(now())
    logger.info(f"send_reminders running at {current_time}")
    habits = Habit.objects.filter(
        time__hour=current_time.hour, time__minute=current_time.minute
    )
    for habit in habits:
        chat_id = habit.user.telegram_chat_id
        logger.info(f"Sending reminder to chat_id={chat_id} for habit {habit.action}")
        if chat_id:
            message = f"Напоминание: {habit.action} в {habit.place}"
            url = (
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            )
            logger.info(f"Telegram token loaded: {settings.TELEGRAM_BOT_TOKEN[:5]}***")
            response = requests.post(url, data={"chat_id": chat_id, "text": message})
            logger.info(
                f"Telegram API response status: {response.status_code}, text: {response.text}"
            )


@shared_task
def send_test_message(chat_id):  # тестовое сообщение прошло успешно
    message = "Привет! Это тестовое сообщение из Celery"
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    logger.info(f"Sending test message to {chat_id}")

    try:
        response = requests.post(url, data={"chat_id": chat_id, "text": message})
        logger.info(f"Telegram API response: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
