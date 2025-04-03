from django.urls import path, include
from rest_framework import routers
from .views import *
from profiles.views import FunnyAPIView

router = routers.DefaultRouter()
# router.register(r'specializations', SpecializationViewSet, basename='specialization')


urlpatterns = [
    
    path('', include(router.urls)),
    path('home', FunnyAPIView.as_view(), name='default_view'),
    # router.urls,
    
]
