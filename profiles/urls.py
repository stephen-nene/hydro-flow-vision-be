from django.urls import path, include
from rest_framework import routers
from profiles.views import *

from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView,TokenObtainSlidingView,TokenVerifyView,TokenBlacklistView)


router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
# router.register(r'logs', LogSheetViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
        # Authentication routes ----------------------------
    path('auth/me', MeView.as_view(), name='me'),  # Logged-in user info route
    # path('auth/loginn', CustomLoginView.as_view(), name='login'),  # JWT login
    path('auth/signup', UserCreateView.as_view(), name='signup'),
    path('auth/logout', LogoutView.as_view(), name='logout'),
    path('auth/forgot', ForgotPasswordView.as_view(), name='forgot_password'),
    path('auth/reset', ResetPasswordView.as_view(), name='reset_password'),
    
    # Other routes ---------------------------
    path('auth/login', CustomTokenObtainPairView.as_view(), name='token_obtain'),  # 
    path('auth/refresh', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh token
    path('auth/obtain/sliding/', TokenObtainSlidingView.as_view(), name='token_obtain_sliding'),
    path('auth/verify/', TokenVerifyViewExtended.as_view(), name='token_verify'),

    # Logout
    path('auth/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),

    
    # All users ---------------------------------------
    path('userz',AllUserView.as_view(),name='all users')
    
    
]
