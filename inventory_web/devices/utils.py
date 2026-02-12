from inventory_web.reprtsgen import DeviceToReport
from inventory_web.settings import MEDIA_ROOT

from .models import Equipment


def prepare_device_to_report(device: Equipment, report_number, template_file):
    return DeviceToReport(
        template_path=f'{MEDIA_ROOT}/{template_file}',
        device_name = device.model,
        serial_number = device.serial_number,
        condition = device.get_condition_display(),
        employee_name = device.employee.name,
        report_number=report_number,
    )
