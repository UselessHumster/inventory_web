from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .models import UserCompany


class UserCompanyListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = UserCompany
    template_name = "users/usercompany_list.html"
    context_object_name = "user_companies"

    def test_func(self):
        return self.request.user.is_superuser


class UserCompanyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = UserCompany
    template_name = "users/usercompany_form.html"
    fields = ["user", "company"]
    success_url = reverse_lazy("users:usercompany_list")

    def test_func(self):
        return self.request.user.is_superuser


class UserCompanyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = UserCompany
    template_name = "users/usercompany_form.html"
    fields = ["user", "company"]
    success_url = reverse_lazy("users:usercompany_list")

    def test_func(self):
        return self.request.user.is_superuser


class UserCompanyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = UserCompany
    template_name = "users/usercompany_confirm_delete.html"
    success_url = reverse_lazy("users:usercompany_list")

    def test_func(self):
        return self.request.user.is_superuser
