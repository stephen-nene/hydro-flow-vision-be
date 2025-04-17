from django.contrib import admin
from django.utils.html import format_html
from .models import ManagementAttachment

# admin.py
from django.contrib import admin
from .models import (
    WaterGuideline,
    WaterGuidelineParameter,
    CustomerRequest,
    WaterLabReport,
    WaterLabParameter,
    WaterReportAttachment,
    ManagementAttachment,
)


class WaterGuidelineParameterInline(admin.TabularInline):
    model = WaterGuidelineParameter
    extra = 1

@admin.register(WaterGuideline)
class WaterGuidelineAdmin(admin.ModelAdmin):
    list_display = ("body", "usage", "status", "created_at")
    list_filter = ("status", "usage")
    search_fields = ("body", "description")
    inlines = [WaterGuidelineParameterInline]

@admin.register(WaterGuidelineParameter)
class WaterGuidelineParameterAdmin(admin.ModelAdmin):
    list_display = ("name", "guideline", "min_value", "max_value", "unit")
    list_filter = ("guideline__usage",)
    search_fields = ("name", "guideline__body")

@admin.register(CustomerRequest)
class CustomerRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "water_source", "water_usage", "daily_water_requirement", "status")
    list_filter = ("status", "water_usage")
    search_fields = ("customer__username", "water_source")
    raw_id_fields = ("customer", "handlers")

@admin.register(WaterLabReport)
class WaterLabReportAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_request", "report_source", "test_type", "report_date", "created_at")
    list_filter = ("report_source", "test_type")
    search_fields = ("customer_request__id",)
    raw_id_fields = ("customer_request",)

@admin.register(WaterLabParameter)
class WaterLabParameterAdmin(admin.ModelAdmin):
    list_display = ("id", "lab_report", "name", "value", "unit")
    list_filter = ("name", "unit")
    search_fields = (
        "id",  # own ID
        "lab_report__id",  # related report UUID
        "lab_report__customer_request__id",  # deep search by request ID
        "name",
        "unit",
        "value",
    )


@admin.register(WaterReportAttachment)
class WaterReportAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "document_type", "customer_request", "water_report", "is_sensitive", "created_at")
    list_filter = ("document_type", "is_sensitive")
    search_fields = ("caption", "description")
    raw_id_fields = ("customer_request", "water_report")

@admin.register(ManagementAttachment)
class ManagementAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "document_type", "content_type", "caption", "is_sensitive", "created_at")
    list_filter = ("document_type", "is_sensitive")
    search_fields = ("caption", "description")
    raw_id_fields = ("content_type",)

