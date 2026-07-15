from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("companies", "0007_remove_company_report_file_company_report_file_from_and_more")]

    operations = [
        migrations.AddField(model_name="company", name="equipment_email_to", field=models.CharField(blank=True, max_length=1000, verbose_name="Кому отправлять уведомления об оборудовании")),
        migrations.AddField(model_name="company", name="equipment_email_cc", field=models.CharField(blank=True, max_length=1000, verbose_name="Копия уведомлений об оборудовании")),
    ]
