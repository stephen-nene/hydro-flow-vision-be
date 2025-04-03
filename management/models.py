from django.db import models
from uuid import uuid4
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.utils import timezone


# Enums 
class DocumentType(models.TextChoices):
    # doc tyes for water treatements
    WATER_TREATMENT_PLAN = 'Water Treatment Plan', 'Water Treatment Plan'
    WATER_QUALITY_REPORT = 'Water Quality Report', 'Water Quality Report'
    WATER_QUALITY_MONITORING = 'Water Quality Monitoring', 'Water Quality Monitoring'
    WATER_QUALITY_ASSESSMENT = 'Water Quality Assessment', 'Water Quality Assessment'
    WATER_QUALITY_REGULATIONS = 'Water Quality Regulations', 'Water Quality Regulations'
    


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
