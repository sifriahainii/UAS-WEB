from datetime import date, time
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from administrator.models import Event, KategoriTiket
from .models import Customer, Pendaftaran, Pembayaran


class CustomerFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("customer", "customer@test.id", "Customer123!")
        self.customer = Customer.objects.create(user=self.user, nama_lengkap="Customer Demo", nomor_hp="08123456789")
        self.event = Event.objects.create(
            nama_event="ColorRun Test", slug="colorrun-test", deskripsi="Event test", tanggal_mulai=date(2026, 8, 10),
            jam_mulai=time(6, 0), lokasi="Jakarta", contact_person="Admin", nomor_contact_person="0812",
            status=Event.StatusEvent.DIPUBLIKASIKAN,
        )
        self.category = KategoriTiket.objects.create(event=self.event, nama_kategori="Fun Run", harga=175000, kuota=100)

    def test_home_and_login(self):
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)
        self.assertTrue(self.client.login(username="customer", password="Customer123!"))
        self.assertEqual(self.client.get(reverse("customer_dashboard")).status_code, 200)

    def test_registration_creates_payment_and_code(self):
        self.client.login(username="customer", password="Customer123!")
        response = self.client.post(reverse("daftar_tiket", args=[self.event.slug, self.category.pk]), {
            "nama_lengkap": "Customer Demo", "email": "customer@test.id", "nomor_hp": "08123456789",
            "tanggal_lahir": "2000-01-01", "jenis_kelamin": "P", "ukuran_kaos": "M",
            "nama_kontak_darurat": "Keluarga", "nomor_kontak_darurat": "08120000000",
            "riwayat_penyakit": "", "catatan": "",
        })
        self.assertEqual(response.status_code, 302)
        registration = Pendaftaran.objects.get(customer=self.customer)
        self.assertTrue(registration.kode_check_in.startswith("RUN-"))
        self.assertTrue(Pembayaran.objects.filter(pendaftaran=registration).exists())
