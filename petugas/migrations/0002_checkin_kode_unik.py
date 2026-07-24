from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("petugas", "0001_initial")]
    operations = [
        migrations.RenameField(model_name="checkin", old_name="kode_qr_dipindai", new_name="kode_dimasukkan"),
        migrations.AlterField(
            model_name="checkin", name="metode",
            field=models.CharField(choices=[("kode_unik", "Kode Unik")], default="kode_unik", max_length=20),
        ),
    ]
