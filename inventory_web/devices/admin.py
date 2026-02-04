from django.contrib import admin

from .models import Equipment, EquipmentType


@admin.register(EquipmentType)
class EquipmentTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "company",
        "employee",
        "condition",
        "created_at",
    )
    search_fields = (
        "model",
        "serial_number",
        "employee__name",
        "company__name",
    )
    list_filter = ("company", "equipment_type", "condition", "created_at")
    autocomplete_fields = ("company", "employee", "equipment_type")
