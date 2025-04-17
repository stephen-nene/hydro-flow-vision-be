from django.urls import path, include
from rest_framework import routers
from .views import *
from profiles.views import FunnyAPIView

router = routers.DefaultRouter()
router.register(r'waterguidelines', WaterGuidelineViewSet, basename='user')
router.register(r'customerrequests', CustomerRequestViewSet, basename='customerrequest')
router.register(r'waterlabreports', WaterLabReportViewSet, basename='waterlabreport')
# router.register(r'specializations', SpecializationViewSet, basename='specialization')


urlpatterns = [
    
    path('', include(router.urls)),
    path('home', FunnyAPIView.as_view(), name='default_view'),
    # router.urls,
    
    path("agent/process-customer-request", FormatCustomerRequestPromptView.as_view()),

]
