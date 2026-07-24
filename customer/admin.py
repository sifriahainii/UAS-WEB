from django.contrib import admin
from .models import Customer, Pembayaran, Pendaftaran

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("nama_lengkap", "user", "nomor_hp", "aktif", "dibuat_pada")
    list_filter = ("aktif", "jenis_kelamin")
    search_fields = ("nama_lengkap", "nomor_hp", "user__username", "user__email")

@admin.register(Pendaftaran)
class PendaftaranAdmin(admin.ModelAdmin):
    list_display = ("kode_pendaftaran", "kode_check_in", "nama_lengkap", "event", "kategori_tiket", "status_pendaftaran", "waktu_pendaftaran")
    list_filter = ("status_pendaftaran", "event", "kategori_tiket", "jenis_kelamin", "ukuran_kaos")
    search_fields = ("kode_pendaftaran", "kode_check_in", "nama_lengkap", "email", "nomor_hp")
    readonly_fields = ("kode_pendaftaran", "kode_check_in", "waktu_pendaftaran", "diperbarui_pada")

@admin.register(Pembayaran)
class PembayaranAdmin(admin.ModelAdmin):
    list_display = ("kode_pembayaran", "pendaftaran", "jumlah_pembayaran", "metode_pembayaran", "status_pembayaran", "diverifikasi_oleh", "tanggal_verifikasi")
    list_filter = ("status_pembayaran", "metode_pembayaran", "tanggal_verifikasi")
    search_fields = ("kode_pembayaran", "pendaftaran__kode_pendaftaran", "pendaftaran__nama_lengkap")
    readonly_fields = ("kode_pembayaran", "dibuat_pada", "diperbarui_pada")
