from django.conf import settings
from django.db import models


class Petugas(models.Model):
    class JenisKelamin(models.TextChoices):
        LAKI_LAKI = "L", "Laki-laki"
        PEREMPUAN = "P", "Perempuan"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="petugas_profile"
    )
    kode_petugas = models.CharField(max_length=20, unique=True)
    nama_lengkap = models.CharField(max_length=150)
    nomor_hp = models.CharField(max_length=20)
    jenis_kelamin = models.CharField(max_length=1, choices=JenisKelamin.choices, blank=True)
    alamat = models.TextField(blank=True)
    foto = models.ImageField(upload_to="profil/petugas/", blank=True, null=True)
    aktif = models.BooleanField(default=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Petugas"
        verbose_name_plural = "Petugas"
        ordering = ["nama_lengkap"]

    def __str__(self):
        return f"{self.kode_petugas} - {self.nama_lengkap}"


class CheckIn(models.Model):
    pendaftaran = models.OneToOneField(
        "customer.Pendaftaran", on_delete=models.CASCADE, related_name="check_in"
    )
    petugas = models.ForeignKey(Petugas, on_delete=models.PROTECT, related_name="riwayat_check_in")
    waktu_check_in = models.DateTimeField(auto_now_add=True)
    metode = models.CharField(
        max_length=20, choices=[("kode_unik", "Kode Unik")], default="kode_unik"
    )
    kode_dimasukkan = models.CharField(max_length=100, blank=True)
    catatan = models.TextField(blank=True)

    class Meta:
        verbose_name = "Check-in"
        verbose_name_plural = "Check-in"
        ordering = ["-waktu_check_in"]

    def __str__(self):
        return f"Check-in {self.pendaftaran.kode_pendaftaran} oleh {self.petugas.nama_lengkap}"
