from django.contrib import admin

from .models import (
    Administrator,
    Event,
    KategoriTiket,
    LogAktivitas,
    PengaturanSistem,
)


@admin.register(Administrator)
class AdministratorAdmin(admin.ModelAdmin):
    list_display = (
        "nama_lengkap",
        "user",
        "nomor_hp",
        "aktif",
    )
    search_fields = (
        "nama_lengkap",
        "user__username",
        "user__email",
    )
    list_filter = ("aktif",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "nama_event",
        "tanggal_mulai",
        "lokasi",
        "status",
        "total_kuota",
        "total_tiket_terjual",
    )
    list_filter = ("status", "tanggal_mulai")
    search_fields = ("nama_event", "lokasi")
    prepopulated_fields = {"slug": ("nama_event",)}
    readonly_fields = ("dibuat_pada", "diperbarui_pada")


@admin.register(KategoriTiket)
class KategoriTiketAdmin(admin.ModelAdmin):
    list_display = (
        "nama_kategori",
        "event",
        "harga",
        "kuota",
        "jumlah_tiket_terjual",
        "sisa_kuota",
        "aktif",
    )
    list_filter = ("aktif", "event")
    search_fields = ("nama_kategori", "event__nama_event")


@admin.register(PengaturanSistem)
class PengaturanSistemAdmin(admin.ModelAdmin):
    list_display = (
        "nama_aplikasi",
        "email_admin",
        "nomor_whatsapp",
        "diperbarui_pada",
    )


@admin.register(LogAktivitas)
class LogAktivitasAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "jenis_aktivitas",
        "deskripsi",
        "alamat_ip",
        "dibuat_pada",
    )
    list_filter = ("jenis_aktivitas", "dibuat_pada")
    search_fields = (
        "user__username",
        "deskripsi",
        "nama_tabel",
    )
    readonly_fields = (
        "user",
        "jenis_aktivitas",
        "deskripsi",
        "nama_tabel",
        "id_objek",
        "alamat_ip",
        "user_agent",
        "dibuat_pada",
    )