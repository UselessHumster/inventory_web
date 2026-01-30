from Companies.models import Company
from django.db import models
from Employees.models import Employee


class EquipmentType(models.Model):
    """Model representing a type of equipment."""

    name = models.CharField(max_length=100, unique=True, verbose_name="Название типа")

    class Meta:
        verbose_name = "Тип оборудования"
        verbose_name_plural = "Типы оборудования"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Equipment(models.Model):
    """Model representing a piece of equipment."""

    class Condition(models.TextChoices):
        NEW = "NEW", "Новое"
        USED = "USED", "БУ"

    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        verbose_name="Компания",
        help_text="Компанию нельзя будет удалить, если за ней числится оборудование.",
    )
    employee = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Сотрудник"
    )
    equipment_type = models.ForeignKey(
        EquipmentType, on_delete=models.PROTECT, verbose_name="Тип оборудования"
    )
    model = models.CharField(max_length=255, verbose_name="Модель устройства")
    serial_number = models.CharField(max_length=255, unique=True, verbose_name="Серийный номер")
    condition = models.CharField(
        max_length=4,
        choices=Condition.choices,
        default=Condition.NEW,
        verbose_name="Состояние",
    )
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        verbose_name = "Оборудование"
        verbose_name_plural = "Оборудование"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.equipment_type} {self.model} ({self.serial_number})"
