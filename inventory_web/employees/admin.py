from django.contrib import admin

from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "email", "phone", "city", "status_display")
    search_fields = ("name", "email", "phone", "city", "company__name")
    list_filter = ("company", "is_active", "city")
    autocomplete_fields = ("company",)
