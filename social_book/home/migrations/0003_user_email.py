# Generated by Django 3.2.6 on 2024-12-23 17:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_auto_20241223_2229'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email',
            field=models.EmailField(default='default@gmail.com', max_length=255, unique=True),
        ),
    ]
