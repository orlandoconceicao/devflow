from django.db import migrations


def mark_legacy_records(apps, schema_editor):
    subscription = apps.get_model("subscriptions", "Subscription")
    payment_event = apps.get_model("subscriptions", "PaymentEvent")
    subscription.objects.filter(provider="stripe").update(provider="legacy")
    payment_event.objects.filter(provider="stripe").update(provider="legacy")


class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0002_subscription_canceled_at_subscription_provider_and_more")]

    operations = [
        migrations.RenameField(
            model_name="subscription",
            old_name="provider_customer_id",
            new_name="provider_payer_id",
        ),
        migrations.RunPython(mark_legacy_records, migrations.RunPython.noop),
    ]
