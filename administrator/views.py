import csv

from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from colorrun.utils import role_required, write_log
from customer.models import Customer, Pendaftaran, Pembayaran
from petugas.models import CheckIn, Petugas
from .forms import (
    EventForm, 
    KategoriTiketForm, 
    PetugasCreateForm, 
    PetugasEditForm
)
from .models import (
    Event, 
    KategoriTiket, 
    LogAktivitas
)


@role_required("administrator")
def administrator_dashboard(request):
    confirmed = Pendaftaran.objects.filter(status_pendaftaran__in=["dikonfirmasi", "check_in", "selesai"])
    context = {
        "total_event": Event.objects.count(),
        "total_customer": Customer.objects.count(),
        "total_petugas": Petugas.objects.count(),
        "total_tiket_terjual": confirmed.count(),
        "total_pembayaran_masuk": Pembayaran.objects.filter(status_pembayaran="diterima").aggregate(total=Sum("jumlah_pembayaran"))["total"] or 0,
        "tiket_belum_dibayar": Pembayaran.objects.filter(status_pembayaran="menunggu_pembayaran").count(),
        "menunggu_verifikasi": Pembayaran.objects.filter(status_pembayaran="menunggu_verifikasi").count(),
        "total_checkin": CheckIn.objects.count(),
        "events": Event.objects.prefetch_related("kategori_tiket")[:6],
        "recent_registrations": Pendaftaran.objects.select_related("event", "kategori_tiket", "pembayaran")[:8],
    }
    return render(request, "administrator/dashboard.html", context)


@role_required("administrator")
def event_list(request):
    query = request.GET.get("q", "").strip()
    events = Event.objects.prefetch_related("kategori_tiket")
    if query:
        events = events.filter(Q(nama_event__icontains=query) | Q(lokasi__icontains=query))
    return render(request, "administrator/event_list.html", {"events": events, "query": query})


@role_required("administrator")
def event_create(request):
    form = EventForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        event = form.save(commit=False)
        event.dibuat_oleh = request.user
        event.save()
        write_log(request, LogAktivitas.JenisAktivitas.TAMBAH, f"Menambah event {event.nama_event}", "Event", event.pk)
        messages.success(request, "Event berhasil ditambahkan.")
        return redirect("administrator_event_list")
    return render(request, "administrator/form.html", {"form": form, "title": "Tambah Event", "back_url": "administrator_event_list"})


@role_required("administrator")
def event_update(request, pk):
    event = get_object_or_404(Event, pk=pk)
    form = EventForm(request.POST or None, request.FILES or None, instance=event)
    if request.method == "POST" and form.is_valid():
        event = form.save()
        write_log(request, LogAktivitas.JenisAktivitas.UBAH, f"Mengubah event {event.nama_event}", "Event", event.pk)
        messages.success(request, "Event berhasil diperbarui.")
        return redirect("administrator_event_list")
    return render(request, "administrator/form.html", {"form": form, "title": "Edit Event", "back_url": "administrator_event_list"})


@role_required("administrator")
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == "POST":
        name = event.nama_event
        try:
            event.delete()
            write_log(request, LogAktivitas.JenisAktivitas.HAPUS, f"Menghapus event {name}", "Event", pk)
            messages.success(request, "Event berhasil dihapus.")
        except Exception:
            messages.error(request, "Event tidak dapat dihapus karena sudah memiliki transaksi.")
        return redirect("administrator_event_list")
    return render(request, "administrator/confirm_delete.html", {"object": event, "title": "Hapus Event", "back_url": "administrator_event_list"})


@role_required("administrator")
def kategori_list(request):
    categories = KategoriTiket.objects.select_related("event")
    return render(request, "administrator/kategori_list.html", {"categories": categories})


@role_required("administrator")
def kategori_create(request):
    form = KategoriTiketForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        write_log(request, LogAktivitas.JenisAktivitas.TAMBAH, f"Menambah kategori {obj.nama_kategori}", "KategoriTiket", obj.pk)
        messages.success(request, "Kategori tiket berhasil ditambahkan.")
        return redirect("administrator_kategori_list")
    return render(request, "administrator/form.html", {"form": form, "title": "Tambah Kategori Tiket", "back_url": "administrator_kategori_list"})


@role_required("administrator")
def kategori_update(request, pk):
    obj = get_object_or_404(KategoriTiket, pk=pk)
    form = KategoriTiketForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        write_log(request, LogAktivitas.JenisAktivitas.UBAH, f"Mengubah kategori {obj.nama_kategori}", "KategoriTiket", obj.pk)
        messages.success(request, "Kategori tiket berhasil diperbarui.")
        return redirect("administrator_kategori_list")
    return render(request, "administrator/form.html", {"form": form, "title": "Edit Kategori Tiket", "back_url": "administrator_kategori_list"})


@role_required("administrator")
def kategori_delete(request, pk):
    obj = get_object_or_404(KategoriTiket, pk=pk)
    if request.method == "POST":
        try:
            obj.delete()
            messages.success(request, "Kategori tiket berhasil dihapus.")
        except Exception:
            messages.error(request, "Kategori tidak dapat dihapus karena sudah digunakan.")
        return redirect("administrator_kategori_list")
    return render(request, "administrator/confirm_delete.html", {"object": obj, "title": "Hapus Kategori", "back_url": "administrator_kategori_list"})


@role_required("administrator")
def petugas_list(request):
    staff = Petugas.objects.select_related("user")
    return render(request, "administrator/petugas_list.html", {"staff": staff})


@role_required("administrator")
def petugas_create(request):
    form = PetugasCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        write_log(request, LogAktivitas.JenisAktivitas.TAMBAH, f"Menambah petugas {obj.nama_lengkap}", "Petugas", obj.pk)
        messages.success(request, "Akun petugas berhasil dibuat.")
        return redirect("administrator_petugas_list")
    return render(request, "administrator/form.html", {"form": form, "title": "Tambah Petugas", "back_url": "administrator_petugas_list"})


@role_required("administrator")
def petugas_update(request, pk):
    obj = get_object_or_404(Petugas, pk=pk)
    form = PetugasEditForm(request.POST or None, request.FILES or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        write_log(request, LogAktivitas.JenisAktivitas.UBAH, f"Mengubah petugas {obj.nama_lengkap}", "Petugas", obj.pk)
        messages.success(request, "Data petugas berhasil diperbarui.")
        return redirect("administrator_petugas_list")
    return render(request, "administrator/form.html", {"form": form, "title": "Edit Petugas", "back_url": "administrator_petugas_list"})


@role_required("administrator")
def customer_list(request):
    query = request.GET.get("q", "").strip()
    customers = Customer.objects.select_related("user").annotate(total_daftar=Count("pendaftaran"))
    if query:
        customers = customers.filter(Q(nama_lengkap__icontains=query) | Q(user__email__icontains=query) | Q(nomor_hp__icontains=query))
    return render(request, "administrator/customer_list.html", {"customers": customers, "query": query})


@role_required("administrator")
def pendaftaran_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "semua")
    registrations = Pendaftaran.objects.select_related("customer", "event", "kategori_tiket", "pembayaran")
    if query:
        registrations = registrations.filter(Q(nama_lengkap__icontains=query) | Q(kode_pendaftaran__icontains=query) | Q(kode_check_in__icontains=query))
    if status != "semua":
        registrations = registrations.filter(status_pendaftaran=status)
    return render(request, "administrator/pendaftaran_list.html", {
        "registrations": registrations, "query": query, "status": status,
        "status_choices": Pendaftaran.StatusPendaftaran.choices,
    })


def _report_queryset(request):
    event_id = request.GET.get("event", "")
    status = request.GET.get("status", "")
    qs = Pendaftaran.objects.select_related("event", "kategori_tiket", "pembayaran", "check_in")
    if event_id:
        qs = qs.filter(event_id=event_id)
    if status:
        qs = qs.filter(status_pendaftaran=status)
    return qs, event_id, status


@role_required("administrator")
def laporan(request):
    registrations, event_id, status = _report_queryset(request)
    payments = Pembayaran.objects.select_related("pendaftaran__event", "diverifikasi_oleh")
    if event_id:
        payments = payments.filter(pendaftaran__event_id=event_id)
    context = {
        "registrations": registrations,
        "payments": payments,
        "events": Event.objects.all(),
        "event_id": event_id,
        "status": status,
        "status_choices": Pendaftaran.StatusPendaftaran.choices,
        "total_peserta": registrations.count(),
        "total_dikonfirmasi": registrations.filter(status_pendaftaran__in=["dikonfirmasi", "check_in", "selesai"]).count(),
        "total_checkin": registrations.filter(status_pendaftaran="check_in").count(),
        "total_pendapatan": payments.filter(status_pembayaran="diterima").aggregate(total=Sum("jumlah_pembayaran"))["total"] or 0,
    }
    return render(request, "administrator/laporan.html", context)


@role_required("administrator")
def laporan_csv(request):
    registrations, _, _ = _report_queryset(request)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="laporan_colorrun.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(["Kode Pendaftaran", "Kode Check-in", "Nama", "Event", "Kategori", "Status", "Pembayaran", "Waktu Daftar"])
    for item in registrations:
        payment_status = item.pembayaran.get_status_pembayaran_display() if hasattr(item, "pembayaran") else "-"
        writer.writerow([
            item.kode_pendaftaran, item.kode_check_in, item.nama_lengkap, item.event.nama_event,
            item.kategori_tiket.nama_kategori, item.get_status_pendaftaran_display(), payment_status,
            item.waktu_pendaftaran.strftime("%d-%m-%Y %H:%M"),
        ])
    return response
