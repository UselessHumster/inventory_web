class DeviceToReport:
    def __init__(
            self, template_path, device_name,
            serial_number, condition, employee_name,
            report_number=1, device_quantity=1):
        self.template_path = template_path
        self.name = device_name
        self.condition = condition
        self.quantity = device_quantity
        self.sn = serial_number
        self.employee_name = employee_name
        self.report_number = report_number


class CellsToFill:
    def __init__(
            self, device_name, device_quantity, device_condition, serial_number,
            employee_name, report_number,
            day, month, year):
        self.device_name = device_name
        self.device_quantity = device_quantity
        self.device_condition = device_condition
        self.sn = serial_number
        self.employee_name = employee_name
        self.report_number = report_number
        self.day = day
        self.month = month
        self.year = year
