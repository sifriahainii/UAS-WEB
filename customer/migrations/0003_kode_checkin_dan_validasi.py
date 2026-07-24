import secrets
from django.db import migrations, models


def populate_codes(apps, schema_editor):
    Pendaftaran = apps.get_model("customer", "Pendaftaran")
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    used = set(Pendaftaran.objects.exclude(kode_check_in__isnull=True).values_list("kode_check_in", flat=True))
    for row in Pendaftaran.objects.all():
        code = "RUN-" + "".join(secrets.choice(alphabet) for _ in range(6))
        while code in used:
            code = "RUN-" + "".join(secrets.choice(alphabet) for _ in range(6))
        row.kode_check_in = code
        row.save(update_fields=["kode_check_in"])
        used.add(code)


class Migration(migrations.Migration):
    dependencies = [("customer", "0002_initial")]
    operations = [
        migrations.AddField(
            model_name="pendaftaran",
            name="kode_check_in",
            field=models.CharField(blank=True, max_length=12, null=True),
        ),
        migrations.RunPython(populate_codes, migrations.RunPython.noop),
        migrations.RemoveField(model_name="pendaftaran", name="qr_token"),
        migrations.AlterField(
            model_name="pendaftaran",
            name="kode_check_in",
            field=models.CharField(editable=False, max_length=12, unique=True),
        ),
        migrations.AlterField(
            model_name="pendaftaran",
            name="ukuran_kaos",
            field=models.CharField(choices=[("S", "S"), ("M", "M"), ("L", "L"), ("XL", "XL"), ("XXL", "XXL")], max_length=3),
        ),
        migrations.AlterField(
            model_name="pendaftaran",
            name="status_pendaftaran",
            field=models.CharField(choices=[("belum_dikonfirmasi", "Belum Dikonfirmasi"), ("dikonfirmasi", "Dikonfirmasi"), ("check_in", "Sudah Check-in"), ("selesai", "Selesai"), ("dibatalkan", "Dibatalkan")], default="belum_dikonfirmasi", max_length=30),
        ),
        migrations.AddIndex(
            model_name="pendaftaran",
            index=models.Index(fields=["kode_check_in"], name="customer_pe_kode_ch_42ab00_idx"),
        ),
        migrations.AddConstraint(
            model_name="pendaftaran",
            constraint=models.UniqueConstraint(fields=("customer", "event"), name="satu_customer_satu_event"),
        ),
    ]
