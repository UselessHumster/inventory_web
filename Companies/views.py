from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

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
    fields = ["name"]
    success_url = reverse_lazy("companies:company_list")

    def test_func(self):
        return self.request.user.is_superuser


class CompanyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Company
    template_name = "companies/company_form.html"
    fields = ["name"]
    success_url = reverse_lazy("companies:company_list")

    def test_func(self):
        return self.request.user.is_superuser


class CompanyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Company
    template_name = "companies/company_confirm_delete.html"
    success_url = reverse_lazy("companies:company_list")

    def test_func(self):
        return self.request.user.is_superuser
