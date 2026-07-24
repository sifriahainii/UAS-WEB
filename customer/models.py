import secrets
import string
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.utils import timezone


def generate_checkin_code():
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "RUN-" + "".join(secrets.choice(alphabet) for _ in range(6))


class Customer(models.Model):
    class JenisKelamin(models.TextChoices):
        LAKI_LAKI = "L", "Laki-laki"
        PEREMPUAN = "P", "Perempuan"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer_profile"
    )
    nama_lengkap = models.CharField(max_length=150)
    nomor_hp = models.CharField(max_length=20)
    tanggal_lahir = models.DateField(blank=True, null=True)
    jenis_kelamin = models.CharField(max_length=1, choices=JenisKelamin.choices, blank=True)
    alamat = models.TextField(blank=True)
    foto = models.ImageField(upload_to="profil/customer/", blank=True, null=True)
    aktif = models.BooleanField(default=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customer"
        ordering = ["nama_lengkap"]

    def __str__(self):
        return self.nama_lengkap


class Pendaftaran(models.Model):
    class UkuranKaos(models.TextChoices):
        S = "S", "S"
        M = "M", "M"
        L = "L", "L"
        XL = "XL", "XL"
        XXL = "XXL", "XXL"

    class JenisKelamin(models.TextChoices):
        LAKI_LAKI = "L", "Laki-laki"
        PEREMPUAN = "P", "Perempuan"

    class StatusPendaftaran(models.TextChoices):
        BELUM_DIKONFIRMASI = "belum_dikonfirmasi", "Belum Dikonfirmasi"
        DIKONFIRMASI = "dikonfirmasi", "Dikonfirmasi"
        CHECK_IN = "check_in", "Sudah Check-in"
        SELESAI = "selesai", "Selesai"
        DIBATALKAN = "dibatalkan", "Dibatalkan"

    kode_pendaftaran = models.CharField(max_length=30, unique=True, editable=False)
    kode_check_in = models.CharField(max_length=12, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="pendaftaran")
    event = models.ForeignKey("administrator.Event", on_delete=models.PROTECT, related_name="pendaftaran")
    kategori_tiket = models.ForeignKey(
        "administrator.KategoriTiket", on_delete=models.PROTECT, related_name="pendaftaran"
    )
    nama_lengkap = models.CharField(max_length=150)
    email = models.EmailField()
    nomor_hp = models.CharField(max_length=20)
    tanggal_lahir = models.DateField()
    jenis_kelamin = models.CharField(max_length=1, choices=JenisKelamin.choices)
    ukuran_kaos = models.CharField(max_length=3, choices=UkuranKaos.choices)
    nama_kontak_darurat = models.CharField(max_length=150)
    nomor_kontak_darurat = models.CharField(max_length=20)
    riwayat_penyakit = models.TextField(blank=True, help_text="Opsional. Kosongkan jika tidak ada.")
    harga_tiket = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    status_pendaftaran = models.CharField(
        max_length=30, choices=StatusPendaftaran.choices, default=StatusPendaftaran.BELUM_DIKONFIRMASI
    )
    waktu_pendaftaran = models.DateTimeField(auto_now_add=True)
    diperbarui_pada = models.DateTimeField(auto_now=True)
    catatan = models.TextField(blank=True)

    class Meta:
        verbose_name = "Pendaftaran"
        verbose_name_plural = "Pendaftaran"
        ordering = ["-waktu_pendaftaran"]
        indexes = [
            models.Index(fields=["kode_pendaftaran"]),
            models.Index(fields=["kode_check_in"]),
            models.Index(fields=["status_pendaftaran"]),
            models.Index(fields=["event"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["customer", "event"], name="satu_customer_satu_event")
        ]

    def __str__(self):
        return f"{self.kode_pendaftaran} - {self.nama_lengkap}"

    def clean(self):
        super().clean()
        if self.kategori_tiket_id and self.event_id and self.kategori_tiket.event_id != self.event_id:
            raise ValidationError({"kategori_tiket": "Kategori tiket tidak berasal dari event yang dipilih."})
        if self.kategori_tiket_id and not self.pk and self.kategori_tiket.sisa_kuota <= 0:
            raise ValidationError({"kategori_tiket": "Kuota tiket sudah habis."})
        if self.kategori_tiket_id and not self.kategori_tiket.aktif:
            raise ValidationError({"kategori_tiket": "Kategori tiket sedang tidak aktif."})
        if self.customer_id and self.event_id:
            qs = Pendaftaran.objects.filter(customer_id=self.customer_id, event_id=self.event_id)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("Akun ini sudah terdaftar pada event yang sama.")

    def save(self, *args, **kwargs):
        if not self.kode_pendaftaran:
            tanggal = timezone.localdate().strftime("%Y%m%d")
            self.kode_pendaftaran = f"CRV-{tanggal}-{uuid.uuid4().hex[:8].upper()}"
        if not self.kode_check_in:
            code = generate_checkin_code()
            while Pendaftaran.objects.filter(kode_check_in=code).exists():
                code = generate_checkin_code()
            self.kode_check_in = code
        if self.kategori_tiket_id and not self.harga_tiket:
            self.harga_tiket = self.kategori_tiket.harga
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def sudah_check_in(self):
        return hasattr(self, "check_in")

    @property
    def tiket_dapat_dicetak(self):
        return (
            hasattr(self, "pembayaran")
            and self.pembayaran.status_pembayaran == Pembayaran.StatusPembayaran.DITERIMA
            and self.status_pendaftaran != self.StatusPendaftaran.DIBATALKAN
        )


class Pembayaran(models.Model):
    class MetodePembayaran(models.TextChoices):
        TRANSFER_BANK = "transfer_bank", "Transfer Bank"
        QRIS = "qris", "QRIS"
        TUNAI = "tunai", "Tunai"

    class StatusPembayaran(models.TextChoices):
        MENUNGGU_PEMBAYARAN = "menunggu_pembayaran", "Menunggu Pembayaran"
        MENUNGGU_VERIFIKASI = "menunggu_verifikasi", "Menunggu Verifikasi"
        DITOLAK = "ditolak", "Pembayaran Ditolak"
        DITERIMA = "diterima", "Pembayaran Diterima"

    pendaftaran = models.OneToOneField(Pendaftaran, on_delete=models.CASCADE, related_name="pembayaran")
    kode_pembayaran = models.CharField(max_length=30, unique=True, editable=False)
    metode_pembayaran = models.CharField(
        max_length=30, choices=MetodePembayaran.choices, default=MetodePembayaran.TRANSFER_BANK
    )
    jumlah_pembayaran = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    bukti_pembayaran = models.ImageField(
        upload_to="pembayaran/%Y/%m/", blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"])],
    )
    nama_pengirim = models.CharField(max_length=150, blank=True)
    bank_pengirim = models.CharField(max_length=100, blank=True)
    status_pembayaran = models.CharField(
        max_length=30, choices=StatusPembayaran.choices,
        default=StatusPembayaran.MENUNGGU_PEMBAYARAN,
    )
    tanggal_upload = models.DateTimeField(blank=True, null=True)
    diverifikasi_oleh = models.ForeignKey(
        "petugas.Petugas", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="pembayaran_diverifikasi",
    )
    tanggal_verifikasi = models.DateTimeField(blank=True, null=True)
    alasan_penolakan = models.TextField(blank=True)
    catatan_petugas = models.TextField(blank=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pembayaran"
        verbose_name_plural = "Pembayaran"
        ordering = ["-dibuat_pada"]
        indexes = [models.Index(fields=["status_pembayaran"]), models.Index(fields=["kode_pembayaran"])]

    def __str__(self):
        return f"{self.kode_pembayaran} - {self.pendaftaran.nama_lengkap}"

    def clean(self):
        super().clean()
        if self.status_pembayaran == self.StatusPembayaran.MENUNGGU_VERIFIKASI and not self.bukti_pembayaran:
            raise ValidationError({"bukti_pembayaran": "Bukti pembayaran wajib diunggah."})
        if self.status_pembayaran == self.StatusPembayaran.DITOLAK and not self.alasan_penolakan:
            raise ValidationError({"alasan_penolakan": "Alasan penolakan harus diisi."})

    def save(self, *args, **kwargs):
        if not self.kode_pembayaran:
            tanggal = timezone.localdate().strftime("%Y%m%d")
            self.kode_pembayaran = f"PAY-{tanggal}-{uuid.uuid4().hex[:8].upper()}"
        if not self.jumlah_pembayaran:
            self.jumlah_pembayaran = self.pendaftaran.harga_tiket
        if (
            self.bukti_pembayaran and not self.tanggal_upload
            and self.status_pembayaran in [self.StatusPembayaran.MENUNGGU_PEMBAYARAN, self.StatusPembayaran.DITOLAK]
        ):
            self.status_pembayaran = self.StatusPembayaran.MENUNGGU_VERIFIKASI
            self.tanggal_upload = timezone.now()
            self.alasan_penolakan = ""
        self.full_clean()
        super().save(*args, **kwargs)
