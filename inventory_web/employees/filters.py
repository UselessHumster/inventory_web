import django_filters
from inventory_web.companies.models import Company
from .models import Employee

class EmployeeFilter(django_filters.FilterSet):
    company = django_filters.ModelChoiceFilter(queryset=Company.objects.all())

    class Meta:
        model = Employee
        fields = ['company']

    def filter_self_company(self, queryset, name, value):
        if value:
            user = self.request.user
            return queryset.filter(company__usercompany__user=user)
        return queryset
