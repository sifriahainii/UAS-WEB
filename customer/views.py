from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from administrator.models import Event, KategoriTiket, LogAktivitas, PengaturanSistem
from colorrun.utils import get_user_role, role_required, write_log
from .forms import CustomerProfileForm, CustomerRegisterForm, PendaftaranForm, PembayaranForm
from .models import Pendaftaran, Pembayaran


def home(request):
    events = Event.objects.filter(status__in=[Event.StatusEvent.DIPUBLIKASIKAN, Event.StatusEvent.BERLANGSUNG]).prefetch_related("kategori_tiket")[:6]
    return render(request, "home.html", {"events": events})


def event_list(request):
    query = request.GET.get("q", "").strip()
    events = Event.objects.filter(status__in=[Event.StatusEvent.DIPUBLIKASIKAN, Event.StatusEvent.BERLANGSUNG]).prefetch_related("kategori_tiket")
    if query:
        events = events.filter(Q(nama_event__icontains=query) | Q(lokasi__icontains=query))
    return render(request, "customer/event_list.html", {"events": events, "query": query})


def event_detail(request, slug):
    event = get_object_or_404(Event.objects.prefetch_related("kategori_tiket"), slug=slug)
    if event.status == Event.StatusEvent.DRAFT and get_user_role(request.user) != "administrator":
        messages.error(request, "Event belum dipublikasikan.")
        return redirect("event_list")
    return render(request, "customer/event_detail.html", {"event": event})


def register_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)
    form = CustomerRegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save()
        login(request, user)
        messages.success(request, "Akun berhasil dibuat. Selamat datang di ColorRun Vest!")
        return redirect("customer_dashboard")
    return render(request, "register.html", {"form": form})


def redirect_by_role(user):
    role = get_user_role(user)
    if role == "administrator":
        return redirect("administrator_dashboard")
    if role == "petugas":
        return redirect("petugas_dashboard")
    if role == "customer":
        return redirect("customer_dashboard")
    return redirect("home")


def login_view(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)
    next_url = request.GET.get("next") or request.POST.get("next")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_active:
            login(request, user)
            write_log(request, LogAktivitas.JenisAktivitas.LOGIN, f"Login sebagai {get_user_role(user)}")
            messages.success(request, f"Selamat datang, {user.first_name or user.username}.")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect_by_role(user)
        messages.error(request, "Username atau password salah.")
    return render(request, "login.html", {"next": next_url})


def logout_view(request):
    if request.user.is_authenticated:
        write_log(request, LogAktivitas.JenisAktivitas.LOGOUT, "Logout dari aplikasi")
    logout(request)
    messages.success(request, "Anda telah keluar dari aplikasi.")
    return redirect("login")


@role_required("customer")
def customer_dashboard(request):
    customer = request.user.customer_profile
    registrations = customer.pendaftaran.select_related("event", "kategori_tiket", "pembayaran").all()
    active_count = registrations.filter(status_pendaftaran__in=["belum_dikonfirmasi", "dikonfirmasi", "check_in"]).count()
    confirmed_count = registrations.filter(status_pendaftaran__in=["dikonfirmasi", "check_in", "selesai"]).count()
    return render(request, "customer/dashboard.html", {
        "customer": customer,
        "registrations": registrations[:8],
        "active_count": active_count,
        "confirmed_count": confirmed_count,
        "ticket_count": registrations.filter(pembayaran__status_pembayaran="diterima").count(),
    })


@role_required("customer")
def daftar_tiket(request, slug, kategori_id):
    customer = request.user.customer_profile
    event = get_object_or_404(Event, slug=slug, status__in=[Event.StatusEvent.DIPUBLIKASIKAN, Event.StatusEvent.BERLANGSUNG])
    kategori = get_object_or_404(KategoriTiket, pk=kategori_id, event=event)
    existing = Pendaftaran.objects.filter(customer=customer, event=event).first()
    if existing:
        messages.info(request, "Anda sudah terdaftar pada event ini.")
        return redirect("detail_pendaftaran", pk=existing.pk)
    if not kategori.masih_tersedia:
        messages.error(request, "Kategori tiket tidak tersedia atau kuota telah habis.")
        return redirect("detail_event", slug=slug)
    form = PendaftaranForm(request.POST or None, customer=customer)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                kategori_locked = KategoriTiket.objects.select_for_update().get(pk=kategori.pk)
                if not kategori_locked.masih_tersedia:
                    messages.error(request, "Maaf, kuota tiket baru saja habis.")
                    return redirect("detail_event", slug=slug)
                pendaftaran = form.save(commit=False)
                pendaftaran.customer = customer
                pendaftaran.event = event
                pendaftaran.kategori_tiket = kategori_locked
                pendaftaran.harga_tiket = kategori_locked.harga
                pendaftaran.save()
                Pembayaran.objects.create(
                    pendaftaran=pendaftaran,
                    jumlah_pembayaran=kategori_locked.harga,
                )
            write_log(request, LogAktivitas.JenisAktivitas.TAMBAH, f"Mendaftar event {event.nama_event}", "Pendaftaran", pendaftaran.pk)
            messages.success(request, "Pendaftaran berhasil. Silakan unggah bukti pembayaran.")
            return redirect("upload_pembayaran", pk=pendaftaran.pk)
        except (IntegrityError, ValueError):
            messages.error(request, "Pendaftaran tidak dapat diproses. Periksa data dan coba kembali.")
    return render(request, "customer/pendaftaran_form.html", {"form": form, "event": event, "kategori": kategori})


@role_required("customer")
def detail_pendaftaran(request, pk):
    pendaftaran = get_object_or_404(
        Pendaftaran.objects.select_related("event", "kategori_tiket", "pembayaran"),
        pk=pk, customer=request.user.customer_profile,
    )
    return render(request, "customer/pendaftaran_detail.html", {"pendaftaran": pendaftaran})


@role_required("customer")
def upload_pembayaran(request, pk):
    pendaftaran = get_object_or_404(Pendaftaran, pk=pk, customer=request.user.customer_profile)
    pembayaran = pendaftaran.pembayaran
    if pembayaran.status_pembayaran == Pembayaran.StatusPembayaran.DITERIMA:
        messages.info(request, "Pembayaran sudah diterima dan tidak dapat diubah.")
        return redirect("detail_pendaftaran", pk=pk)
    form = PembayaranForm(request.POST or None, request.FILES or None, instance=pembayaran)
    if request.method == "POST" and form.is_valid():
        pembayaran = form.save(commit=False)
        pembayaran.jumlah_pembayaran = pendaftaran.harga_tiket
        pembayaran.save()
        write_log(request, LogAktivitas.JenisAktivitas.UBAH, f"Mengunggah bukti pembayaran {pembayaran.kode_pembayaran}", "Pembayaran", pembayaran.pk)
        messages.success(request, "Bukti pembayaran berhasil diunggah dan menunggu verifikasi petugas.")
        return redirect("detail_pendaftaran", pk=pk)
    pengaturan = PengaturanSistem.objects.first()
    return render(request, "customer/pembayaran_form.html", {
        "form": form, "pendaftaran": pendaftaran, "pembayaran": pembayaran, "pengaturan": pengaturan,
    })


@role_required("customer")
def tiket(request, pk):
    pendaftaran = get_object_or_404(
        Pendaftaran.objects.select_related("event", "kategori_tiket", "pembayaran"),
        pk=pk, customer=request.user.customer_profile,
    )
    if not pendaftaran.tiket_dapat_dicetak:
        messages.error(request, "E-ticket hanya tersedia setelah pembayaran diterima.")
        return redirect("detail_pendaftaran", pk=pk)
    return render(request, "customer/tiket.html", {"pendaftaran": pendaftaran})


@role_required("customer")
def profile(request):
    customer = request.user.customer_profile
    form = CustomerProfileForm(request.POST or None, request.FILES or None, instance=customer)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profil berhasil diperbarui.")
        return redirect("profile")
    return render(request, "customer/profile.html", {"form": form, "customer": customer})
