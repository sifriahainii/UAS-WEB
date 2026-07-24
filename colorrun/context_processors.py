from .utils import get_user_role


def global_context(request):
    from administrator.models import PengaturanSistem
    pengaturan = PengaturanSistem.objects.first()
    return {
        "current_role": get_user_role(request.user),
        "pengaturan_sistem": pengaturan,
    }
