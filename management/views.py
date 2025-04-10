from rest_framework import viewsets, permissions, status

from django.db.models import Prefetch
from django.shortcuts import get_object_or_404


from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import *
from .serializers import *

class WaterGuidelineViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing water quality guidelines.
    """
    queryset = WaterGuideline.objects.all()
    serializer_class = WaterGuidelineSerializer

    # -------------------------
    # 🟩 LIST
    # -------------------------
    @swagger_auto_schema(
        operation_summary="List all water quality guidelines",
        operation_description="Returns all water quality guidelines with their parameters",
        responses={200: WaterGuidelineSerializer(many=True)},
        tags=["Water Quality Standards"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    # -------------------------
    # 🟩 RETRIEVE
    # -------------------------
    @swagger_auto_schema(
        operation_summary="Retrieve a specific water guideline",
        responses={200: WaterGuidelineSerializer()},
        tags=["Water Quality Standards"]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    # -------------------------
    # 🟩 CREATE
    # -------------------------
    @swagger_auto_schema(
        operation_summary="Create a new water guideline",
        request_body=WaterGuidelineSerializer,
        responses={201: WaterGuidelineSerializer()},
        tags=["Water Quality Standards"]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    # -------------------------
    # 🟩 UPDATE
    # -------------------------
    @swagger_auto_schema(
        operation_summary="Update an existing water guideline",
        request_body=WaterGuidelineSerializer,
        responses={200: WaterGuidelineSerializer()},
        tags=["Water Quality Standards"]
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    # -------------------------
    # 🟩 PARTIAL UPDATE (PATCH)
    # -------------------------
    @swagger_auto_schema(
        operation_summary="Partial update of an existing water guideline",
        request_body=WaterGuidelineSerializer,
        responses={200: WaterGuidelineSerializer()},
        tags=["Water Quality Standards"]
    )
    def partial_update(self, request, *args, **kwargs):
        """
        Partially update the water guideline (only the fields provided will be updated).
        """
        return super().partial_update(request, *args, **kwargs)
    
    # -------------------------
    # 🟩 CUSTOM ACTIONS
    # -------------------------
    @swagger_auto_schema(
        method='get',
        operation_summary="Get guidelines by usage type",
        manual_parameters=[
            openapi.Parameter(
                'usage',
                openapi.IN_QUERY,
                description="Filter by water usage type (domestic, industrial, etc.)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={200: WaterGuidelineSerializer(many=True)},
        tags=["Water Quality Standards"]
    )
    @action(detail=False, methods=['get'])
    def by_usage(self, request):
        usage = request.query_params.get('usage')
        guidelines = WaterGuideline.objects.filter(usage__iexact=usage)
        serializer = self.get_serializer(guidelines, many=True)
        return Response(serializer.data)
    # -------------------------
    # 🟩 DESTROY
    # -------------------------
    @swagger_auto_schema(
        operation_summary="Delete a water guideline",
        responses={204: "No content"},
        tags=["Water Quality Standards"]
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class CustomerRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing customer water treatment requests.
    """
    queryset = CustomerRequest.objects.all()
    serializer_class = CustomerRequestSerializer

        # Override the 'get_queryset' method to apply optimizations
    def get_queryset(self):
        # Prefetch related WaterLabReport and WaterLabParameter
        water_lab_reports = WaterLabReport.objects.prefetch_related('parameters')

        queryset = CustomerRequest.objects.select_related(
            'customer'  # Optimizing the ForeignKey to 'customer'
        ).prefetch_related(
            'handlers',  # Prefetch the many-to-many relationship with handlers (users)
            Prefetch('water_lab_reports', queryset=water_lab_reports)  # Prefetch related water_lab_reports and their parameters
        )
        return queryset

    # -------------------------
    # 🟩 LIST
    # -------------------------
    @swagger_auto_schema(
        operation_summary="List all customer requests",
        operation_description="Returns all water treatment requests from customers",
        manual_parameters=[
            openapi.Parameter(
                'status',
                openapi.IN_QUERY,
                description="Filter by status (pending, approved, rejected)",
                type=openapi.TYPE_STRING,
                required=False
            )
        ],
        responses={200: CustomerRequestSerializer(many=True)},
        tags=["Customer Requests"]
    )
    def list(self, request, *args, **kwargs):
        status_filter = request.query_params.get('status')
        if status_filter:
            self.queryset = self.queryset.filter(status=status_filter.lower())
        return super().list(request, *args, **kwargs)


    # -------------------------
    # 🟩 RETRIEVE
    # -------------------------
    @swagger_auto_schema(
        operation_summary="Retrieve a specific customer request",
        responses={200: CustomerRequestSerializer()},
        tags=["Customer Requests"]
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        serializer = self.get_serializer(instance)
        return super().retrieve(request, *args, **kwargs)
    # -------------------------
    # 🟩 CREATE
    # -------------------------
    @swagger_auto_schema(
        operation_summary="Create a new customer request",
        request_body=CustomerRequestSerializer,
        responses={201: CustomerRequestSerializer()},
        tags=["Customer Requests"]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    # -------------------------
    # 🟩 PARTIAL UPDATE (PATCH)
    # -------------------------
    @swagger_auto_schema(
        operation_summary="Partial update of an existing customer request",
        request_body=CustomerRequestSerializer,
        responses={200: CustomerRequestSerializer()},
        tags=["Customer Requests"]
    )
    def partial_update(self, request, *args, **kwargs):
        """
        Partially update the customer request (only the fields provided will be updated).
        """
        return super().partial_update(request, *args, **kwargs)

    # -------------------------
    # 🟩 UPDATE
    # -------------------------
    @swagger_auto_schema(
        operation_summary="Update an existing customer request",
        request_body=CustomerRequestSerializer,
        responses={200: CustomerRequestSerializer()},
        tags=["Customer Requests"]
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    # -------------------------
    # 🟩 CUSTOM ACTIONS
    # -------------------------
    @swagger_auto_schema(
        method='post',
        operation_summary="Assign staff to handle request",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'staff_ids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description="List of staff user IDs to assign"
                )
            }
        ),
        responses={200: CustomerRequestSerializer()},
        tags=["Customer Requests"]
    )
    @action(detail=True, methods=['post'])
    def assign_staff(self, request, pk=None):
        request_obj = self.get_object()
        staff_ids = request.data.get('staff_ids', [])
        request_obj.handlers.add(*staff_ids)
        return Response(self.get_serializer(request_obj).data)
    
    # -------------------------
    # 🟩 DESTROY
    # -------------------------
    @swagger_auto_schema(
        operation_summary="Delete a customer request",
        responses={204: "No content"},
        tags=["Customer Requests"]
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

class WaterLabReportViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing water laboratory test reports.
    """
    queryset = WaterLabReport.objects.all()
    serializer_class = WaterLabReportSerializer

    # -------------------------
    # 🟩 CREATE
    # -------------------------
    @swagger_auto_schema(
        operation_summary="Create a new lab report with parameters",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                **WaterLabReportSerializer().get_fields(),
                'parameters': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'name': openapi.Schema(type=openapi.TYPE_STRING),
                            'value': openapi.Schema(type=openapi.TYPE_NUMBER),
                            'unit': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    )
                )
            }
        ),
        responses={201: WaterLabReportSerializer()},
        tags=["Laboratory Reports"]
    )
    def create(self, request, *args, **kwargs):
        # Handle report creation with parameters
        report_data = request.data.copy()
        parameters_data = report_data.pop('parameters', [])
        
        serializer = self.get_serializer(data=report_data)
        serializer.is_valid(raise_exception=True)
        report = serializer.save()
        
        # Create parameters
        for param_data in parameters_data:
            WaterLabParameter.objects.create(lab_report=report, **param_data)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # -------------------------
    # 🟩 CUSTOM ACTIONS
    # -------------------------
    @swagger_auto_schema(
        method='get',
        operation_summary="Compare report against guidelines",
        responses={200: openapi.Response(
            description="Comparison results",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'guideline': openapi.Schema(type=openapi.TYPE_STRING),
                    'parameters': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Items(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'name': openapi.Schema(type=openapi.TYPE_STRING),
                                'value': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'unit': openapi.Schema(type=openapi.TYPE_STRING),
                                'guideline_min': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'guideline_max': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'status': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    )
                }
            )
        )},
        tags=["Laboratory Reports"]
    )
    @action(detail=True, methods=['get'])
    def compare(self, request, pk=None):
        report = self.get_object()
        # Implementation would compare report parameters against guidelines
        return Response({"message": "Comparison results would go here"})

class WaterReportAttachmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing water report attachments.
    """
    queryset = WaterReportAttachment.objects.all()
    serializer_class = WaterReportAttachmentSerializer

    # -------------------------
    # 🟩 CREATE
    # -------------------------
    @swagger_auto_schema(
        operation_summary="Upload a new attachment",
        manual_parameters=[
            openapi.Parameter(
                'file',
                openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                required=True,
                description='Document file'
            )
        ],
        responses={201: WaterReportAttachmentSerializer()},
        tags=["Attachments"]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    # -------------------------
    # 🟩 CUSTOM ACTIONS
    # -------------------------
    @swagger_auto_schema(
        method='get',
        operation_summary="List attachments by type",
        manual_parameters=[
            openapi.Parameter(
                'document_type',
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                enum=[dt[0] for dt in DocumentType.choices],
                required=True,
                description='Filter by document type'
            )
        ],
        responses={200: WaterReportAttachmentSerializer(many=True)},
        tags=["Attachments"]
    )
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        doc_type = request.query_params.get('document_type')
        attachments = self.queryset.filter(document_type=doc_type)
        serializer = self.get_serializer(attachments, many=True)
        return Response(serializer.data)