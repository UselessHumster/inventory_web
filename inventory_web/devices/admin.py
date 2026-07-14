from django.contrib import admin

from .models import Equipment, EquipmentNotificationSettings, EquipmentType


@admin.register(EquipmentType)
class EquipmentTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(EquipmentNotificationSettings)
class EquipmentNotificationSettingsAdmin(admin.ModelAdmin):
    fields = ("email_to", "email_cc")

    def has_add_permission(self, request):
        return not EquipmentNotificationSettings.objects.exists()


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
