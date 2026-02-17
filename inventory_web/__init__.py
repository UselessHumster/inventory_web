from .service import EmailService

_service = EmailService()


def send_email(
    msg,
    topic,
    recipient,
    copy_to=None,
    attachments=None,
):
    return _service.send_email(
        msg=msg,
        subject=topic,
        recipient=recipient,
        copy_to=copy_to,
        attachments=attachments,
    )