from django.db import migrations, models


# Apply this function to safely migrate the current data about SR status to two new columns of status
def migrate_status_data(apps, schema_editor):
    ScanReport = apps.get_model("mapping", "ScanReport")
    for report in ScanReport.objects.all():
        if report.status in ["UPINPRO", "UPCOMPL", "UPFAILE"]:
            report.upload_status = report.status
            report.mapping_status = "PENDING"
        else:
            report.upload_status = "UPCOMPL"
            report.mapping_status = report.status
        report.save()


class Migration(migrations.Migration):

    dependencies = [
        (
            "mapping",
            "0003_handmade_20220428_1503",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="scanreport",
            name="upload_status",
            field=models.CharField(
                choices=[
                    ("UPINPRO", "Upload in Progress"),
                    ("UPCOMPL", "Upload Complete"),
                    ("UPFAILE", "Upload Failed"),
                ],
                default="UPINPRO",
                max_length=7,
            ),
        ),
        migrations.AddField(
            model_name="scanreport",
            name="mapping_status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Mapping 0%"),
                    ("INPRO25", "Mapping 25%"),
                    ("INPRO50", "Mapping 50%"),
                    ("INPRO75", "Mapping 75%"),
                    ("COMPLET", "Mapping Complete"),
                    ("BLOCKED", "Blocked"),
                ],
                default="PENDING",
                max_length=7,
            ),
        ),
        migrations.RunPython(migrate_status_data),
        migrations.RemoveField(
            model_name="scanreport",
            name="status",
        ),
    ]
