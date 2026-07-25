from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from .models import Event, KategoriTiket
from petugas.models import Petugas


class StyledModelForm(forms.ModelForm):
    def apply_styles(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
            else:
                field.widget.attrs.setdefault("class", "form-control")


class EventForm(StyledModelForm):
    class Meta:
        model = Event
        exclude = ["slug", "dibuat_oleh"]
        widgets = {
            "tanggal_mulai": forms.DateInput(attrs={"type": "date"}),
            "jam_mulai": forms.TimeInput(attrs={"type": "time"}),
            "jam_selesai": forms.TimeInput(attrs={"type": "time"}),
            "deskripsi": forms.Textarea(attrs={"rows": 5}),
            "rute_color_run": forms.Textarea(attrs={"rows": 3}),
            "fasilitas": forms.Textarea(attrs={"rows": 4}),
            "poster_event": forms.FileInput(attrs={"accept": ".jpg,.jpeg,.png,.webp"}),
            "banner_event": forms.FileInput(attrs={"accept": ".jpg,.jpeg,.png,.webp"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()

    def save(self, commit=True):
        event = super().save(commit=False)
        if not event.slug:
            base = slugify(event.nama_event) or "event"
            slug = base
            i = 2
            while Event.objects.filter(slug=slug).exclude(pk=event.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            event.slug = slug
        if commit:
            event.save()
            self.save_m2m()
        return event


class KategoriTiketForm(StyledModelForm):
    class Meta:
        model = KategoriTiket
        fields = [
            "event", "nama_kategori", "deskripsi", "harga", "kuota",
            "tanggal_penjualan_mulai", "tanggal_penjualan_selesai", "aktif",
        ]
        widgets = {
            "deskripsi": forms.Textarea(attrs={"rows": 3}),
            "tanggal_penjualan_mulai": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "tanggal_penjualan_selesai": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["tanggal_penjualan_mulai"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["tanggal_penjualan_selesai"].input_formats = ["%Y-%m-%dT%H:%M"]


class PetugasCreateForm(forms.Form):
    kode_petugas = forms.CharField(max_length=20, label="Kode petugas")
    nama_lengkap = forms.CharField(max_length=150, label="Nama lengkap")
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    nomor_hp = forms.CharField(max_length=20, label="Nomor HP")
    jenis_kelamin = forms.ChoiceField(choices=[("", "Pilih"), *Petugas.JenisKelamin.choices], required=False)
    alamat = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("Username sudah digunakan.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email sudah digunakan.")
        return email

    def clean_kode_petugas(self):
        kode = self.cleaned_data["kode_petugas"].strip().upper()
        if Petugas.objects.filter(kode_petugas__iexact=kode).exists():
            raise ValidationError("Kode petugas sudah digunakan.")
        return kode

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data["username"], email=self.cleaned_data["email"],
            password=self.cleaned_data["password"], first_name=self.cleaned_data["nama_lengkap"],
        )
        return Petugas.objects.create(
            user=user, kode_petugas=self.cleaned_data["kode_petugas"],
            nama_lengkap=self.cleaned_data["nama_lengkap"], nomor_hp=self.cleaned_data["nomor_hp"],
            jenis_kelamin=self.cleaned_data["jenis_kelamin"], alamat=self.cleaned_data["alamat"],
        )


class PetugasEditForm(StyledModelForm):
    email = forms.EmailField()

    class Meta:
        model = Petugas
        fields = ["kode_petugas", "nama_lengkap", "nomor_hp", "jenis_kelamin", "alamat", "foto", "aktif"]
        widgets = {"alamat": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["email"].initial = self.instance.user.email

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.user_id).exists():
            raise ValidationError("Email sudah digunakan.")
        return email

    def save(self, commit=True):
        petugas = super().save(commit=False)
        petugas.user.email = self.cleaned_data["email"]
        petugas.user.first_name = petugas.nama_lengkap
        petugas.user.is_active = petugas.aktif
        if commit:
            petugas.user.save()
            petugas.save()
        return petugas
