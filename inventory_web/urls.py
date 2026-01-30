from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('', RedirectView.as_view(url='home/', permanent=False), name='index'), # Redirect root to home
    path('home/', include('inventory_web.home_urls')),
    path('companies/', include('Companies.urls')),
    path('employees/', include('Employees.urls')),
    path('devices/', include('Devices.urls')),
    path('users/', include('Users.urls')),
]
