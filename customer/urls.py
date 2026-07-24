from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("event/", views.event_list, name="event_list"),
    path("event/<slug:slug>/", views.event_detail, name="detail_event"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.customer_dashboard, name="customer_dashboard"),
    path("event/<slug:slug>/daftar/<int:kategori_id>/", views.daftar_tiket, name="daftar_tiket"),
    path("pendaftaran/<int:pk>/", views.detail_pendaftaran, name="detail_pendaftaran"),
    path("pendaftaran/<int:pk>/pembayaran/", views.upload_pembayaran, name="upload_pembayaran"),
    path("pendaftaran/<int:pk>/tiket/", views.tiket, name="tiket"),
    path("profil/", views.profile, name="profile"),
]
