from inventory_web.devices.models import Report
from inventory_web.devices.utils import (
    gen_report_file,
    format_device_creation_txt
)
from inventory_web.telegram import send_device_creation_to_tg
from inventory_web import send_email

class EquipmentNotificationService:

    @staticmethod
    def notify_about_device(device, form):
        company = device.company

        # Telegram
        msg_to_send = format_device_creation_txt(device)
        if company.telegram_chat_id:
            send_device_creation_to_tg(
                msg=msg_to_send,
                chat_id=company.telegram_chat_id
            )

        # Email
        if form.cleaned_data.get("send_email"):
            recipients = EquipmentNotificationService._parse_emails(
                form.cleaned_data.get("email_to")
            )
            copies = EquipmentNotificationService._parse_emails(
                form.cleaned_data.get("email_cc")
            )

            html_message = format_device_creation_txt(device, to_mail=True)

            report_file = None
            if form.cleaned_data.get("send_act"):
                if device.company.report_file_to:
                    report = Report.get_or_create_by_device(
                        device,
                        to_user=True
                    )
                    report_file = [
                        (
                            f"{device.serial_number}_{device.employee}.xlsx",
                            gen_report_file(report=report, device=device).getvalue(),
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

    @staticmethod
    def _parse_emails(raw_string):
        if not raw_string:
            return []
        return [email.strip() for email in raw_string.split(",")]