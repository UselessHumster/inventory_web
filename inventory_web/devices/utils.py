from inventory_web.reprtsgen import CellsToFill, DeviceToReport, generate_report
from inventory_web.settings import MEDIA_ROOT

from .models import Equipment

device_desc_template = (
    "Обновление инвентаря\n"
    "Сотрудник: {employee_name}\n"
    "Тип оборудования: {device_type}\n"
    "Модель устройства: {device_model}\n"
    "Серийный номер: {serial_number}{comment_block}\n"
)

device_desc_html_template = (
    "Сотрудник: <b>{employee_name}</b><br>"
    "Тип оборудования: {device_type}<br>"
    "Модель устройства: {device_model}<br>"
    "Серийный номер: <b>{serial_number}</b>{comment_block}"
)


def prepare_device_to_report(device: Equipment, report_number, template_file):
    return DeviceToReport(
        template_path=f"{MEDIA_ROOT}/{template_file}",
        device_name=device.model,
        serial_number=device.serial_number,
        condition=device.get_condition_display(),
        employee_name=device.employee.name,
        report_number=report_number,
    )


def format_device_creation_txt(device: Equipment, to_mail: bool = False, include_comment: bool = False):
    template = device_desc_html_template if to_mail else device_desc_template
    comment_block = ""

    if include_comment and device.comment:
        comment_block = f"<br>Комментарий: {device.comment}" if to_mail else f"\nКомментарий: {device.comment}"

    return template.format(
        employee_name=device.employee.name if device.employee else "-",
        device_type=device.equipment_type,
        device_model=device.model,
        serial_number=device.serial_number,
        comment_block=comment_block,
    )


def gen_report_file(report, device: Equipment, is_to_user: bool = True):
    return generate_report(
        prepare_device_to_report(
            device=device,
            report_number=report.id,
            template_file=device.company.report_file_to if is_to_user else device.company.report_file_from,
        ),
        CellsToFill(
            device_name="J16",
            device_quantity="AS16",
            device_condition="BW16",
            serial_number="BE16",
            employee_name="AQ25" if is_to_user else "AO22",
            report_number="O6",
            day="BH6",
            month="BP6",
            year="CG6",
        ),
    )
