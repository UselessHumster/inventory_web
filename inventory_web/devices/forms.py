from django import forms

from inventory_web.companies.models import Company

from .models import Equipment


class EquipmentCreateForm(forms.ModelForm):
    send_email = forms.BooleanField(
        required=False,
        label="Отправить по почте",
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input"}
        )
    )

    email_to = forms.CharField(
        required=False,
        label="Кому",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "email1@mail.com, email2@mail.com"
        })
    )

    email_cc = forms.CharField(
        required=False,
        label="Копия",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "email1@mail.com, email2@mail.com"
        })
    )

    send_act = forms.BooleanField(
        required=False,
        initial=True,
        label="Отправить акт",
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input"}
        )
    )

    class Meta:
        model = Equipment
        fields = [
            "company",
            "employee",
            "equipment_type",
            "model",
            "serial_number",
            "condition",
            "comment",
        ]

    def clean(self):
        cleaned_data = super().clean()
        send_email = cleaned_data.get("send_email")

        if send_email:
            if not cleaned_data.get("email_to"):
                raise forms.ValidationError(
                    "Укажите хотя бы одного получателя"
                )

        return cleaned_data


class CitylinkImportUploadForm(forms.Form):
    file = forms.FileField(
        label="Файл Citilink",
        widget=forms.FileInput(
            attrs={
                "class": "form-control",
                "accept": (
                    ".xls,.xlsx,application/vnd.ms-excel,"
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
            }
        ),
    )
    company = forms.ModelChoiceField(
        queryset=Company.objects.none(),
        label="Компания",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    email_to = forms.CharField(
        required=False,
        label="Кому",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "email1@mail.com, email2@mail.com",
            }
        ),
    )
    email_cc = forms.CharField(
        required=False,
        label="Копия",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "email1@mail.com, email2@mail.com",
            }
        ),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and not user.is_superuser:
            self.fields["company"].queryset = Company.objects.filter(usercompany__user=user).distinct()
        else:
            self.fields["company"].queryset = Company.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        email_to = cleaned_data.get("email_to", "").strip()
        email_cc = cleaned_data.get("email_cc", "").strip()

        if email_cc and not email_to:
            raise forms.ValidationError("Укажите получателя в поле «Кому».")

        return cleaned_data
