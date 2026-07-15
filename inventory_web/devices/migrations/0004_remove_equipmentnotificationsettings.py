from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("devices", "0003_equipmentnotificationsettings")]

    operations = [migrations.DeleteModel(name="EquipmentNotificationSettings")]
