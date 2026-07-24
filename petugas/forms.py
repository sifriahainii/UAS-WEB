from django import forms


class CheckInKodeForm(forms.Form):
    kode_check_in = forms.CharField(
        max_length=20,
        label="Kode unik peserta",
        widget=forms.TextInput(attrs={
            "class": "form-control code-input",
            "placeholder": "Contoh: RUN-A7K9P2",
            "autocomplete": "off",
            "autofocus": True,
        }),
    )

    def clean_kode_check_in(self):
        return self.cleaned_data["kode_check_in"].strip().upper().replace(" ", "")


class VerifikasiPembayaranForm(forms.Form):
    keputusan = forms.ChoiceField(
        choices=[("terima", "Terima pembayaran"), ("tolak", "Tolak pembayaran")],
        widget=forms.RadioSelect,
    )
    catatan_petugas = forms.CharField(
        required=False, label="Catatan petugas", widget=forms.Textarea(attrs={"class": "form-control", "rows": 3})
    )
    alasan_penolakan = forms.CharField(
        required=False, label="Alasan penolakan", widget=forms.Textarea(attrs={"class": "form-control", "rows": 3})
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("keputusan") == "tolak" and not cleaned.get("alasan_penolakan", "").strip():
            self.add_error("alasan_penolakan", "Alasan penolakan wajib diisi.")
        return cleaned
