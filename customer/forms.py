from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Customer, Pendaftaran, Pembayaran


class StyledFormMixin:
    def apply_styles(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            else:
                widget.attrs.setdefault("class", "form-control")
            if not isinstance(widget, (forms.Select, forms.FileInput, forms.CheckboxInput)):
                widget.attrs.setdefault("placeholder", field.label)


class CustomerRegisterForm(StyledFormMixin, forms.Form):
    nama_lengkap = forms.CharField(max_length=150, label="Nama lengkap")
    username = forms.CharField(max_length=150, label="Username")
    email = forms.EmailField(label="Email")
    nomor_hp = forms.CharField(max_length=20, label="Nomor HP")
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Konfirmasi password")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("Username sudah digunakan.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Email sudah terdaftar.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Konfirmasi password tidak sama.")
        if p1:
            try:
                validate_password(p1)
            except ValidationError as exc:
                self.add_error("password1", exc)
        return cleaned

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
            first_name=self.cleaned_data["nama_lengkap"],
        )
        Customer.objects.create(
            user=user,
            nama_lengkap=self.cleaned_data["nama_lengkap"],
            nomor_hp=self.cleaned_data["nomor_hp"],
        )
        return user


class PendaftaranForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Pendaftaran
        fields = [
            "nama_lengkap", "email", "nomor_hp", "tanggal_lahir", "jenis_kelamin", "ukuran_kaos",
            
        ]
        widgets = {
            "tanggal_lahir": forms.DateInput(attrs={"type": "date"}),
            
        }

    def __init__(self, *args, customer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
    
        if customer and not self.is_bound:
            self.initial.update({
                "nama_lengkap": customer.nama_lengkap,
                "email": customer.user.email,
                "nomor_hp": customer.nomor_hp,
                "tanggal_lahir": customer.tanggal_lahir,
                "jenis_kelamin": customer.jenis_kelamin,
            })


class PembayaranForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Pembayaran
        fields = ["metode_pembayaran", "nama_pengirim", "bank_pengirim", "bukti_pembayaran"]
        widgets = {"bukti_pembayaran": forms.FileInput(attrs={"accept": ".jpg,.jpeg,.png,.webp"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()
        self.fields["bukti_pembayaran"].required = True

    def clean_bukti_pembayaran(self):
        file = self.cleaned_data.get("bukti_pembayaran")
        if file and file.size > 5 * 1024 * 1024:
            raise ValidationError("Ukuran file maksimal 5 MB.")
        return file


class CustomerProfileForm(StyledFormMixin, forms.ModelForm):
    email = forms.EmailField(label="Email")

    class Meta:
        model = Customer
        fields = [
            "nama_lengkap",
            "nomor_hp",
            "tanggal_lahir",
            "jenis_kelamin",
            "alamat",
        ]

        widgets = {
            "tanggal_lahir": forms.DateInput(
                attrs={"type": "date"}
            ),
            "alamat": forms.Textarea(
                attrs={"rows": 3}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()

        self.fields["email"].initial = (
            self.instance.user.email
            if self.instance.pk
            else ""
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if (
            User.objects
            .filter(email__iexact=email)
            .exclude(pk=self.instance.user_id)
            .exists()
        ):
            raise ValidationError("Email sudah digunakan.")

        return email

    def save(self, commit=True):
        customer = super().save(commit=False)

        customer.user.email = self.cleaned_data["email"]
        customer.user.first_name = customer.nama_lengkap

        if commit:
            customer.user.save(
                update_fields=["email", "first_name"]
            )
            customer.save()

        return customer