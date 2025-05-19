from django.urls import path, include
from rest_framework import routers
from .views import *

from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView,TokenObtainSlidingView,TokenVerifyView,TokenBlacklistView)


router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
# router.register(r'logs', LogSheetViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # Authentication routes ----------------------------
    # path('auth/me2', UserProfileView.as_view(), name='me_update'),  # Update logged-in user info route
    # path('auth/loginn', CustomLoginView.as_view(), name='login'),  # JWT login
    
    # path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),


    # Authentication routes ---------------------------
    path('auth/me', MeView.as_view(), name='me'),  # Logged-in user info route
    path('auth/login', CustomTokenObtainPairView.as_view(), name='token_obtain'),  # 
    path('auth/refresh', CustomTokenRefreshView.as_view(), name='token_refresh'),  # Refresh token
    path('auth/logout/', CustomeTokenBlacklistView.as_view(), name='token_blacklist'),
    # path('auth/obtain/sliding/', TokenObtainSlidingView.as_view(), name='token_obtain_sliding'),
    path('auth/verify/', TokenVerifyViewExtended.as_view(), name='token_verify'),

    path('auth/signup', UserCreateView.as_view(), name='signup'),
    path('auth/activate/resend', ResendActivationView.as_view(), name='resend_activation_email'),
    path('auth/update-email', UpdateEmailView.as_view(), name='update-email'),

    # path('auth/forgot', ForgotPasswordView.as_view(), name='forgot_password'),
    # path('auth/reset', ResetPasswordView.as_view(), name='reset_password'),
    path('auth/password-reset', PasswordResetView.as_view(), name='password_reset'),
    
    # Logout

    
    # All users ---------------------------------------
    # path('userz',UserViewSet,name='all users')
    
    
]

