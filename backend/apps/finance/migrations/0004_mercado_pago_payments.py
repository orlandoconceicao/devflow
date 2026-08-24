from django.db import migrations, models


def mark_legacy_records(apps, schema_editor):
    for model_name in ("InvoicePayment", "InvoicePaymentEvent"):
        model = apps.get_model("finance", model_name)
        model.objects.filter(provider="stripe").update(provider="legacy")


class Migration(migrations.Migration):
    dependencies = [("finance", "0003_invoice_project")]

    operations = [
        migrations.RenameField(
            model_name="invoicepayment",
            old_name="qr_code_url",
            new_name="qr_code",
        ),
        migrations.AlterField(
            model_name="invoicepayment",
            name="qr_code",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="invoicepayment",
            name="provider",
            field=models.CharField(default="mercado_pago", max_length=20),
        ),
        migrations.AlterField(
            model_name="invoicepaymentevent",
            name="provider",
            field=models.CharField(default="mercado_pago", max_length=20),
        ),
        migrations.RunPython(mark_legacy_records, migrations.RunPython.noop),
    ]
