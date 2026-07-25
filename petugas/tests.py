from datetime import date, time
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from administrator.models import Event, KategoriTiket
from customer.models import Customer, Pendaftaran, Pembayaran
from .models import CheckIn, Petugas


class StaffFlowTests(TestCase):
    def setUp(self):
        staff_user = User.objects.create_user("petugas", password="Petugas123!")
        self.staff = Petugas.objects.create(user=staff_user, kode_petugas="PTG-001", nama_lengkap="Petugas", nomor_hp="0812")
        customer_user = User.objects.create_user("customer2", email="c2@test.id", password="Customer123!")
        customer = Customer.objects.create(user=customer_user, nama_lengkap="Peserta", nomor_hp="0813")
        event = Event.objects.create(
            nama_event="Event", slug="event", deskripsi="Test", tanggal_mulai=date(2026, 8, 10), jam_mulai=time(6),
            lokasi="Lokasi", contact_person="Admin", nomor_contact_person="0812", status="dipublikasikan",
        )
        category = KategoriTiket.objects.create(event=event, nama_kategori="Regular", harga=100000, kuota=10)
        self.registration = Pendaftaran.objects.create(
        customer=customer,
        event=event,
        kategori_tiket=category,
        nama_lengkap="Peserta",
        email="c2@test.id",
        nomor_hp="0813",
        tanggal_lahir=date(2000, 1, 1),
        jenis_kelamin="L",
        ukuran_kaos="L",
        harga_tiket=100000,
        status_pendaftaran="dikonfirmasi",
)
     
        Pembayaran.objects.create(
            pendaftaran=self.registration, jumlah_pembayaran=100000, status_pembayaran="diterima"
        )

    def test_code_checkin(self):
        self.client.login(username="petugas", password="Petugas123!")
        response = self.client.post(reverse("check_in_kode"), {"kode_check_in": self.registration.kode_check_in})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(CheckIn.objects.filter(pendaftaran=self.registration).exists())
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.status_pendaftaran, "check_in")
