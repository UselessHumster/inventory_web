from django import forms
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