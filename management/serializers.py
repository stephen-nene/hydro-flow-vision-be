# from rest_framework import serializers
# from rest_framework import serializers
# from .models import *

# class WaterLabParameterSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = WaterLabParameter
#         fields = ['id', 'name', 'unit', 'value']
#         read_only_fields = fields


# class WaterReportAttachmentSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = WaterReportAttachment
#         fields = [
#             'id', 'document_type', 'caption', 'description',
#             'is_sensitive', 'file', 'created_at'
#         ]
#         read_only_fields = fields


# class WaterLabReportSerializer(serializers.ModelSerializer):
#     parameters = WaterLabParameterSerializer(many=True, read_only=True)
#     attachments = WaterReportAttachmentSerializer(many=True, read_only=True)

#     class Meta:
#         model = WaterLabReport
#         fields = [
#             'id', 'report_source', 'test_type', 'created_at',
#             'parameters', 'attachments'
#         ]
#         read_only_fields = fields


# class CustomerRequestSerializer(serializers.ModelSerializer):
#     water_lab_reports = WaterLabReportSerializer(many=True, read_only=True)

#     class Meta:
#         model = CustomerRequest
#         fields = [
#             'id', 'water_source', 'daily_water_requirement', 'daily_flow_rate',
#             'water_usage', 'site_location', 'extras', 'budjet', 'status',
#             'created_at', 'updated_at', 'water_lab_reports'
#         ]
#         read_only_fields = fields


# class WaterGuidelineParameterSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = WaterGuidelineParameter
#         fields = ['id', 'name', 'unit', 'min_value', 'max_value']
#         read_only_fields = fields


# class WaterGuidelineSerializer(serializers.ModelSerializer):
#     parameters = WaterGuidelineParameterSerializer(many=True, read_only=True)

#     class Meta:
#         model = WaterGuideline
#         fields = ['id', 'body', 'usage', 'parameters']
#         read_only_fields = fields




from rest_framework import serializers
from .models import *
from profiles.serializers import UserSerializer  # Assuming you have this

class WaterGuidelineParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterGuidelineParameter
        fields = ['id', 'name', 'unit', 'min_value', 'max_value']
        read_only_fields = fields

class WaterGuidelineSerializer(serializers.ModelSerializer):
    parameters = WaterGuidelineParameterSerializer(many=True, read_only=True)
    
    class Meta:
        model = WaterGuideline
        fields = ['id', 'body', 'usage', 'parameters']
        read_only_fields = fields

class WaterLabParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaterLabParameter
        fields = ['id', 'name', 'unit', 'value']
        read_only_fields = fields

class WaterLabReportSerializer2(serializers.ModelSerializer):
    params = WaterLabParameterSerializer(many=True, read_only=True)
    class Meta:
        model = WaterLabReport
        fields = ['id', 'report_source', 'report_date', 'test_type','params']

class CustomerRequestSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)
    handlers = UserSerializer(many=True, read_only=True)
    water_lab_reports = WaterLabReportSerializer2(many=True, read_only=True)  # Related reports

    class Meta:
        model = CustomerRequest
        fields = [
            'id', 'customer', 'handlers', 'water_source', 
            'daily_water_requirement', 'daily_flow_rate',
            'water_usage', 'site_location', 'extras', 
            'budjet', 'status', 'water_lab_reports', 'created_at'
        ]
        read_only_fields = fields



class WaterLabReportSerializer(serializers.ModelSerializer):
    parameters = WaterLabParameterSerializer(many=True, read_only=True)
    customer_request = serializers.PrimaryKeyRelatedField(read_only=True)
    test_type_display = serializers.CharField(source='get_test_type_display', read_only=True)
    report_source_display = serializers.CharField(source='get_report_source_display', read_only=True)
    
    class Meta:
        model = WaterLabReport
        fields = [
            'id', 'customer_request', 'report_source', 'report_source_display',
            'report_date', 'test_type', 'test_type_display', 'parameters',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields

class WaterReportAttachmentSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    
    class Meta:
        model = WaterReportAttachment
        fields = [
            'id', 'water_report', 'file', 'document_type', 'document_type_display',
            'caption', 'description', 'is_sensitive', 'access_audit', 'created_at'
        ]
        read_only_fields = fields

class ManagementAttachmentSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    content_object = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = ManagementAttachment
        fields = [
            'id', 'content_type', 'object_id', 'content_object', 'file',
            'document_type', 'document_type_display', 'caption', 'description',
            'is_sensitive', 'access_audit', 'created_at'
        ]
        read_only_fields = fields
    
    def get_content_object(self, obj):
        # Generic method to display minimal info about related object
        return str(obj.content_object) if obj.content_object else None