from django.core.management.base import BaseCommand
from django_celery_beat.models import IntervalSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Create periodic tasks for reminders"

    def handle(self, *args, **options):
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES,
        )

        task, created = PeriodicTask.objects.get_or_create(
            interval=schedule,
            name="Check habits for reminders every minute",
            task="telegram_bot.tasks.send_reminders",
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Periodic task created"))
        else:
            self.stdout.write("Periodic task already exists")
