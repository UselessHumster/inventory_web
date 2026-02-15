from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import ModelChoiceField
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from inventory_web.companies.models import Company

from .models import Employee
from .filters import EmployeeFilter


class EmployeeCompanyFilterMixin:
    """Mixin to filter companies in forms based on user permissions."""

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        if not user.is_superuser:
            company_field = form.fields.get("company")
            if isinstance(company_field, ModelChoiceField):
                company_field.queryset = Company.objects.filter(usercompany__user=user)
        return form


class EmployeeListView(LoginRequiredMixin, ListView):
    model = Employee
    template_name = "employees/employee_list.html"
    context_object_name = "employees"

    def get_queryset(self):
        queryset = super().get_queryset()

        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                company__usercompany__user=self.request.user
            )

        self.filterset = EmployeeFilter(
            self.request.GET,
            queryset=queryset
        )

        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        return context


class EmployeeCreateView(LoginRequiredMixin, EmployeeCompanyFilterMixin, CreateView):
    model = Employee
    template_name = "employees/employee_form.html"
    fields = ["name", "company", "email", "phone", "city", "is_active"]
    success_url = reverse_lazy("employees:employee_list")

    def form_valid(self, form):
        # If user has access to only one company, assign it automatically
        user = self.request.user
        if not user.is_superuser:
            companies = Company.objects.filter(usercompany__user=user)
            if companies.count() == 1:
                form.instance.company = companies.first()
        return super().form_valid(form)


class EmployeeUpdateView(LoginRequiredMixin, UserPassesTestMixin, EmployeeCompanyFilterMixin, UpdateView):
    model = Employee
    template_name = "employees/employee_form.html"
    fields = ["name", "company", "email", "phone", "city", "is_active"]
    success_url = reverse_lazy("employees:employee_list")

    def test_func(self):
        # Only superuser or user with access to the employee's company can update
        user = self.request.user
        if user.is_superuser:
            return True
        employee = self.get_object()
        return employee.company in Company.objects.filter(usercompany__user=user)


class EmployeeDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Employee
    template_name = "employees/employee_confirm_delete.html"
    success_url = reverse_lazy("employees:employee_list")

    def test_func(self):
        # Only superuser or user with access to the employee's company can delete
        user = self.request.user
        if user.is_superuser:
            return True
        employee = self.get_object()
        return employee.company in Company.objects.filter(usercompany__user=user)
