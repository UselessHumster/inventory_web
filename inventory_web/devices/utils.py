from inventory_web.reprtsgen import DeviceToReport
from .models import Equipment
from inventory_web.settings import MEDIA_ROOT

def prepare_device_to_report(device: Equipment):
    return DeviceToReport(
        template_path=f'{MEDIA_ROOT}/{device.company.report_file}',
        device_name = device.model,
        serial_number = device.serial_number,
        condition = device.get_condition_display(),
        employee_name = device.employee.name,
    )
