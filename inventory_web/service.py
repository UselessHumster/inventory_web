from typing import List, Tuple
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

from .utils import normalize_emails, EmailRecipients


class EmailService:

    def send_email(
        self,
        msg: str,
        subject: str,
        recipient: EmailRecipients,
        copy_to: EmailRecipients = None,
        attachments: List[Tuple[str, bytes, str]] = None,
    ) -> None:
        """
        attachments:
            List of tuples:
            (filename, file_content_bytes, mime_type)
        """

        recipients = normalize_emails(recipient)
        copies = normalize_emails(copy_to)

        email = EmailMultiAlternatives(
            subject=subject,
            body=self._strip_html(msg),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
            cc=copies,
        )

        # HTML версия
        email.attach_alternative(msg, "text/html")

        # Вложения
        if attachments:
            for filename, content, mime_type in attachments:
                email.attach(filename, content, mime_type)

        email.send(fail_silently=False)

    def _strip_html(self, html: str) -> str:
        """
        Минимальный fallback.
        В production лучше использовать html2text.
        """
        import re
        clean = re.compile("<.*?>")
        return re.sub(clean, "", html)