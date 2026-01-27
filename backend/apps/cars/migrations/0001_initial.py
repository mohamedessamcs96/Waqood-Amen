"""
Initial migrations for cars and vehicles.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Car',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plate', models.CharField(db_index=True, max_length=20, unique=True)),
                ('paid', models.BooleanField(db_index=True, default=False)),
                ('video', models.CharField(blank=True, max_length=255, null=True)),
                ('analysis', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'cars',
            },
        ),
        migrations.CreateModel(
            name='DetectedVehicle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('video_id', models.IntegerField(db_index=True)),
                ('vehicle_index', models.IntegerField(default=0)),
                ('crop_image', models.CharField(blank=True, max_length=255, null=True)),
                ('plate_image', models.CharField(blank=True, max_length=255, null=True)),
                ('plate_text', models.CharField(blank=True, db_index=True, max_length=50, null=True)),
                ('car_color', models.CharField(blank=True, max_length=50, null=True)),
                ('driver_face_image', models.CharField(blank=True, max_length=255, null=True)),
                ('vehicle_confidence', models.FloatField(default=0.0)),
                ('plate_confidence', models.FloatField(blank=True, null=True)),
                ('face_confidence', models.FloatField(blank=True, null=True)),
                ('timestamp', models.BigIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'detected_vehicles',
            },
        ),
        migrations.AddIndex(
            model_name='detectedvehicle',
            index=models.Index(fields=['video_id'], name='detected_v_video_i_idx'),
        ),
        migrations.AddIndex(
            model_name='detectedvehicle',
            index=models.Index(fields=['plate_text'], name='detected_v_plate_t_idx'),
        ),
        migrations.AddIndex(
            model_name='detectedvehicle',
            index=models.Index(fields=['-created_at'], name='detected_v_created_idx'),
        ),
    ]
