from django.core.management.base import BaseCommand
from inventory_web.management.commands.utils import (
    Devices,
    latin_to_cyrillic,
    load_data_from_json,
)


from inventory_web.employees.models import Employee
from inventory_web.companies.models import Company
from inventory_web.devices.models import Equipment, EquipmentType


phone = 'phone'
ipad = 'ipad'
laptop = 'laptop'
doc = 'doc'
monitor = 'monitor'
pc = 'pc'
phone_set = 'phone_set'
camera = 'camera'
projector = 'projector'
unknown = 'unknown'

NORM_TYPES = {
    phone: 'Смартфон',
    ipad: 'Планшет',
    laptop: 'Ноутбук',
    monitor: 'Монитор',
    pc: 'Стационарный компьютер',
    projector: 'Проектор',
}

USELESS_TYPES = [doc, phone_set, camera, unknown]

def normalize_name(name):
    norm_name = latin_to_cyrillic(name)
    norm_name.title()
    return " ".join(reversed(norm_name.split(' ')))

class Command(BaseCommand):
    help = "Import equipment from JSON"

    def add_arguments(self, parser):
        parser.add_argument("company_name", type=str)
        parser.add_argument("file_path", type=str)

    def handle(self, *args, **options):
        try:
            load_data_from_json(options["file_path"])
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Ошибка при загрузке данных: {e}'))
            return

        company = Company.objects.filter(name=options["company_name"]).first()

        if not company:
            self.stdout.write(self.style.ERROR(f'Компании "{options["company_name"]}" не существует!'))
            return

        created_employees = 0
        created_types = 0
        created_equipment = 0

        for device in Devices.objects.all():

            if not device.serial_number:
                continue

            if device.type in USELESS_TYPES or not device.type:
                continue

            if not device.model:
                device.model = '-'

            device.type = NORM_TYPES[device.type]

            # --- Employee ---
            employee_name = normalize_name(device.owner)

            employee, created = Employee.objects.get_or_create(
                name=employee_name,
                company=company,
                defaults={"is_active": True},
            )

            if created:
                created_employees += 1

            # --- EquipmentType ---
            equipment_type, created = EquipmentType.objects.get_or_create(
                name=device.type
            )
            if created:
                created_types += 1
            # --- Equipment ---
            if not Equipment.objects.filter(
                    serial_number=device.serial_number).exists():
                Equipment.objects.create(
                    company=company,
                    employee=employee,
                    equipment_type=equipment_type,
                    model=device.model.title(),
                    serial_number=device.serial_number.upper(),
                    condition=Equipment.Condition.NEW,
                )
                created_equipment += 1
        self.stdout.write(self.style.SUCCESS(
            f"Импорт завершён:\n"
            f"Сотрудников создано: {created_employees}\n"
            f"Типов оборудования создано: {created_types}\n"
            f"Оборудования создано: {created_equipment}"
        ))