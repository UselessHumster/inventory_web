import json
import re

from django.db import transaction
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from inventory_web.companies.models import Company
from inventory_web.devices.models import Equipment, EquipmentType

BITLOCKER_RECOVERY_KEY_PATTERN = re.compile(r"\b\d{6}(?:-\d{6}){7}\b")


@method_decorator(csrf_exempt, name="dispatch")
class BitLockerKeyView(View):
    """Save a BitLocker recovery key for equipment selected by company API key."""

    def post(self, request, *args, **kwargs):
        company = self._get_company(request)
        if not company:
            return self._error("Недействительный API-ключ.", 401)

        try:
            payload = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._error("Тело запроса должно быть корректным JSON.", 400)

        if not isinstance(payload, dict):
            return self._error("Тело запроса должно быть JSON-объектом.", 400)

        serial_number = payload.get("serial_number")
        if not isinstance(serial_number, str) or not (serial_number := serial_number.strip()):
            return self._error("Укажите непустой serial_number.", 400)
        if len(serial_number) > Equipment._meta.get_field("serial_number").max_length:
            return self._error("serial_number слишком длинный.", 400)

        bitlocker_key, error = self._extract_key(payload)
        if error:
            return self._error(error[0], error[1])

        with transaction.atomic():
            equipment = Equipment.objects.select_for_update().filter(serial_number=serial_number).first()
            if equipment and equipment.company_id != company.id:
                return self._error("Серийный номер уже принадлежит другой компании.", 409)

            created = equipment is None
            if created:
                equipment_type, _ = EquipmentType.objects.get_or_create(name="Ноутбук")
                equipment = Equipment.objects.create(
                    company=company,
                    equipment_type=equipment_type,
                    model="Не определено",
                    serial_number=serial_number,
                    bitlocker_recovery_key=bitlocker_key,
                )
            else:
                equipment.bitlocker_recovery_key = bitlocker_key
                equipment.save(update_fields=["bitlocker_recovery_key"])

        return JsonResponse(
            {
                "id": equipment.id,
                "serial_number": equipment.serial_number,
                "created": created,
            },
            status=201 if created else 200,
        )

    @staticmethod
    def _get_company(request):
        api_key = request.headers.get("X-API-Key", "").strip()
        if not api_key:
            return None
        return Company.objects.filter(api_key=api_key).first()

    @staticmethod
    def _extract_key(payload):
        has_key = "bitlocker_key" in payload
        has_text = "text" in payload
        if has_key == has_text:
            return None, ("Передайте ровно одно из полей bitlocker_key или text.", 400)

        value = payload["bitlocker_key"] if has_key else payload["text"]
        if not isinstance(value, str):
            return None, ("Значение ключа должно быть строкой.", 400)

        match = (
            BITLOCKER_RECOVERY_KEY_PATTERN.fullmatch(value.strip())
            if has_key
            else BITLOCKER_RECOVERY_KEY_PATTERN.search(value)
        )
        if not match:
            return None, ("Не найден корректный ключ восстановления BitLocker.", 422)
        return match.group(0), None

    @staticmethod
    def _error(detail, status):
        return JsonResponse({"detail": detail}, status=status)
