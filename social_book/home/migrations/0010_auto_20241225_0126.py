# Generated by Django 3.2.6 on 2024-12-24 19:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0009_auto_20241225_0019'),
    ]

    operations = [
        migrations.RenameField(
            model_name='review',
            old_name='book',
            new_name='book_id',
        ),
        migrations.RenameField(
            model_name='review',
            old_name='user',
            new_name='user_id',
        ),
    ]