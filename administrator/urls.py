from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.administrator_dashboard, name="administrator_dashboard"),
    path("event/", views.event_list, name="administrator_event_list"),
    path("event/tambah/", views.event_create, name="administrator_event_create"),
    path("event/<int:pk>/edit/", views.event_update, name="administrator_event_update"),
    path("event/<int:pk>/hapus/", views.event_delete, name="administrator_event_delete"),
    path("kategori/", views.kategori_list, name="administrator_kategori_list"),
    path("kategori/tambah/", views.kategori_create, name="administrator_kategori_create"),
    path("kategori/<int:pk>/edit/", views.kategori_update, name="administrator_kategori_update"),
    path("kategori/<int:pk>/hapus/", views.kategori_delete, name="administrator_kategori_delete"),
    path("petugas/", views.petugas_list, name="administrator_petugas_list"),
    path("petugas/tambah/", views.petugas_create, name="administrator_petugas_create"),
    path("petugas/<int:pk>/edit/", views.petugas_update, name="administrator_petugas_update"),
    path("customer/", views.customer_list, name="administrator_customer_list"),
    path("pendaftaran/", views.pendaftaran_list, name="administrator_pendaftaran_list"),
    path("laporan/", views.laporan, name="administrator_laporan"),
    path("laporan/csv/", views.laporan_csv, name="administrator_laporan_csv"),
]
