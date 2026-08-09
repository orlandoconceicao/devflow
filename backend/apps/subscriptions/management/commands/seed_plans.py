from django.core.management.base import BaseCommand

from apps.subscriptions.models import Plan


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for slug, name, price in (
            ("free", "Free", "0.00"),
            ("pro", "DevFlow Pro", "25.00"),
        ):
            Plan.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "price": price,
                    "billing_interval": Plan.Interval.MONTHLY,
                    "is_active": True,
                },
            )
        self.stdout.write(self.style.SUCCESS("Planos sincronizados."))
