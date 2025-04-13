from django.db import models
from uuid import uuid4
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils import timezone
from profiles.models import *
from django.contrib.auth.models import User
from django.conf import settings


# Enums 
class DocumentType(models.TextChoices):
    WATER_ANALYSIS_REPORT = 'WAR', 'Water Analysis Report'
    TREATMENT_PLAN = 'TP', 'Treatment Plan'
    COMPLIANCE_CERTIFICATE = 'CC', 'Compliance Certificate'
    LAB_TEST_RESULT = 'LTR', 'Lab Test Result'
    EQUIPMENT_SPEC = 'ES', 'Equipment Specification'
    MAINTENANCE_LOG = 'ML', 'Maintenance Log'
    OPERATIONAL_REPORT = 'OR', 'Operational Report'
    SAFETY_DATA_SHEET = 'SDS', 'Safety Data Sheet'
    PERMIT = 'PER', 'Permit/License'
    CONTRACT = 'CON', 'Contract Agreement'

class TestType(models.TextChoices):
    GENERAL = 'General', 'General'
    # CHEMICAL = 'Chemical', 'Chemical'
    BACTERIOLOGICAL = 'Bacteriological', 'Bacteriological'
    PHYSICAL = 'PHY', 'Physical Characteristics'
    CHEMICAL = 'CHE', 'Chemical Composition'
    MICROBIOLOGICAL = 'MIC', 'Microbiological'
    RADIOLOGICAL = 'RAD', 'Radiological'
    TOXICOLOGICAL = 'TOX', 'Toxicological'
    COMPREHENSIVE = 'COM', 'Comprehensive Analysis'

class ReportSource(models.TextChoices):
        INTERNAL = 'Internal', 'Internal'
        EXTERNAL = 'External', 'External'

class WeekDay(models.IntegerChoices):
    MONDAY = 0, 'Monday'
    TUESDAY = 1, 'Tuesday'
    WEDNESDAY = 2, 'Wednesday'
    THURSDAY = 3, 'Thursday'
    FRIDAY = 4, 'Friday'
    SATURDAY = 5, 'Saturday'
    SUNDAY = 6, 'Sunday'


# Base Models for Code Reusability
class BaseUUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class WaterGuideline(BaseUUIDModel, TimeStampedModel):
    body =models.CharField(max_length=255) # WHO, KEBS, EPA, etc.
    usage = models.CharField(max_length=255)  # e.g. "domestic", "bottling", "industrial"
    description = models.TextField(blank=True, null=True, help_text="Detailed description of the guideline.")
    status =models.CharField(max_length=255,default='pending' , choices=[('pending', 'Pending'),('active', 'Active'), ('inactive', 'Inactive')])
    # physical Analysis
    # pH = models.FloatField()
    # suspended_solids = models.FloatField()
    # salinity = models.FloatField()
    # electrical_conductivity = models.FloatField()
    # turbidity = models.FloatField()
    # total_dissolved_solids = models.FloatField()

    def __str__(self):
        return f"{self.body} - {self.usage}"

    
class WaterGuidelineParameter(models.Model):
    guideline = models.ForeignKey('WaterGuideline', on_delete=models.CASCADE, related_name='parameters')
    name = models.CharField(max_length=100)  # e.g. "pH", "Iron", "TDS"
    unit = models.CharField(max_length=50)   # e.g. "mg/L", "NTU", "μS/cm"
    # value = models.FloatField()
    min_value = models.FloatField(null=True, blank=True)  # e.g. 6.5
    max_value = models.FloatField(null=True, blank=True)  # e.g. 8.5

    def __str__(self):
        return f"{self.name} ({self.guideline.body} - {self.guideline.usage})"


class CustomerRequest(BaseUUIDModel, TimeStampedModel):
    # customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    handlers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='staffs', blank=True)
    water_source = models.CharField(max_length=255)
    daily_water_requirement = models.PositiveIntegerField()
    daily_flow_rate = models.PositiveIntegerField()
    water_usage = models.CharField(max_length=255)
    site_location = models.JSONField(default=dict,max_length=255)
    extras = models.JSONField(default=dict)
    budjet = models.JSONField(default=dict)
    status = models.CharField(max_length=255,choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')])


class WaterLabReport(BaseUUIDModel, TimeStampedModel):
    """
    Stores metadata about a water lab test report.
    """

    customer_request = models.ForeignKey(
        CustomerRequest,
        on_delete=models.CASCADE,
        related_name='water_lab_reports',
        help_text="Associated customer request that initiated the lab report."
    )
    report_source = models.CharField(
        max_length=50,
        choices=ReportSource.choices,
        help_text="Origin of the water lab report (internal/external)."
    )
    report_date = models.DateField(null=True, blank=True)
    test_type = models.CharField(
        max_length=50,
        choices=TestType.choices,
        help_text="The type of water test conducted (e.g., Chemical, Bacteriological)."
    )

    class Meta:
        verbose_name = "Water Lab Report"
        verbose_name_plural = "Water Lab Reports"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_report_source_display()} Report for {self.customer_request} ({self.get_test_type_display()})"


class WaterLabParameter(models.Model):
    """
    Individual parameter result from a water lab report (e.g., pH, Iron).
    """
    lab_report = models.ForeignKey(
        WaterLabReport,
        on_delete=models.CASCADE,
        related_name='parameters'
    )
    name = models.CharField(
        max_length=100,
        help_text="Parameter name, e.g., pH, Iron, TDS."
    )
    unit = models.CharField(
        max_length=50,
        help_text="Measurement unit, e.g., mg/L, NTU."
    )
    value = models.FloatField(
        help_text="Measured value of the parameter."
    )

    # Optional: if this references a guideline object, define that here
    # guideline = models.ForeignKey(...)

    def __str__(self):
        return f"{self.name} - {self.value} {self.unit}"

    class Meta:
        verbose_name = "Water Lab Parameter"
        verbose_name_plural = "Water Lab Parameters"


class WaterReportAttachment(BaseUUIDModel, TimeStampedModel):
    """
    Attachments related to water lab reports, such as supporting documents, images, or external files.
    """
    customer_request = models.ForeignKey(
        CustomerRequest,
        on_delete=models.CASCADE,
        related_name='attachments',
        help_text="Associated customer request that initiated the lab report."
    )
    water_report = models.ForeignKey(
        WaterLabReport,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(
        upload_to="water_report_attachments/",
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'jpg', 'dcm', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'txt']
        )],
        help_text="Attachment file (PDF, image, document, spreadsheet, etc)."
    )
    document_type = models.CharField(
        max_length=50,
        choices=DocumentType.choices,
        help_text="Type of the document attached."
    )
    caption = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Optional caption for the file."
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional description for the file."
    )
    is_sensitive = models.BooleanField(
        default=False,
        help_text="Indicates if the attachment contains sensitive content."
    )
    access_audit = models.JSONField(
        default=dict,
        help_text="JSON structure tracking access audit information (who accessed and when)."
    )

    class Meta:
        verbose_name = "Water Report Attachment"
        verbose_name_plural = "Water Report Attachments"
        indexes = [
            models.Index(fields=['customer_request','water_report']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        base = f"{self.water_report} | {self.get_document_type_display()}"
        return f"Attachment: {self.caption or 'No Caption'} ({base})"


class ManagementAttachment(BaseUUIDModel, TimeStampedModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey()
    file = models.FileField(upload_to="management_attachments/",
                            validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'dcm'])])
    document_type = models.CharField(max_length=50, choices=DocumentType.choices)
    caption = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_sensitive = models.BooleanField(default=False)
    access_audit = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Management Document"
        verbose_name_plural = "Management Documents"
        indexes = [models.Index(fields=['content_type', 'object_id'])]

    def __str__(self):
        return f"{self.document_type} for {self.content_object} - {self.caption or 'No Caption'}"
