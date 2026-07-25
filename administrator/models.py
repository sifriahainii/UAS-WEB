from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Administrator(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="administrator_profile",
    )
    nama_lengkap = models.CharField(max_length=150)
    nomor_hp = models.CharField(max_length=20, blank=True)
    foto = models.ImageField(upload_to="profil/administrator/", blank=True, null=True)
    aktif = models.BooleanField(default=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Administrator"
        verbose_name_plural = "Administrator"
        ordering = ["nama_lengkap"]

    def __str__(self):
        return self.nama_lengkap


class Event(models.Model):
    class StatusEvent(models.TextChoices):
        DRAFT = "draft", "Draft"
        DIPUBLIKASIKAN = "dipublikasikan", "Dipublikasikan"
        BERLANGSUNG = "berlangsung", "Berlangsung"
        SELESAI = "selesai", "Selesai"
        DIBATALKAN = "dibatalkan", "Dibatalkan"

    nama_event = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    poster_event = models.ImageField(
        upload_to="event/poster/", blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"])],
    )
    banner_event = models.ImageField(
        upload_to="event/banner/", blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"])],
    )
    deskripsi = models.TextField()
    tanggal_mulai = models.DateField()
    jam_mulai = models.TimeField()
    jam_selesai = models.TimeField(blank=True, null=True)
    lokasi = models.CharField(max_length=255)
    dress_code = models.CharField(max_length=200, blank=True)
    rute_color_run = models.TextField(blank=True)
    fasilitas = models.TextField(blank=True, help_text="Tuliskan satu fasilitas pada setiap baris.")
    contact_person = models.CharField(max_length=100)
    nomor_contact_person = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=StatusEvent.choices, default=StatusEvent.DRAFT)
    dibuat_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="event_dibuat",
    )
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Event"
        ordering = ["-tanggal_mulai", "-jam_mulai"]

    def __str__(self):
        return self.nama_event

    def clean(self):
        super().clean()
        if self.tanggal_selesai and self.tanggal_selesai < self.tanggal_mulai:
            raise ValidationError({"tanggal_selesai": "Tanggal selesai tidak boleh sebelum tanggal mulai."})

    def get_absolute_url(self):
        return reverse("detail_event", kwargs={"slug": self.slug})

    @property
    def total_kuota(self):
        return sum(kategori.kuota for kategori in self.kategori_tiket.all())

    @property
    def total_tiket_terjual(self):
        return sum(kategori.jumlah_tiket_terjual for kategori in self.kategori_tiket.all())

    @property
    def total_tiket_tersedia(self):
        return max(self.total_kuota - self.total_tiket_terjual, 0)

    @property
    def persentase_kuota_terisi(self):
        return round((self.total_tiket_terjual / self.total_kuota) * 100, 2) if self.total_kuota else 0


class KategoriTiket(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="kategori_tiket")
    nama_kategori = models.CharField(max_length=100)
    deskripsi = models.TextField(blank=True)
    harga = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    kuota = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    tanggal_penjualan_mulai = models.DateTimeField(default=timezone.now)
    tanggal_penjualan_selesai = models.DateTimeField(blank=True, null=True)
    aktif = models.BooleanField(default=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kategori Tiket"
        verbose_name_plural = "Kategori Tiket"
        ordering = ["event", "harga"]
        constraints = [
            models.UniqueConstraint(fields=["event", "nama_kategori"], name="kategori_tiket_unik_per_event")
        ]

    def __str__(self):
        return f"{self.event.nama_event} - {self.nama_kategori}"

    def clean(self):
        super().clean()
        if self.tanggal_penjualan_selesai and self.tanggal_penjualan_selesai < self.tanggal_penjualan_mulai:
            raise ValidationError({"tanggal_penjualan_selesai": "Waktu penjualan selesai tidak valid."})

    @property
    def jumlah_tiket_terjual(self):
        return self.pendaftaran.filter(
            status_pendaftaran__in=["dikonfirmasi", "check_in", "selesai"],
            pembayaran__status_pembayaran="diterima",
        ).count()

    @property
    def sisa_kuota(self):
        return max(self.kuota - self.jumlah_tiket_terjual, 0)

    @property
    def masih_tersedia(self):
        now = timezone.now()
        within_period = self.tanggal_penjualan_mulai <= now and (
            not self.tanggal_penjualan_selesai or now <= self.tanggal_penjualan_selesai
        )
        return self.aktif and within_period and self.sisa_kuota > 0


class PengaturanSistem(models.Model):
    nama_aplikasi = models.CharField(max_length=150, default="ColorRun Vest")
    nama_penyelenggara = models.CharField(max_length=150, blank=True)
    logo_event = models.ImageField(upload_to="pengaturan/logo/", blank=True, null=True)
    banner = models.ImageField(upload_to="pengaturan/banner/", blank=True, null=True)
    nama_bank = models.CharField(max_length=100, blank=True)
    nomor_rekening = models.CharField(max_length=50, blank=True)
    atas_nama_rekening = models.CharField(max_length=150, blank=True)
    qris = models.ImageField(upload_to="pengaturan/qris/", blank=True, null=True)
    email_admin = models.EmailField(blank=True)
    nomor_whatsapp = models.CharField(max_length=20, blank=True)
    instagram = models.URLField(blank=True)
    tiktok = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    alamat = models.TextField(blank=True)
    diperbarui_oleh = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="pengaturan_diperbarui",
    )
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pengaturan Sistem"
        verbose_name_plural = "Pengaturan Sistem"

    def __str__(self):
        return self.nama_aplikasi


class LogAktivitas(models.Model):
    class JenisAktivitas(models.TextChoices):
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        TAMBAH = "tambah", "Tambah Data"
        UBAH = "ubah", "Ubah Data"
        HAPUS = "hapus", "Hapus Data"
        VERIFIKASI = "verifikasi", "Verifikasi"
        CHECK_IN = "check_in", "Check-in"
        RESET_PASSWORD = "reset_password", "Reset Password"
        BACKUP = "backup", "Backup Database"
        RESTORE = "restore", "Restore Database"
        LAINNYA = "lainnya", "Lainnya"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="log_aktivitas",
    )
    jenis_aktivitas = models.CharField(max_length=30, choices=JenisAktivitas.choices, default=JenisAktivitas.LAINNYA)
    deskripsi = models.TextField()
    nama_tabel = models.CharField(max_length=100, blank=True)
    id_objek = models.CharField(max_length=100, blank=True)
    alamat_ip = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log Aktivitas"
        verbose_name_plural = "Log Aktivitas"
        ordering = ["-dibuat_pada"]

    def __str__(self):
        username = self.user.username if self.user else "Sistem"
        return f"{username} - {self.get_jenis_aktivitas_display()}"
