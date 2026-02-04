from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from inventory_web.devices.models import EquipmentType


# EquipmentType Views
class EquipmentTypeListView(LoginRequiredMixin, ListView):
    model = EquipmentType
    template_name = "devices/equipmenttype_list.html"
    context_object_name = "equipment_types"


class EquipmentTypeCreateView(LoginRequiredMixin, CreateView):
    model = EquipmentType
    template_name = "devices/equipmenttype_form.html"
    fields = ["name"]
    success_url = reverse_lazy("devices:equipmenttype_list")


class EquipmentTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = EquipmentType
    template_name = "devices/equipmenttype_form.html"
    fields = ["name"]
    success_url = reverse_lazy("devices:equipmenttype_list")


class EquipmentTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = EquipmentType
    template_name = "devices/equipmenttype_confirm_delete.html"
    success_url = reverse_lazy("devices:equipmenttype_list")
