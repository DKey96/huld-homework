# Generated by Django 4.2.1 on 2023-05-28 14:01

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("file_manager", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="file",
            name="path",
            field=models.FilePathField(max_length=255),
        ),
    ]