from Companies.models import Company
from django.contrib.auth.models import User
from django.db import models


class UserCompany(models.Model):
    """Model to link users to companies they have access to."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Компания")

    class Meta:
        verbose_name = "Право доступа к компании"
        verbose_name_plural = "Права доступа к компаниям"
        unique_together = ('user', 'company')

    def __str__(self):
        return f"{self.user.username} - {self.company.name}"
