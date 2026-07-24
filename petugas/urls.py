from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.petugas_dashboard, name="petugas_dashboard"),
    path("pembayaran/", views.daftar_pembayaran, name="daftar_pembayaran"),
    path("pembayaran/<int:pk>/verifikasi/", views.verifikasi_pembayaran, name="verifikasi_pembayaran"),
    path("peserta/", views.daftar_peserta, name="daftar_peserta"),
    path("check-in/", views.check_in_kode, name="check_in_kode"),
    path("riwayat-check-in/", views.riwayat_checkin, name="riwayat_checkin"),
]
