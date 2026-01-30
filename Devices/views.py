from Companies.models import Company
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import ModelChoiceField
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from Employees.models import Employee

from .models import Equipment, EquipmentType


class EquipmentCompanyEmployeeFilterMixin:
    """Mixin to filter companies and employees in forms based on user permissions."""

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user

        # Filter companies
        if not user.is_superuser:
            company_field = form.fields.get("company")
            if isinstance(company_field, ModelChoiceField):
                company_field.queryset = Company.objects.filter(usercompany__user=user)

        # Filter employees based on selected company
        employee_field = form.fields.get("employee")
        if isinstance(employee_field, ModelChoiceField):
            # If a company is already selected (e.g., in update view or from initial data)
            # or if the user has only one company, filter employees for that company.
            initial_company = None
            if self.object: # Update view
                initial_company = self.object.company
            elif self.request.method == 'GET' and 'company' in self.request.GET:
                try:
                    initial_company = Company.objects.get(pk=self.request.GET['company'])
                except Company.DoesNotExist:
                    pass
            elif not user.is_superuser:
                companies_for_user = Company.objects.filter(usercompany__user=user)
                if companies_for_user.count() == 1:
                    initial_company = companies_for_user.first()

            if initial_company:
                employee_field.queryset = Employee.objects.filter(company=initial_company)
            else:
                employee_field.queryset = Employee.objects.none() # No company selected, no employees

        return form

    def get_initial(self):
        initial = super().get_initial()
        user = self.request.user
        # Automatically set company if user has access to only one
        if not user.is_superuser:
            companies_for_user = Company.objects.filter(usercompany__user=user)
            if companies_for_user.count() == 1:
                initial['company'] = companies_for_user.first()
        return initial


# EquipmentType Views
class EquipmentTypeListView(LoginRequiredMixin, ListView):
    model = EquipmentType
    template_name = "devices/equipmenttype_list.html"
    context_object_name = "equipment_types"


class EquipmentTypeCreateView(LoginRequiredMixin, CreateView):
    model = EquipmentType
    template_name = "devices/equipmenttype_form.html"
    fields = ["name"]
    success_url = reverse_lazy("devices:equipmenttype_list")


class EquipmentTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = EquipmentType
    template_name = "devices/equipmenttype_form.html"
    fields = ["name"]
    success_url = reverse_lazy("devices:equipmenttype_list")


class EquipmentTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = EquipmentType
    template_name = "devices/equipmenttype_confirm_delete.html"
    success_url = reverse_lazy("devices:equipmenttype_list")


# Equipment Views
class EquipmentListView(LoginRequiredMixin, ListView):
    model = Equipment
    template_name = "devices/equipment_list.html"
    context_object_name = "equipment_items"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_superuser:
            return queryset
        return queryset.filter(company__usercompany__user=user)


class EquipmentCreateView(LoginRequiredMixin, EquipmentCompanyEmployeeFilterMixin, CreateView):
    model = Equipment
    template_name = "devices/equipment_form.html"
    fields = ["company", "employee", "equipment_type", "model", "serial_number", "condition", "comment"]
    success_url = reverse_lazy("devices:equipment_list")


class EquipmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, EquipmentCompanyEmployeeFilterMixin, UpdateView):
    model = Equipment
    template_name = "devices/equipment_form.html"
    fields = ["company", "employee", "equipment_type", "model", "serial_number", "condition", "comment"]
    success_url = reverse_lazy("devices:equipment_list")

    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        equipment = self.get_object()
        return equipment.company in Company.objects.filter(usercompany__user=user)


class EquipmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Equipment
    template_name = "devices/equipment_confirm_delete.html"
    success_url = reverse_lazy("devices:equipment_list")

    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        equipment = self.get_object()
        return equipment.company in Company.objects.filter(usercompany__user=user)
