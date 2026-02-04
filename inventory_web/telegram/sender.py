from inventory_web.devices.models import Equipment
from .settings import bot, inventory_chat_id


device_desc_template = ('Inventory update\n'
                        'Username: {employee_name}\n'
                        'Device type: {device_type}\n'
                        'Device model: {device_model}\n'
                        'Serial Number: {serial_number}\n')


def send_device_creation(device: Equipment):
    msg = device_desc_template.format(
        employee_name=device.employee.name if device.employee else '-',
        device_type=device.equipment_type,
        device_model=device.model,
        serial_number=device.serial_number
    )
    return bot.send_message(chat_id=inventory_chat_id, text=msg)