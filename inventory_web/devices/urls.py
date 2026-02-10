from django.urls import path

from . import views

app_name = 'devices'

urlpatterns = [
    # EquipmentType URLs
    path('types/', views.EquipmentTypeListView.as_view(), name='equipmenttype_list'),
    path('types/create/', views.EquipmentTypeCreateView.as_view(), name='equipmenttype_create'),
    path('types/<int:pk>/update/', views.EquipmentTypeUpdateView.as_view(), name='equipmenttype_update'),
    path('types/<int:pk>/delete/', views.EquipmentTypeDeleteView.as_view(), name='equipmenttype_delete'),

    # Equipment URLs
    path('', views.EquipmentListView.as_view(), name='equipment_list'),
    path('create/', views.EquipmentCreateView.as_view(), name='equipment_create'),
    path('<int:pk>/update/', views.EquipmentUpdateView.as_view(), name='equipment_update'),
    path('<int:pk>/delete/', views.EquipmentDeleteView.as_view(), name='equipment_delete'),
    path('<int:pk>/download-report/', views.EquipmentReportDownloadView.as_view(),name='equipment_download_report'),
]
