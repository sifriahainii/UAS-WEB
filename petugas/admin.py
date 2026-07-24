from django.contrib import admin
from .models import CheckIn, Petugas

@admin.register(Petugas)
class PetugasAdmin(admin.ModelAdmin):
    list_display = ("kode_petugas", "nama_lengkap", "user", "nomor_hp", "aktif")
    list_filter = ("aktif", "jenis_kelamin")
    search_fields = ("kode_petugas", "nama_lengkap", "user__username", "user__email")

@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ("pendaftaran", "petugas", "metode", "waktu_check_in")
    list_filter = ("metode", "waktu_check_in")
    search_fields = ("pendaftaran__kode_pendaftaran", "pendaftaran__kode_check_in", "pendaftaran__nama_lengkap", "petugas__nama_lengkap")
