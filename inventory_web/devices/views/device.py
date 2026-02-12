from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import ModelChoiceField
from django.shortcuts import HttpResponse, redirect
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from inventory_web.companies.models import Company
from inventory_web.devices.models import Equipment, Report
from inventory_web.devices.utils import prepare_device_to_report
from inventory_web.employees.models import Employee
from inventory_web.reprtsgen import CellsToFill, generate_report
from inventory_web.telegram import send_device_creation


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

            company_id = self.request.POST.get(
                'company') if self.request.method == 'POST' else (
                self.request.GET.get('company'))
            if company_id:
                try:
                    initial_company = Company.objects.get(pk=company_id)
                except Company.DoesNotExist:
                    pass

            if self.object: # Update view
                initial_company = self.object.company

            elif self.request.method == 'GET' and 'company' in self.request.GET:
                try:
                    initial_company = Company.objects.get(
                        pk=self.request.GET['company'])
                except Company.DoesNotExist:
                    pass
            elif not user.is_superuser:
                companies_for_user = Company.objects.filter(
                    usercompany__user=user)
                if companies_for_user.count() == 1:
                    initial_company = companies_for_user.first()
            if initial_company:
                employee_field.queryset = Employee.objects.filter(
                    company=initial_company)
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

    def form_valid(self, form):
        device = form.save()
        company = device.company

        if company.telegram_chat_id:
            messages.success(
                self.request,
                f'Оборудование "{device.model}" создано успешно, уведомление отправлено!')
            send_device_creation(
                device=device,
                chat_id=company.telegram_chat_id)
        else:
            messages.warning(
                self.request,
                f'Оборудование "{device.model}" создано успешно, но у компании нет телеграм чата, уведомление не отправлено!')
        return redirect(self.success_url)


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


class EquipmentReportDownloadView(LoginRequiredMixin, DetailView):
    model = Equipment
    template_name = None
    fields = ["company", "employee", "equipment_type", "model", "serial_number",
              "condition", "comment"]

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        is_to_user = request.GET.get('to_user') == 'true'

        report = Report.get_or_create_by_device(self.object, is_to_user)

        # генерируем файл в памяти
        report_buffer = generate_report(
            prepare_device_to_report(
                device=self.object,
                report_number=report.id,
                template_file=self.object.company.report_file_to
                if is_to_user else self.object.company.report_file_from),
            CellsToFill(
                device_name = 'J16',
                device_quantity = 'AS16',
                device_condition = 'BW16',
                serial_number = 'BE16',
                employee_name = 'AQ25' if is_to_user else 'AO22',
                report_number = 'O6',
                day = 'BH6',
                month = 'BP6',
                year = 'CG6',
            )
        )

        filename = slugify(
            f"Report_{self.object.company.name}_{self.object.serial_number}")
        safe_filename = f"{filename}.xlsx"

        response = HttpResponse(
            report_buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response[
            'Content-Disposition'] = f'attachment; filename="{safe_filename}"'
        response[
            'Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{safe_filename}'

        return response
