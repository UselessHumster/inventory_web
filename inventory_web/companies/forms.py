from django import forms
from .models import Company

class CompanyUpdateForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["name", "telegram_chat_id", "report_file"]
        widgets = {
            "report_file": forms.ClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            # для всех виджетов навешиваем класс Bootstrap
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " form-control").strip()
