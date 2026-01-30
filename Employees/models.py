from Companies.models import Company
from django.db import models


class Employee(models.Model):
    """Model representing an employee."""

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, verbose_name="Компания"
    )
    name = models.CharField(max_length=255, verbose_name="Имя")
    email = models.EmailField(blank=True, verbose_name="Почта")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Номер телефона")
    city = models.CharField(max_length=100, blank=True, verbose_name="Город")
    is_active = models.BooleanField(default=True, verbose_name="Статус")

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def status_display(self):
        return "Работает" if self.is_active else "Уволенный"
