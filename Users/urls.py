from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('', views.UserCompanyListView.as_view(), name='usercompany_list'),
    path('create/', views.UserCompanyCreateView.as_view(), name='usercompany_create'),
    path('<int:pk>/update/', views.UserCompanyUpdateView.as_view(), name='usercompany_update'),
    path('<int:pk>/delete/', views.UserCompanyDeleteView.as_view(), name='usercompany_delete'),
]
