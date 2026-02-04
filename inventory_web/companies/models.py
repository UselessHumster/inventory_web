from django.db import models


class Company(models.Model):
    """Model representing a company."""

    name = models.CharField(max_length=255, unique=True, verbose_name="Название компании")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компании"
        ordering = ["name"]

    def __str__(self):
        return self.name
