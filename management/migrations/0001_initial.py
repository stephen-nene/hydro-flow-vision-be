# Generated by Django 5.2 on 2025-04-09 20:24

import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WaterGuideline',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('body', models.CharField(max_length=255)),
                ('usage', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CustomerRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('water_source', models.CharField(max_length=255)),
                ('daily_water_requirement', models.PositiveIntegerField()),
                ('daily_flow_rate', models.PositiveIntegerField()),
                ('water_usage', models.CharField(max_length=255)),
                ('site_location', models.JSONField(default=dict, max_length=255)),
                ('extras', models.JSONField(default=dict)),
                ('budjet', models.JSONField(default=dict)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], max_length=255)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('handlers', models.ManyToManyField(blank=True, related_name='staffs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='WaterGuidelineParameter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('unit', models.CharField(max_length=50)),
                ('min_value', models.FloatField(blank=True, null=True)),
                ('max_value', models.FloatField(blank=True, null=True)),
                ('guideline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parameters', to='management.waterguideline')),
            ],
        ),
        migrations.CreateModel(
            name='WaterLabReport',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('report_source', models.CharField(choices=[('Internal', 'Internal'), ('External', 'External')], help_text='Origin of the water lab report (internal/external).', max_length=50)),
                ('test_type', models.CharField(choices=[('General', 'General'), ('Chemical', 'Chemical'), ('Bacteriological', 'Bacteriological')], help_text='The type of water test conducted (e.g., Chemical, Bacteriological).', max_length=50)),
                ('customer_request', models.ForeignKey(help_text='Associated customer request that initiated the lab report.', on_delete=django.db.models.deletion.CASCADE, related_name='water_lab_reports', to='management.customerrequest')),
            ],
            options={
                'verbose_name': 'Water Lab Report',
                'verbose_name_plural': 'Water Lab Reports',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WaterLabParameter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Parameter name, e.g., pH, Iron, TDS.', max_length=100)),
                ('unit', models.CharField(help_text='Measurement unit, e.g., mg/L, NTU.', max_length=50)),
                ('value', models.FloatField(help_text='Measured value of the parameter.')),
                ('lab_report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='parameters', to='management.waterlabreport')),
            ],
            options={
                'verbose_name': 'Water Lab Parameter',
                'verbose_name_plural': 'Water Lab Parameters',
            },
        ),
        migrations.CreateModel(
            name='ManagementAttachment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('object_id', models.UUIDField()),
                ('file', models.FileField(upload_to='management_attachments/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'dcm'])])),
                ('document_type', models.CharField(choices=[('Water Treatment Plan', 'Water Treatment Plan'), ('Water Quality Report', 'Water Quality Report'), ('Water Quality Monitoring', 'Water Quality Monitoring'), ('Water Quality Assessment', 'Water Quality Assessment'), ('Water Quality Regulations', 'Water Quality Regulations')], max_length=50)),
                ('caption', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('is_sensitive', models.BooleanField(default=False)),
                ('access_audit', models.JSONField(default=dict)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'verbose_name': 'Management Document',
                'verbose_name_plural': 'Management Documents',
                'indexes': [models.Index(fields=['content_type', 'object_id'], name='management__content_13cbd0_idx')],
            },
        ),
        migrations.CreateModel(
            name='WaterReportAttachment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('file', models.FileField(help_text='Attachment file (PDF, image, document, spreadsheet, etc).', upload_to='water_report_attachments/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'dcm', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'txt'])])),
                ('document_type', models.CharField(choices=[('Water Treatment Plan', 'Water Treatment Plan'), ('Water Quality Report', 'Water Quality Report'), ('Water Quality Monitoring', 'Water Quality Monitoring'), ('Water Quality Assessment', 'Water Quality Assessment'), ('Water Quality Regulations', 'Water Quality Regulations')], help_text='Type of the document attached.', max_length=50)),
                ('caption', models.CharField(blank=True, help_text='Optional caption for the file.', max_length=255, null=True)),
                ('description', models.TextField(blank=True, help_text='Optional description for the file.', null=True)),
                ('is_sensitive', models.BooleanField(default=False, help_text='Indicates if the attachment contains sensitive content.')),
                ('access_audit', models.JSONField(default=dict, help_text='JSON structure tracking access audit information (who accessed and when).')),
                ('water_report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='management.waterlabreport')),
            ],
            options={
                'verbose_name': 'Water Report Attachment',
                'verbose_name_plural': 'Water Report Attachments',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['water_report'], name='management__water_r_82ba16_idx')],
            },
        ),
    ]
