# Generated by Django 5.0.6 on 2024-06-14 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chatsnipserver", "0007_alter_chat_json_data_alter_chat_markdown"),
    ]

    operations = [
        migrations.AddField(
            model_name="chat",
            name="images_downloaded",
            field=models.BooleanField(default=False),
        ),
    ]
