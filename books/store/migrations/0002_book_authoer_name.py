# Generated by Django 4.0.6 on 2022-08-01 19:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='authoer_name',
            field=models.CharField(default='auther', max_length=255),
            preserve_default=False,
        ),
    ]