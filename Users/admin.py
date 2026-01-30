from django.contrib import admin

from .models import UserCompany


@admin.register(UserCompany)
class UserCompanyAdmin(admin.ModelAdmin):
    list_display = ("user", "company")
    search_fields = ("user__username", "company__name")
    autocomplete_fields = ("user", "company")
