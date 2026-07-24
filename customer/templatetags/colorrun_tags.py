from django import template

register = template.Library()


@register.filter
def rupiah(value):
    try:
        return "Rp{:,.0f}".format(float(value)).replace(",", ".")
    except (TypeError, ValueError):
        return "Rp0"


@register.filter
def splitlines(value):
    return [line.strip() for line in (value or "").splitlines() if line.strip()]


@register.filter
def status_class(value):
    mapping = {
        "diterima": "success", "dikonfirmasi": "success", "check_in": "success", "selesai": "success",
        "menunggu_verifikasi": "warning", "menunggu_pembayaran": "neutral", "belum_dikonfirmasi": "neutral",
        "ditolak": "danger", "dibatalkan": "danger", "draft": "neutral",
        "dipublikasikan": "success", "berlangsung": "warning",
    }
    return mapping.get(str(value), "neutral")
