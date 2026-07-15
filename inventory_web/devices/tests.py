import json
import shutil
import tempfile
from pathlib import Path

from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from openpyxl import Workbook

from inventory_web.companies.models import Company
from inventory_web.devices.models import Equipment, EquipmentType
from inventory_web.devices.services.citylink_import import CitylinkImportService
from inventory_web.users.models import UserCompany


class CitylinkImportServiceTests(TestCase):
    def test_parse_file_extracts_model_and_serial_numbers(self):
        temp_dir = tempfile.mkdtemp()
        file_path = Path(temp_dir) / "citylink.xls"
        file_path.write_bytes(self._build_workbook_bytes())

        try:
            parsed_rows = CitylinkImportService.parse_file(file_path)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self.assertEqual(len(parsed_rows), 2)
        self.assertEqual(parsed_rows[0].model, "Ноутбук Lenovo Test")
        self.assertEqual(parsed_rows[0].serial_number, "SN-001")
        self.assertEqual(parsed_rows[1].serial_number, "SN-002")

    def test_parse_file_removes_leading_s_for_ipad_serial(self):
        temp_dir = tempfile.mkdtemp()
        file_path = Path(temp_dir) / "citylink.xls"
        file_path.write_bytes(self._build_workbook_bytes(model="Apple iPad Air", serials=("S123456",)))

        try:
            parsed_rows = CitylinkImportService.parse_file(file_path)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self.assertEqual(parsed_rows[0].serial_number, "123456")

    @staticmethod
    def _build_workbook_bytes(model="Ноутбук Lenovo Test", serials=("SN-001", "SN-002")):
        workbook = Workbook()
        sheet = workbook.active
        sheet["B2"] = "Наименование товара (описание выполненных работ, оказанных услуг), имущественного права"
        sheet["F2"] = "Серийные номера"
        row_index = 5
        for serial in serials:
            sheet[f"B{row_index}"] = model
            sheet[f"F{row_index}"] = serial
            row_index += 1
        sheet[f"B{row_index}"] = "Кол-во штук всего"

        import io

        buffer = io.BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()


class BitLockerKeyApiTests(TestCase):
    key = "123456-234567-345678-456789-567890-678901-789012-890123"

    def setUp(self):
        self.company = Company.objects.create(name="API Company", api_key="company-api-key")
        self.other_company = Company.objects.create(name="Other API Company", api_key="other-api-key")
        self.equipment_type = EquipmentType.objects.create(name="Ноутбук")
        self.url = "/api/bitlocker-keys"

    def post(self, payload, api_key="company-api-key"):
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_API_KEY=api_key,
        )

    def test_creates_device_and_extracts_key_from_text_without_notifications(self):
        response = self.post(
            {
                "serial_number": "SN-NEW",
                "text": f"Recovery password for this device: {self.key}. Keep it safe.",
            }
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["created"], True)
        device = Equipment.objects.get(serial_number="SN-NEW")
        self.assertEqual(device.company, self.company)
        self.assertEqual(device.equipment_type.name, "Ноутбук")
        self.assertEqual(device.model, "Не определено")
        self.assertEqual(device.bitlocker_recovery_key, self.key)
        self.assertEqual(len(mail.outbox), 0)

    def test_updates_existing_device_with_direct_key(self):
        device = Equipment.objects.create(
            company=self.company,
            equipment_type=self.equipment_type,
            model="ThinkPad",
            serial_number="SN-EXISTING",
        )

        response = self.post({"serial_number": device.serial_number, "bitlocker_key": self.key})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["created"], False)
        device.refresh_from_db()
        self.assertEqual(device.bitlocker_recovery_key, self.key)

    def test_rejects_invalid_requests_and_other_company_serial(self):
        response = self.post({"serial_number": "SN-INVALID", "text": "No recovery password here"})
        self.assertEqual(response.status_code, 422)

        response = self.post({"serial_number": "SN-BOTH", "text": self.key, "bitlocker_key": self.key})
        self.assertEqual(response.status_code, 400)

        response = self.post({"serial_number": "SN-UNAUTH", "bitlocker_key": self.key}, api_key="invalid")
        self.assertEqual(response.status_code, 401)

        device = Equipment.objects.create(
            company=self.other_company,
            equipment_type=self.equipment_type,
            model="Other laptop",
            serial_number="SN-OTHER",
        )
        response = self.post({"serial_number": device.serial_number, "bitlocker_key": self.key})
        self.assertEqual(response.status_code, 409)
        device.refresh_from_db()
        self.assertEqual(device.bitlocker_recovery_key, "")

    def test_only_post_is_allowed(self):
        response = self.client.get(self.url, HTTP_X_API_KEY="company-api-key")

        self.assertEqual(response.status_code, 405)


class EquipmentNotificationDefaultsViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass12345")
        self.company = Company.objects.create(
            name="Test Company",
            equipment_email_to="equipment@example.com",
            equipment_email_cc="accounting@example.com",
        )
        self.equipment_type = EquipmentType.objects.create(name="Ноутбук")
        self.device = Equipment.objects.create(
            company=self.company,
            equipment_type=self.equipment_type,
            model="Test laptop",
            serial_number="SN-001",
        )
        UserCompany.objects.create(user=self.user, company=self.company)
        self.client.force_login(self.user)

    def test_create_and_update_forms_use_notification_defaults(self):
        for url in (
            reverse("devices:equipment_create"),
            reverse("devices:equipment_update", args=[self.device.pk]),
        ):
            response = self.client.get(url)

            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"]["send_email"].value())
            self.assertEqual(response.context["form"]["email_to"].value(), "equipment@example.com")
            self.assertEqual(response.context["form"]["email_cc"].value(), "accounting@example.com")

    def test_notification_recipients_are_available_for_company_selection(self):
        response = self.client.get(
            reverse("devices:equipment_notification_recipients"),
            {"company_id": self.company.pk},
        )

        self.assertEqual(response.json(), {"email_to": "equipment@example.com", "email_cc": "accounting@example.com"})


class EquipmentListViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass12345")
        company = Company.objects.create(name="Test Company")
        equipment_type = EquipmentType.objects.create(name="Ноутбук")
        UserCompany.objects.create(user=self.user, company=company)
        Equipment.objects.bulk_create(
            [
                Equipment(
                    company=company,
                    equipment_type=equipment_type,
                    model=f"Test laptop {index}",
                    serial_number=f"SN-{index:03}",
                )
                for index in range(55)
            ]
        )
        self.client.force_login(self.user)

    def test_list_is_paginated_with_default_page_size(self):
        response = self.client.get(reverse("devices:equipment_list"))

        self.assertEqual(len(response.context["equipment_items"]), 50)
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(response.context["selected_per_page"], 50)

    def test_list_accepts_allowed_page_size_and_preserves_filters(self):
        response = self.client.get(
            reverse("devices:equipment_list"),
            {"per_page": 100, "model": "Test laptop"},
        )

        self.assertEqual(len(response.context["equipment_items"]), 55)
        self.assertEqual(response.context["selected_per_page"], 100)
        self.assertIn("per_page=100", response.context["pagination_query"])
        self.assertIn("model=Test+laptop", response.context["pagination_query"])

    def test_list_uses_default_page_size_for_unknown_value(self):
        response = self.client.get(reverse("devices:equipment_list"), {"per_page": 10})

        self.assertEqual(len(response.context["equipment_items"]), 50)
        self.assertEqual(response.context["selected_per_page"], 50)


class EquipmentCitylinkImportViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temp_media_dir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_media_dir, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass12345")
        self.company = Company.objects.create(name="Test Company")
        self.laptop_type = EquipmentType.objects.create(name="Ноутбук")
        self.tablet_type = EquipmentType.objects.create(name="Планшет")
        UserCompany.objects.create(user=self.user, company=self.company)
        self.client.force_login(self.user)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="noreply@example.com",
    )
    def test_import_preview_and_confirm_create_selected_equipment_and_send_email(self):
        with self.settings(MEDIA_ROOT=self.temp_media_dir):
            upload_response = self.client.post(
                reverse("devices:equipment_import_citylink"),
                data={
                    "action": "upload",
                    "company": self.company.pk,
                    "email_to": "user@example.com",
                    "email_cc": "copy@example.com",
                    "file": self._build_upload(),
                },
            )

            self.assertEqual(upload_response.status_code, 200)
            self.assertContains(upload_response, "SN-001")
            self.assertContains(upload_response, "SN-002")

            preview_rows = upload_response.context["preview_rows"]
            self.assertEqual(len(preview_rows), 2)
            first_row = preview_rows[0]
            self.assertEqual(first_row["suggested_equipment_type_name"], "Ноутбук")
            self.assertTrue(first_row["row_id"] in upload_response.context["selected_serials"])

            confirm_response = self.client.post(
                reverse("devices:equipment_import_citylink"),
                data={
                    "action": "confirm",
                    "company": self.company.pk,
                    "email_to": "user@example.com",
                    "email_cc": "copy@example.com",
                    "temp_file_path": upload_response.context["temp_file_path"],
                    "original_filename": upload_response.context["original_filename"],
                    "selected_rows": [first_row["row_id"]],
                    f"equipment_type_{first_row['row_id']}": str(self.laptop_type.id),
                },
                follow=True,
            )

            self.assertRedirects(confirm_response, reverse("devices:equipment_list"))
            self.assertTrue(Equipment.objects.filter(serial_number="SN-001", company=self.company).exists())
            self.assertFalse(Equipment.objects.filter(serial_number="SN-002").exists())

            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, "Серийные номера citylink_test")
            self.assertEqual(mail.outbox[0].body.strip(), "Во вложении серийные номера с закупки citylink_test")
            self.assertEqual(mail.outbox[0].to, ["user@example.com"])
            self.assertEqual(mail.outbox[0].cc, ["copy@example.com"])
            self.assertEqual(mail.outbox[0].attachments[0][0], "citylink_test.xls")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="noreply@example.com",
    )
    def test_row_without_detected_type_is_unchecked_by_default(self):
        with self.settings(MEDIA_ROOT=self.temp_media_dir):
            upload_response = self.client.post(
                reverse("devices:equipment_import_citylink"),
                data={
                    "action": "upload",
                    "company": self.company.pk,
                    "email_to": "",
                    "email_cc": "",
                    "file": self._build_upload(
                        filename="unknown_test.xls",
                        model="Устройство Без Совпадения",
                        serials=("SN-777",),
                    ),
                },
            )

            preview_rows = upload_response.context["preview_rows"]
            self.assertEqual(preview_rows[0]["suggested_equipment_type_id"], "")
            self.assertFalse(preview_rows[0]["row_id"] in upload_response.context["selected_serials"])

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="noreply@example.com",
    )
    def test_edited_serial_number_is_saved_to_db(self):
        with self.settings(MEDIA_ROOT=self.temp_media_dir):
            upload_response = self.client.post(
                reverse("devices:equipment_import_citylink"),
                data={
                    "action": "upload",
                    "company": self.company.pk,
                    "email_to": "",
                    "email_cc": "",
                    "file": self._build_upload(),
                },
            )

            first_row = upload_response.context["preview_rows"][0]
            confirm_response = self.client.post(
                reverse("devices:equipment_import_citylink"),
                data={
                    "action": "confirm",
                    "company": self.company.pk,
                    "email_to": "",
                    "email_cc": "",
                    "temp_file_path": upload_response.context["temp_file_path"],
                    "original_filename": upload_response.context["original_filename"],
                    "selected_rows": [first_row["row_id"]],
                    f"equipment_type_{first_row['row_id']}": str(self.laptop_type.id),
                    f"serial_number_{first_row['row_id']}": "SN-999",
                },
                follow=True,
            )

            self.assertRedirects(confirm_response, reverse("devices:equipment_list"))
            self.assertTrue(Equipment.objects.filter(serial_number="SN-999", company=self.company).exists())
            self.assertFalse(Equipment.objects.filter(serial_number="SN-001", company=self.company).exists())

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="noreply@example.com",
    )
    def test_existing_serial_is_not_imported_twice(self):
        Equipment.objects.create(
            company=self.company,
            equipment_type=self.laptop_type,
            model="Уже в базе",
            serial_number="SN-001",
        )

        with self.settings(MEDIA_ROOT=self.temp_media_dir):
            upload_response = self.client.post(
                reverse("devices:equipment_import_citylink"),
                data={
                    "action": "upload",
                    "company": self.company.pk,
                    "email_to": "",
                    "email_cc": "",
                    "file": self._build_upload(),
                },
            )

            preview_rows = upload_response.context["preview_rows"]
            duplicate_row = next(row for row in preview_rows if row["serial_number"] == "SN-001")
            self.assertTrue(duplicate_row["exists_in_db"])
            self.assertFalse(duplicate_row["selectable"])

            confirm_response = self.client.post(
                reverse("devices:equipment_import_citylink"),
                data={
                    "action": "confirm",
                    "company": self.company.pk,
                    "email_to": "",
                    "email_cc": "",
                    "temp_file_path": upload_response.context["temp_file_path"],
                    "original_filename": upload_response.context["original_filename"],
                    "selected_rows": [preview_rows[0]["row_id"], preview_rows[1]["row_id"]],
                    f"equipment_type_{preview_rows[0]['row_id']}": str(self.laptop_type.id),
                    f"equipment_type_{preview_rows[1]['row_id']}": str(self.laptop_type.id),
                },
                follow=True,
            )

            self.assertRedirects(confirm_response, reverse("devices:equipment_list"))
            self.assertEqual(Equipment.objects.filter(serial_number="SN-001").count(), 1)
            self.assertTrue(Equipment.objects.filter(serial_number="SN-002").exists())
            self.assertEqual(len(mail.outbox), 0)

    def _build_upload(self, filename="citylink_test.xls", model="Ноутбук Lenovo Test", serials=("SN-001", "SN-002")):
        return SimpleUploadedFile(
            filename,
            CitylinkImportServiceTests._build_workbook_bytes(model=model, serials=serials),
            content_type="application/vnd.ms-excel",
        )
