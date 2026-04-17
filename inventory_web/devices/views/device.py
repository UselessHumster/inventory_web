from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import ModelChoiceField
from django.shortcuts import HttpResponse, redirect
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from inventory_web.companies.models import Company
from inventory_web.devices.filters import EquipmentFilter
from inventory_web.devices.forms import CitylinkImportUploadForm, EquipmentCreateForm
from inventory_web.devices.models import Equipment, Report
from inventory_web.devices.services.citylink_import import (
    CitylinkImportError,
    CitylinkImportService,
)
from inventory_web.devices.services.equipment_notifications import EquipmentNotificationService
from inventory_web.devices.utils import format_device_creation_txt, gen_report_file
from inventory_web.employees.models import Employee


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


class EquipmentCitylinkImportView(LoginRequiredMixin, View):
    template_name = "devices/equipment_import.html"
    success_url = reverse_lazy("devices:equipment_list")

    def get(self, request, *args, **kwargs):
        return self._render_upload_form()

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action", "upload")
        if action == "confirm":
            return self._handle_confirm()
        return self._handle_upload()

    def _handle_upload(self):
        form = CitylinkImportUploadForm(self.request.POST, self.request.FILES, user=self.request.user)
        if not form.is_valid():
            return self._render_upload_form(form=form)

        uploaded_file = form.cleaned_data["file"]
        temp_file_path = CitylinkImportService.save_temp_upload(uploaded_file)

        try:
            parsed_rows = CitylinkImportService.parse_file(temp_file_path)
            _, preview_rows = CitylinkImportService.build_preview_from_parsed(parsed_rows)
        except CitylinkImportError as exc:
            CitylinkImportService.cleanup_temp_file(temp_file_path)
            form.add_error("file", str(exc))
            return self._render_upload_form(form=form)

        if not any(row["selectable"] for row in preview_rows):
            CitylinkImportService.cleanup_temp_file(temp_file_path)
            form.add_error("file", "Все серийные номера из файла уже есть в базе или дублируются внутри файла.")
            return self._render_upload_form(form=form)

        return self._render_preview(
            form=form,
            preview_rows=preview_rows,
            temp_file_path=str(temp_file_path),
            original_filename=uploaded_file.name,
        )

    def _handle_confirm(self):
        form = CitylinkImportUploadForm(self.request.POST, user=self.request.user)
        form.fields["file"].required = False
        temp_file_path = self.request.POST.get("temp_file_path", "")
        original_filename = self.request.POST.get("original_filename", "")

        if not temp_file_path:
            messages.error(self.request, "Файл для импорта не найден. Загрузите его повторно.")
            return redirect("devices:equipment_import_citylink")

        try:
            parsed_rows = CitylinkImportService.parse_file(temp_file_path)
        except CitylinkImportError as exc:
            messages.error(self.request, str(exc))
            CitylinkImportService.cleanup_temp_file(temp_file_path)
            return redirect("devices:equipment_import_citylink")

        serial_overrides = self._get_serial_overrides()
        effective_rows, preview_rows = CitylinkImportService.build_preview_from_parsed(
            parsed_rows,
            serial_overrides,
        )
        if not form.is_valid():
            return self._render_preview(
                form=form,
                preview_rows=preview_rows,
                temp_file_path=temp_file_path,
                original_filename=original_filename,
                selected_serials=set(self.request.POST.getlist("selected_rows")),
                selected_type_ids=self._get_selected_type_ids(),
                serial_overrides=serial_overrides,
            )

        selected_serials = {
            row_id.strip()
            for row_id in self.request.POST.getlist("selected_rows")
            if row_id.strip()
        }
        selectable_row_ids = {row["row_id"] for row in preview_rows if row["selectable"]}
        selected_serials &= selectable_row_ids

        if not selected_serials:
            messages.error(self.request, "Выберите хотя бы одно оборудование для загрузки.")
            return self._render_preview(
                form=form,
                preview_rows=preview_rows,
                temp_file_path=temp_file_path,
                original_filename=original_filename,
                selected_serials=selected_serials,
                selected_type_ids=self._get_selected_type_ids(),
                serial_overrides=serial_overrides,
            )

        selected_type_ids = {
            row_id: self.request.POST.get(f"equipment_type_{row_id}", "").strip()
            for row_id in selected_serials
        }
        missing_type_rows = [
            row["row_number"]
            for row in preview_rows
            if row["row_id"] in selected_serials and not selected_type_ids.get(row["row_id"])
        ]
        if missing_type_rows:
            messages.error(
                self.request,
                "Выберите тип оборудования для строк: "
                + ", ".join(str(row_number) for row_number in missing_type_rows),
            )
            return self._render_preview(
                form=form,
                preview_rows=preview_rows,
                temp_file_path=temp_file_path,
                original_filename=original_filename,
                selected_serials=selected_serials,
                selected_type_ids=selected_type_ids,
                serial_overrides=serial_overrides,
            )

        created_devices, skipped_serials = CitylinkImportService.import_selected_rows(
            company=form.cleaned_data["company"],
            parsed_rows=effective_rows,
            selected_row_ids=selected_serials,
            selected_type_ids=selected_type_ids,
        )

        if form.cleaned_data.get("email_to"):
            CitylinkImportService.send_original_file(
                file_path=temp_file_path,
                original_filename=original_filename,
                email_to=form.cleaned_data["email_to"],
                email_cc=form.cleaned_data["email_cc"],
            )

        CitylinkImportService.cleanup_temp_file(temp_file_path)

        if created_devices:
            messages.success(
                self.request,
                f"Загружено оборудования: {len(created_devices)}."
            )
        if skipped_serials:
            messages.warning(
                self.request,
                "Некоторые серийные номера пропущены, потому что уже существуют в базе: "
                + ", ".join(skipped_serials[:10])
                + ("..." if len(skipped_serials) > 10 else "")
            )
        if form.cleaned_data.get("email_to"):
            messages.success(self.request, "Исходный файл отправлен на почту.")

        return redirect(self.success_url)

    def _render_upload_form(self, form=None):
        form = form or CitylinkImportUploadForm(user=self.request.user)
        return self.render_to_response(
            {
                "form": form,
                "step": "upload",
            }
        )

    def _render_preview(
        self,
        *,
        form,
        preview_rows,
        temp_file_path,
        original_filename,
        selected_serials=None,
        selected_type_ids=None,
        serial_overrides=None,
    ):
        selected_serials = selected_serials or {
            row["row_id"]
            for row in preview_rows
            if row["selectable"] and row["suggested_equipment_type_id"]
        }
        selected_type_ids = selected_type_ids or {}
        serial_overrides = serial_overrides or {}
        for row in preview_rows:
            row["selected_equipment_type_id"] = (
                selected_type_ids.get(row["row_id"]) or row["suggested_equipment_type_id"]
            )
            row["edited_serial_number"] = serial_overrides.get(row["row_id"], row["serial_number"])
        return self.render_to_response(
            {
                "form": form,
                "step": "preview",
                "preview_rows": preview_rows,
                "temp_file_path": temp_file_path,
                "original_filename": original_filename,
                "selected_serials": selected_serials,
                "equipment_types": CitylinkImportService.get_equipment_types(),
            }
        )

    def _get_selected_type_ids(self):
        return {
            key.removeprefix("equipment_type_"): value.strip()
            for key, value in self.request.POST.items()
            if key.startswith("equipment_type_")
        }

    def _get_serial_overrides(self):
        return {
            key.removeprefix("serial_number_"): value.strip()
            for key, value in self.request.POST.items()
            if key.startswith("serial_number_")
        }

    def render_to_response(self, context):
        from django.shortcuts import render

        return render(self.request, self.template_name, context)


class EquipmentCreateView(LoginRequiredMixin, EquipmentCompanyEmployeeFilterMixin, CreateView):
    model = Equipment
    form_class = EquipmentCreateForm
    template_name = "devices/equipment_form.html"
    success_url = reverse_lazy("devices:equipment_list")

    def form_valid(self, form):
        device = form.save()

        EquipmentNotificationService.notify_about_device(device, form)

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
    form_class = EquipmentCreateForm
    template_name = "devices/equipment_form.html"
    success_url = reverse_lazy("devices:equipment_list")

    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        equipment = self.get_object()
        return equipment.company in Company.objects.filter(
            usercompany__user=user
        )

    def form_valid(self, form):
        device = form.save()

        EquipmentNotificationService.notify_about_device(device, form)

        messages.success(
            self.request,
            f'Оборудование "{device.model}" обновлено успешно!'
        )

        return redirect(self.success_url)


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
