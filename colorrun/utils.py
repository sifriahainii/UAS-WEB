from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def get_user_role(user):
    if not getattr(user, "is_authenticated", False):
        return "guest"
    if user.is_superuser or hasattr(user, "administrator_profile"):
        return "administrator"
    if hasattr(user, "petugas_profile"):
        return "petugas"
    if hasattr(user, "customer_profile"):
        return "customer"
    return "unknown"


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"/login/?next={request.get_full_path()}")
            role = get_user_role(request.user)
            if role not in allowed_roles:
                messages.error(request, "Anda tidak memiliki hak akses ke halaman tersebut.")
                if role == "administrator":
                    return redirect("administrator_dashboard")
                if role == "petugas":
                    return redirect("petugas_dashboard")
                if role == "customer":
                    return redirect("customer_dashboard")
                return redirect("home")
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    return forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")


def write_log(request, jenis, deskripsi, nama_tabel="", id_objek=""):
    # Import di dalam fungsi untuk menghindari circular import saat startup.
    from administrator.models import LogAktivitas
    LogAktivitas.objects.create(
        user=request.user if request.user.is_authenticated else None,
        jenis_aktivitas=jenis,
        deskripsi=deskripsi,
        nama_tabel=nama_tabel,
        id_objek=str(id_objek or ""),
        alamat_ip=client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:1000],
    )
