from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from administrator.models import LogAktivitas
from colorrun.utils import role_required, write_log
from customer.models import Pendaftaran, Pembayaran
from .forms import CheckInKodeForm, VerifikasiPembayaranForm
from .models import CheckIn


@role_required("petugas")
def petugas_dashboard(request):
    petugas = request.user.petugas_profile
    pending = Pembayaran.objects.filter(status_pembayaran=Pembayaran.StatusPembayaran.MENUNGGU_VERIFIKASI)
    today = timezone.localdate()
    checkin_today = CheckIn.objects.filter(waktu_check_in__date=today)
    recent = Pendaftaran.objects.select_related("event", "kategori_tiket", "pembayaran").order_by("-waktu_pendaftaran")[:8]
    return render(request, "petugas/dashboard.html", {
        "petugas": petugas,
        "pending_count": pending.count(),
        "confirmed_count": Pendaftaran.objects.filter(status_pendaftaran=Pendaftaran.StatusPendaftaran.DIKONFIRMASI).count(),
        "checkin_today": checkin_today.count(),
        "participant_count": Pendaftaran.objects.count(),
        "recent": recent,
    })


@role_required("petugas")
def daftar_pembayaran(request):
    status = request.GET.get("status", Pembayaran.StatusPembayaran.MENUNGGU_VERIFIKASI)
    query = request.GET.get("q", "").strip()
    payments = Pembayaran.objects.select_related("pendaftaran__event", "pendaftaran__kategori_tiket")
    if status and status != "semua":
        payments = payments.filter(status_pembayaran=status)
    if query:
        payments = payments.filter(
            Q(kode_pembayaran__icontains=query) | Q(pendaftaran__nama_lengkap__icontains=query)
            | Q(pendaftaran__kode_pendaftaran__icontains=query)
        )
    return render(request, "petugas/pembayaran_list.html", {
        "payments": payments, "status": status, "query": query,
        "status_choices": Pembayaran.StatusPembayaran.choices,
    })


@role_required("petugas")
def verifikasi_pembayaran(request, pk):
    payment = get_object_or_404(
        Pembayaran.objects.select_related("pendaftaran__event", "pendaftaran__kategori_tiket"), pk=pk
    )
    if payment.status_pembayaran == Pembayaran.StatusPembayaran.DITERIMA:
        messages.info(request, "Pembayaran ini sudah diterima.")
        return redirect("daftar_pembayaran")
    form = VerifikasiPembayaranForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            payment = Pembayaran.objects.select_for_update().select_related("pendaftaran").get(pk=pk)
            payment.diverifikasi_oleh = request.user.petugas_profile
            payment.tanggal_verifikasi = timezone.now()
            payment.catatan_petugas = form.cleaned_data.get("catatan_petugas", "")
            if form.cleaned_data["keputusan"] == "terima":
                payment.status_pembayaran = Pembayaran.StatusPembayaran.DITERIMA
                payment.alasan_penolakan = ""
                payment.pendaftaran.status_pendaftaran = Pendaftaran.StatusPendaftaran.DIKONFIRMASI
                payment.pendaftaran.save(update_fields=["status_pendaftaran", "diperbarui_pada"])
                message = "Pembayaran diterima dan pendaftaran telah dikonfirmasi."
            else:
                payment.status_pembayaran = Pembayaran.StatusPembayaran.DITOLAK
                payment.alasan_penolakan = form.cleaned_data["alasan_penolakan"]
                payment.pendaftaran.status_pendaftaran = Pendaftaran.StatusPendaftaran.BELUM_DIKONFIRMASI
                payment.pendaftaran.save(update_fields=["status_pendaftaran", "diperbarui_pada"])
                message = "Pembayaran ditolak. Customer dapat mengunggah ulang bukti pembayaran."
            payment.save()
        write_log(request, LogAktivitas.JenisAktivitas.VERIFIKASI, f"Verifikasi {payment.kode_pembayaran}: {payment.status_pembayaran}", "Pembayaran", payment.pk)
        messages.success(request, message)
        return redirect("daftar_pembayaran")
    return render(request, "petugas/pembayaran_verify.html", {"payment": payment, "form": form})


@role_required("petugas")
def daftar_peserta(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "semua")
    registrations = Pendaftaran.objects.select_related("event", "kategori_tiket", "pembayaran")
    if query:
        registrations = registrations.filter(
            Q(nama_lengkap__icontains=query) | Q(kode_pendaftaran__icontains=query)
            | Q(kode_check_in__icontains=query)
        )
    if status != "semua":
        registrations = registrations.filter(status_pendaftaran=status)
    return render(request, "petugas/peserta_list.html", {
        "registrations": registrations, "query": query, "status": status,
        "status_choices": Pendaftaran.StatusPendaftaran.choices,
    })


@role_required("petugas")
def check_in_kode(request):
    form = CheckInKodeForm(request.POST or None)
    hasil = None
    if request.method == "POST" and form.is_valid():
        code = form.cleaned_data["kode_check_in"]
        with transaction.atomic():
            registration = Pendaftaran.objects.select_for_update().select_related(
                "event", "kategori_tiket", "pembayaran"
            ).filter(kode_check_in__iexact=code).first()
            if not registration:
                messages.error(request, "Kode unik tidak ditemukan. Periksa kembali kode peserta.")
            elif registration.sudah_check_in:
                messages.warning(request, f"Peserta sudah check-in pada {registration.check_in.waktu_check_in:%d-%m-%Y %H:%M}.")
                hasil = registration
            elif not hasattr(registration, "pembayaran") or registration.pembayaran.status_pembayaran != Pembayaran.StatusPembayaran.DITERIMA:
                messages.error(request, "Check-in ditolak karena pembayaran belum diterima.")
                hasil = registration
            elif registration.status_pendaftaran != Pendaftaran.StatusPendaftaran.DIKONFIRMASI:
                messages.error(request, "Status pendaftaran belum dikonfirmasi atau sudah tidak aktif.")
                hasil = registration
            else:
                CheckIn.objects.create(
                    pendaftaran=registration,
                    petugas=request.user.petugas_profile,
                    metode="kode_unik",
                    kode_dimasukkan=code,
                )
                registration.status_pendaftaran = Pendaftaran.StatusPendaftaran.CHECK_IN
                registration.save(update_fields=["status_pendaftaran", "diperbarui_pada"])
                write_log(request, LogAktivitas.JenisAktivitas.CHECK_IN, f"Check-in peserta {registration.nama_lengkap} dengan kode unik", "Pendaftaran", registration.pk)
                messages.success(request, f"Check-in berhasil untuk {registration.nama_lengkap}.")
                hasil = registration
                form = CheckInKodeForm()
    recent = CheckIn.objects.select_related("pendaftaran__event", "petugas")[:8]
    return render(request, "petugas/checkin.html", {"form": form, "hasil": hasil, "recent": recent})


@role_required("petugas")
def riwayat_checkin(request):
    query = request.GET.get("q", "").strip()
    history = CheckIn.objects.select_related("pendaftaran__event", "petugas")
    if query:
        history = history.filter(
            Q(pendaftaran__nama_lengkap__icontains=query) | Q(pendaftaran__kode_check_in__icontains=query)
            | Q(pendaftaran__kode_pendaftaran__icontains=query)
        )
    return render(request, "petugas/checkin_history.html", {"history": history, "query": query})
