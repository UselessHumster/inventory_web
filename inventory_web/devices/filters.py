import django_filters
from .models import Equipment, EquipmentType

from inventory_web.companies.models import Company
from inventory_web.employees.models import Employee


class EquipmentFilter(django_filters.FilterSet):
    company = django_filters.ModelChoiceFilter(queryset=Company.objects.all())
    employee = django_filters.ModelChoiceFilter(queryset=Employee.objects.all())
    equipment_type = django_filters.ModelChoiceFilter(
        queryset=EquipmentType.objects.all())
    condition = django_filters.ChoiceFilter(choices=Equipment.Condition.choices)
    model = django_filters.CharFilter(lookup_expr='icontains')
    serial_number = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Equipment
        fields = []

    def filter_self_equipment(self, queryset, name, value):
        if value:
            user = self.request.user
            return queryset.filter(company__usercompany__user=user)
        return queryset
