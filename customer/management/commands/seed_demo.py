from datetime import date, time, timedelta
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from administrator.models import Administrator, Event, KategoriTiket, PengaturanSistem
from customer.models import Customer, Pendaftaran, Pembayaran
from petugas.models import Petugas


class Command(BaseCommand):
    help = "Membuat data contoh dan akun pengujian ColorRun Vest secara idempotent."

    @transaction.atomic
    def handle(self, *args, **options):
        admin_user, _ = User.objects.get_or_create(
            username="colorrunvest",
            defaults={"email": "admin@colorrunvest.id", "first_name": "Administrator ColorRun", "is_staff": True, "is_superuser": True},
        )
        admin_user.email = "admin@colorrunvest.id"
        admin_user.first_name = "Administrator ColorRun"
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_active = True
        admin_user.set_password("Admin123!")
        admin_user.save()
        Administrator.objects.update_or_create(
            user=admin_user,
            defaults={"nama_lengkap": "Administrator ColorRun", "nomor_hp": "081200002026", "aktif": True},
        )

        staff_user, _ = User.objects.get_or_create(username="petugas", defaults={"email": "petugas@colorrunvest.id"})
        staff_user.email = "petugas@colorrunvest.id"
        staff_user.first_name = "Petugas ColorRun"
        staff_user.is_active = True
        staff_user.set_password("Petugas123!")
        staff_user.save()
        petugas, _ = Petugas.objects.update_or_create(
            user=staff_user,
            defaults={"kode_petugas": "PTG-001", "nama_lengkap": "Petugas ColorRun", "nomor_hp": "081211112026", "jenis_kelamin": "P", "aktif": True},
        )

        settings_obj, _ = PengaturanSistem.objects.get_or_create(pk=1)
        settings_obj.nama_aplikasi = "ColorRun Vest"
        settings_obj.nama_penyelenggara = "ColorRun Vest Organizer"
        settings_obj.nama_bank = "Bank BCA"
        settings_obj.nomor_rekening = "1234567890"
        settings_obj.atas_nama_rekening = "ColorRun Vest Organizer"
        settings_obj.email_admin = "admin@colorrunvest.id"
        settings_obj.nomor_whatsapp = "0812-0000-2026"
        settings_obj.alamat = "Jakarta, Indonesia"
        settings_obj.diperbarui_oleh = admin_user
        settings_obj.save()

        events_data = [
            {
                "nama_event": "ColorRun Vest 2026",
                "slug": "colorrun-vest-2026",
                "deskripsi": "Bergabunglah dalam pengalaman lari penuh warna, kebersamaan, dan energi positif. ColorRun Vest 2026 menghadirkan rute ramah pemula, hiburan, color zone, serta berbagai fasilitas untuk peserta.",
                "tanggal_mulai": date(2026, 8, 16), "jam_mulai": time(6, 0), "jam_selesai": time(11, 0),
                "lokasi": "Lapangan Banteng, Jakarta", "dress_code": "Kaos putih atau race jersey ColorRun",
                "rute_color_run": "Start Lapangan Banteng - Color Zone 1 - Water Station - Color Zone 2 - Finish Festival Area.",
                "fasilitas": "Race jersey\nNomor dada\nMedali finisher\nColor powder\nWater station\nFoto dokumentasi",
                "hadiah_doorprize": "Sepeda, smartwatch, dan voucher olahraga.",
                "contact_person": "Admin ColorRun", "nomor_contact_person": "0812-0000-2026", "status": "dipublikasikan",
                "categories": [("SK Fun Run", 175000, 1500, "Kategori lari 5 km untuk umum."), ("Family Run", 350000, 800, "Paket keluarga untuk dua peserta."), ("Kids Dash", 100000, 1000, "Lintasan khusus peserta anak."), ("VIP Package", 500000, 300, "Akses prioritas dan merchandise eksklusif.")],
            },
            {
                "nama_event": "Sunset Color Dash",
                "slug": "sunset-color-dash",
                "deskripsi": "Color run sore hari dengan suasana matahari terbenam, musik, dan festival warna setelah garis finis.",
                "tanggal_mulai": date(2026, 9, 6), "jam_mulai": time(15, 30), "jam_selesai": time(20, 0),
                "lokasi": "Ancol Beach City, Jakarta", "dress_code": "Kaos putih dan sepatu olahraga",
                "rute_color_run": "Rute 3 km area pantai Ancol.",
                "fasilitas": "Race pack\nMedali finisher\nColor powder\nAir mineral\nFestival musik",
                "hadiah_doorprize": "Voucher dan merchandise.",
                "contact_person": "Admin Event", "nomor_contact_person": "0812-0000-2026", "status": "dipublikasikan",
                "categories": [("Regular", 150000, 600, "Tiket peserta umum."), ("Bestie Pack", 280000, 300, "Paket dua peserta.")],
            },
        ]
        now = timezone.now()
        event_objects = []
        for data in events_data:
            categories = data.pop("categories")
            event, _ = Event.objects.update_or_create(slug=data["slug"], defaults={**data, "dibuat_oleh": admin_user})
            event_objects.append(event)
            for name, price, quota, desc in categories:
                KategoriTiket.objects.update_or_create(
                    event=event, nama_kategori=name,
                    defaults={"harga": price, "kuota": quota, "deskripsi": desc, "aktif": True,
                              "tanggal_penjualan_mulai": now - timedelta(days=7), "tanggal_penjualan_selesai": now + timedelta(days=120)},
                )

        demo_users = [
            ("customer", "customer@demo.id", "Customer Demo", "081233330001", "diterima"),
            ("peserta2", "peserta2@demo.id", "Nabila Fajrin", "081233330002", "menunggu_verifikasi"),
            ("peserta3", "peserta3@demo.id", "Sifriah Aini", "081233330003", "menunggu_pembayaran"),
        ]
        main_event = event_objects[0]
        categories = list(main_event.kategori_tiket.order_by("harga"))
        for idx, (username, email, name, phone, payment_status) in enumerate(demo_users):
            user, _ = User.objects.get_or_create(username=username, defaults={"email": email})
            user.email = email
            user.first_name = name
            user.is_active = True
            user.set_password("Customer123!")
            user.save()
            customer, _ = Customer.objects.update_or_create(
                user=user,
                defaults={"nama_lengkap": name, "nomor_hp": phone, "tanggal_lahir": date(2001, 1, 10 + idx), "jenis_kelamin": "P", "alamat": "Jakarta", "aktif": True},
            )
            registration = Pendaftaran.objects.filter(customer=customer, event=main_event).first()
            if not registration:
                category = categories[min(idx, len(categories)-1)]
                registration = Pendaftaran.objects.create(
                    customer=customer, event=main_event, kategori_tiket=category,
                    nama_lengkap=name, email=email, nomor_hp=phone, tanggal_lahir=date(2001, 1, 10 + idx),
                    jenis_kelamin="P", ukuran_kaos="M", nama_kontak_darurat="Keluarga " + name,
                    nomor_kontak_darurat="08129999000" + str(idx), riwayat_penyakit="", harga_tiket=category.harga,
                    status_pendaftaran="dikonfirmasi" if payment_status == "diterima" else "belum_dikonfirmasi",
                )
            payment, _ = Pembayaran.objects.get_or_create(
                pendaftaran=registration,
                defaults={"jumlah_pembayaran": registration.harga_tiket},
            )
            payment.metode_pembayaran = "transfer_bank"
            payment.jumlah_pembayaran = registration.harga_tiket
            payment.nama_pengirim = name
            payment.bank_pengirim = "BCA"
            payment.status_pembayaran = payment_status
            if payment_status == "diterima":
                payment.diverifikasi_oleh = petugas
                payment.tanggal_verifikasi = now
                registration.status_pendaftaran = "dikonfirmasi"
                registration.save()
            elif payment_status == "menunggu_verifikasi":
                if not payment.bukti_pembayaran:
                    payment.bukti_pembayaran.save("bukti-demo.png", ContentFile(self.make_proof_image(name)), save=False)
                payment.tanggal_upload = now
            payment.save()

        self.stdout.write(self.style.SUCCESS("Data demo ColorRun Vest berhasil disiapkan."))
        self.stdout.write("Akun admin    : colorrunvest / Admin123!")
        self.stdout.write("Akun petugas  : petugas / Petugas123!")
        self.stdout.write("Akun customer : customer / Customer123!")

    @staticmethod
    def make_proof_image(name):
        from PIL import Image, ImageDraw
        image = Image.new("RGB", (900, 520), "white")
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((35, 35, 865, 485), radius=25, outline="#e0c9aa", width=4, fill="#fff9ed")
        draw.text((75, 75), "BUKTI TRANSFER DEMO", fill="#f05218")
        draw.text((75, 145), f"Pengirim: {name}", fill="#222222")
        draw.text((75, 205), "Tujuan: ColorRun Vest Organizer", fill="#222222")
        draw.text((75, 265), "Status: BERHASIL", fill="#1c9a62")
        draw.text((75, 385), "File ini hanya data contoh untuk demonstrasi UAS.", fill="#777777")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
