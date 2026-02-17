from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import ModelChoiceField
from django.shortcuts import HttpResponse, redirect
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from inventory_web.companies.models import Company
from inventory_web.devices.models import Equipment, Report
from inventory_web.devices.utils import gen_report_file, \
    format_device_creation_txt
from inventory_web.employees.models import Employee
from inventory_web.telegram import send_device_creation_to_tg
from inventory_web.devices.filters import EquipmentFilter
from inventory_web.devices.forms import EquipmentCreateForm
from inventory_web import send_email


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = EquipmentFilter(
            self.request.GET,
            queryset=self.get_queryset()
        )
        context['filtered_equipment'] = context['filter'].qs  # для пагинации
        return context





class EquipmentCreateView(LoginRequiredMixin, EquipmentCompanyEmployeeFilterMixin, CreateView):
    model = Equipment
    form_class = EquipmentCreateForm
    template_name = "devices/equipment_form.html"
    success_url = reverse_lazy("devices:equipment_list")

    def form_valid(self, form):
        device = form.save()

        company = device.company
        msg_to_send = format_device_creation_txt(device)
        if company.telegram_chat_id:
            send_device_creation_to_tg(
                msg=msg_to_send,
                chat_id=company.telegram_chat_id
            )

        if form.cleaned_data.get("send_email"):
            recipients = self._parse_emails(form.cleaned_data.get("email_to"))
            copies = self._parse_emails(form.cleaned_data.get("email_cc"))

            html_message = self._build_email_text(device)

            report_file = None
            if form.cleaned_data.get("send_act"):
                if device.company.report_file_to:
                    report = Report.get_or_create_by_device(device,
                                                            to_user=True)
                    report_file = [
                        (
                            f"{device.serial_number}_{device.employee}.xlsx",
                            gen_report_file(report=report,
                                            device=device).getvalue(),
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    ]



            send_email(
                msg=html_message,
                topic=f"Выдача оборудования - {device.employee}",
                recipient=recipients,
                copy_to=copies,
                attachments=report_file
            )

        messages.success(
            self.request,
            f'Оборудование "{device.model}" создано успешно!'
        )

        return redirect(self.success_url)

    def _parse_emails(self, raw_string):
        if not raw_string:
            return []
        return [email.strip() for email in raw_string.split(",")]

    def _build_email_text(self, device):
        return format_device_creation_txt(device, to_mail=True)


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

        report_file = gen_report_file(report=report, device=self.object)

        filename = slugify(
            f"Report_{self.object.company.name}_{self.object.serial_number}")
        safe_filename = f"{filename}.xlsx"

        response = HttpResponse(
            report_file.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response[
            'Content-Disposition'] = f'attachment; filename="{safe_filename}"'
        response[
            'Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{safe_filename}'

        return response
