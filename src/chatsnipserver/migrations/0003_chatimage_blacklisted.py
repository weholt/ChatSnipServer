# Generated by Django 5.0.6 on 2024-06-12 14:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chatsnipserver", "0002_alter_chat_user_chatimage"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatimage",
            name="blacklisted",
            field=models.BooleanField(default=False),
        ),
    ]
