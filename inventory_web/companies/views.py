from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import CompanyUpdateForm
from .models import Company


class CompanyListView(LoginRequiredMixin, ListView):
    model = Company
    template_name = "companies/company_list.html"
    context_object_name = "companies"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_superuser:
            return queryset
        return queryset.filter(usercompany__user=user)


class CompanyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Company
    template_name = "companies/company_form.html"
    fields = ["name", "telegram_chat_id", "equipment_email_to", "equipment_email_cc"]
    success_url = reverse_lazy("companies:company_list")

    def test_func(self):
        return self.request.user.is_superuser


class CompanyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Company
    form_class = CompanyUpdateForm
    template_name = "companies/company_form.html"
    success_url = reverse_lazy("companies:company_list")

    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if "regenerate_api_key" in request.POST:
            self.object.regenerate_api_key()
            self.object.save(update_fields=["api_key"])
            messages.success(request, "API-ключ компании сгенерирован.")
            return redirect("companies:company_update", pk=self.object.pk)
        return super().post(request, *args, **kwargs)


class CompanyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Company
    template_name = "companies/company_confirm_delete.html"
    success_url = reverse_lazy("companies:company_list")

    def test_func(self):
        return self.request.user.is_superuser
