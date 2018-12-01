# Generated by Django 2.1.3 on 2018-11-30 14:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agentex', '0007_auto_20181127_1649'),
    ]

    operations = [
        migrations.AlterField(
            model_name='badge',
            name='image',
            field=models.CharField(choices=[('badge/badge_measurement_250.png', 'badge_measurement_250.png'), ('badge/badge_calibrators_15.png', 'badge_calibrators_15.png'), ('badge/badge_measurement_1000.png', 'badge_measurement_1000.png'), ('badge/badge_manual.png', 'badge_manual.png'), ('badge/badge_top_measurer.png', 'badge_top_measurer.png'), ('badge/badge_calibrators_10.png', 'badge_calibrators_10.png'), ('badge/badge_measurement_50.png', 'badge_measurement_50.png'), ('badge/badge_completed_1.png', 'badge_completed_1.png'), ('badge/badge_completed_2.png', 'badge_completed_2.png'), ('badge/badge_calibrators_3.png', 'badge_calibrators_3.png'), ('badge/badge_completed_3.png', 'badge_completed_3.png'), ('badge/badge_measurement_1500.png', 'badge_measurement_1500.png'), ('badge/badge_measurement_25.png', 'badge_measurement_25.png'), ('badge/badge_calibrators_5.png', 'badge_calibrators_5.png'), ('badge/badge_completed_4.png', 'badge_completed_4.png'), ('badge/badge_completed_5.png', 'badge_completed_5.png'), ('badge/badges.svg', 'badges.svg'), ('badge/badge_measurement_2000.png', 'badge_measurement_2000.png'), ('badge/badge_measurement_10.png', 'badge_measurement_10.png'), ('badge/badge_lightcurve_1star.png', 'badge_lightcurve_1star.png'), ('badge/badge_planet_1.png', 'badge_planet_1.png'), ('badge/badge_lightcurve_3star.png', 'badge_lightcurve_3star.png'), ('badge/badge_measurement_500.png', 'badge_measurement_500.png'), ('badge/badge_measurement_1.png', 'badge_measurement_1.png'), ('badge/badge_planet_3.png', 'badge_planet_3.png'), ('badge/badge_planet_2.png', 'badge_planet_2.png'), ('badge/badge_planet_6.png', 'badge_planet_6.png'), ('badge/badge_measurement_100.png', 'badge_measurement_100.png'), ('badge/badge_planet_7.png', 'badge_planet_7.png'), ('badge/badge_measurement_5.png', 'badge_measurement_5.png'), ('badge/badge_planet_5.png', 'badge_planet_5.png'), ('badge/badge_planet_4.png', 'badge_planet_4.png'), ('badge/badge_calibrators_25.png', 'badge_calibrators_25.png'), ('badge/badge_lightcurve_2star.png', 'badge_lightcurve_2star.png')], max_length=100),
        ),
        migrations.AlterField(
            model_name='datasource',
            name='image',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='finderchart',
            field=models.CharField(blank=True, choices=[('finderchart/OGLETR132b-finder.jpg', 'OGLETR132b-finder.jpg'), ('finderchart/corot2b.jpg', 'corot2b.jpg'), ('finderchart/QATAR1b-finder.jpg', 'QATAR1b-finder.jpg'), ('finderchart/Hat-P-25b-finder.jpg', 'Hat-P-25b-finder.jpg'), ('finderchart/Wasp2b-finder.jpg', 'Wasp2b-finder.jpg'), ('finderchart/TrES3b-finder.jpg', 'TrES3b-finder.jpg'), ('finderchart/Hat-P-8b-finder.jpg', 'Hat-P-8b-finder.jpg')], help_text='Image with a clearly marked up target position', max_length=100, verbose_name='Finder chart'),
        ),
        migrations.AlterField(
            model_name='event',
            name='finderchart_tb',
            field=models.CharField(blank=True, choices=[('finderchart/thumb/TrES3b-finder-thumb2.jpg', 'TrES3b-finder-thumb2.jpg'), ('finderchart/thumb/Hat-P-25b-finder-thumb2.jpg', 'Hat-P-25b-finder-thumb2.jpg'), ('finderchart/thumb/corot2b-finder.thumb.jpg', 'corot2b-finder.thumb.jpg'), ('finderchart/thumb/Hat-P-8b-finder-thumb2.jpg', 'Hat-P-8b-finder-thumb2.jpg'), ('finderchart/thumb/Wasp2b-finder-thumb2.jpg', 'Wasp2b-finder-thumb2.jpg'), ('finderchart/thumb/OGLETR132b-finder-thumb2.jpg', 'OGLETR132b-finder-thumb2.jpg'), ('finderchart/thumb/corot2b-finder.thumb.lg.jpg', 'corot2b-finder.thumb.lg.jpg'), ('finderchart/thumb/QATAR1b-finder-thumb2.jpg', 'QATAR1b-finder-thumb2.jpg')], help_text='Image with a clearly marked up target position', max_length=100, verbose_name='Finder chart thumbnail'),
        ),
        migrations.AlterField(
            model_name='event',
            name='illustration',
            field=models.CharField(blank=True, choices=[('illustration/planet_OGLE-TR-132b.jpg', 'planet_OGLE-TR-132b.jpg'), ('illustration/Hat-P-25b-finder-thumb2.jpg', 'Hat-P-25b-finder-thumb2.jpg'), ('illustration/planet_HAT-P-8b.jpg', 'planet_HAT-P-8b.jpg'), ('illustration/planet_HAT-P-11b.jpg', 'planet_HAT-P-11b.jpg'), ('illustration/planet_WASP-2b.jpg', 'planet_WASP-2b.jpg'), ('illustration/planet_HAT-P-25b.jpg', 'planet_HAT-P-25b.jpg'), ('illustration/planet_Qatar-1-b.jpg', 'planet_Qatar-1-b.jpg'), ('illustration/planet_TrES-3-b.jpg', 'planet_TrES-3-b.jpg'), ('illustration/planet_CoRoT-2b.jpg', 'planet_CoRoT-2b.jpg'), ('illustration/planet_GJ1214b.jpg', 'planet_GJ1214b.jpg')], help_text='illustration for this event', max_length=100, verbose_name='illustration'),
        ),
    ]
