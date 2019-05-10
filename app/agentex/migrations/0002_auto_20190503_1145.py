# Generated by Django 2.1.7 on 2019-05-03 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agentex', '0001_squashed_0010_auto_20190207_1627'),
    ]

    operations = [

        migrations.AlterField(
            model_name='datasource',
            name='fits',
            field=models.FileField(blank=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='datasource',
            name='image',
            field=models.FileField(blank=True, null=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='event',
            name='description',
            field=models.TextField(),
        ),

    ]