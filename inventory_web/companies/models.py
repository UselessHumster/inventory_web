from django.db import models

from inventory_web.settings import REPORTS_URL


class Company(models.Model):
    """Model representing a company."""

    name = models.CharField(max_length=255, unique=True, verbose_name="Название компании")
    telegram_chat_id = models.CharField(max_length=255, default=None,verbose_name='ID Telegram чата', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    report_file_to = models.FileField(upload_to=REPORTS_URL, default=None, null=True, blank=True, verbose_name='Акт выдача')
    report_file_from = models.FileField(upload_to=REPORTS_URL, default=None, null=True, blank=True, verbose_name='Акт прием')

    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компании"
        ordering = ["name"]

    def __str__(self):
        return self.name
