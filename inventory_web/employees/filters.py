import django_filters
from inventory_web.companies.models import Company
from .models import Employee

class EmployeeFilter(django_filters.FilterSet):
    company = django_filters.ModelChoiceFilter(queryset=Company.objects.all())
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Employee
        fields = ['company', 'name']

    def filter_self_company(self, queryset, name, value):
        if value:
            user = self.request.user
            return queryset.filter(company__usercompany__user=user)
        return queryset
