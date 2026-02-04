from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from inventory_web.companies.models import Company
from inventory_web.employees.models import Employee


@login_required
def home_view(request):
    """
    Handles rendering the home page and AJAX requests for employees.
    """
    # Handle AJAX request for employees of a company
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        company_id = request.GET.get("company_id")
        if company_id:
            employees = Employee.objects.filter(company_id=company_id, is_active=True).values("id", "name")
            return JsonResponse(list(employees), safe=False)
        return JsonResponse([], safe=False)

    # Standard page rendering
    user = request.user
    # For regular users, filter based on UserCompany permissions
    if user.is_superuser:
        companies = Company.objects.all()
    else:
        companies = Company.objects.filter(usercompany__user=user)

    context = {
        "user": user,
        "companies_count": companies.count(),
        "companies": companies,
    }
    return render(request, "home.html", context)
