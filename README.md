# ColorRun Vest — Kelompok 4

Aplikasi web **Manajemen Event dan Penjualan Tiket** berbasis Django untuk memenuhi UAS Web Programming Kelas B. Sistem memiliki tiga hak akses: **Administrator, Petugas, dan Customer**. Check-in peserta menggunakan **kode unik**, bukan pemindaian QR.

## Anggota Kelompok 4

| NIM | Nama |
|---|---|
| 2421400008 | Aprilia Nur Kholisah |
| 2421400152 | Nabila Fajrin |
| 2421400072 | Sifriah Aini |
| 2421400037 | Lyda Ramadhani |
| 2421400035 | Khoiratus Sholehah |

## Fitur Utama

### Customer
- Registrasi akun dan login.
- Melihat daftar serta detail event dan kategori tiket.
- Mengisi formulir pendaftaran peserta.
- Mengunggah bukti pembayaran.
- Melihat status pembayaran dan pendaftaran.
- Membuka serta mencetak e-ticket.
- Mendapat kode unik `RUN-XXXXXX` untuk check-in.

### Petugas
- Dashboard ringkasan peserta.
- Melihat dan memverifikasi pembayaran.
- Menerima atau menolak pembayaran beserta catatan.
- Mencari data peserta.
- Check-in dengan mengetik kode unik peserta.
- Melihat riwayat check-in.

### Administrator
- Dashboard statistik tanpa diagram/grafik.
- CRUD data event.
- CRUD kategori tiket.
- Tambah dan edit akun petugas.
- Melihat customer dan data pendaftaran.
- Laporan peserta dan pembayaran.
- Ekspor laporan CSV dan cetak laporan.
- Django Admin untuk pengelolaan tambahan.

## Teknologi
- Python 3.12+
- Django 6.0.7
- SQLite
- HTML, CSS, dan JavaScript responsif
- Pillow untuk upload gambar

## Cara Instalasi

Buka terminal pada folder project:

```bash
py -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Buka `http://127.0.0.1:8000/` pada browser.

Pengguna Windows juga dapat menjalankan `run_windows.bat`.

## Akun Pengujian

| Hak Akses | Username | Password |
|---|---|---|
| Administrator | `colorrunvest` | `Admin123!` |
| Petugas | `petugas` | `Petugas123!` |
| Customer | `customer` | `Customer123!` |

Customer demo sudah memiliki pembayaran diterima sehingga e-ticket dan kode check-in dapat langsung diuji. Login sebagai customer untuk melihat kodenya, kemudian login sebagai petugas dan masukkan kode tersebut pada menu **Check-in Kode Unik**.

## Alur Utama

1. Customer membuat akun dan login.
2. Customer melihat event dan kategori tiket.
3. Customer mengisi formulir pendaftaran.
4. Sistem membuat kode pendaftaran, pembayaran, dan kode check-in unik.
5. Customer mengunggah bukti pembayaran.
6. Petugas memverifikasi pembayaran.
7. Setelah diterima, status menjadi dikonfirmasi dan e-ticket aktif.
8. Pada hari event, petugas mengetik kode unik peserta.
9. Sistem memastikan kode valid, pembayaran diterima, dan peserta belum check-in.
10. Administrator melihat rekapitulasi dan laporan.

## Pengujian

```bash
python manage.py test
python manage.py check
```

## Struktur Django Apps
- `administrator`: event, kategori tiket, pengaturan, log, dashboard dan laporan.
- `customer`: akun customer, pendaftaran, pembayaran, e-ticket.
- `petugas`: akun petugas, verifikasi, dan check-in kode unik.

> Jangan mengunggah folder `env` atau `venv` ke GitHub. File `.gitignore` sudah disediakan.
