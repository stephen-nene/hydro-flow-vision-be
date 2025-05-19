from django.shortcuts import render,get_object_or_404
from django.db import IntegrityError
from .models import User
from .serializers import *
from django.views import View
from django.http import JsonResponse
from django.db.models import Q

from rest_framework import status, viewsets

from rest_framework_simplejwt.exceptions import AuthenticationFailed, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView,TokenVerifyView,TokenRefreshView,TokenBlacklistView
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken,UntypedToken, OutstandingToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken

from rest_framework_simplejwt.settings import api_settings

# from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated,AllowAny,IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView

from .services.emails import send_login_notification,send_welcome_email,send_email_verification,send_password_reset_email


from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import jwt
import requests
import time
from django.utils import timezone

from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from urllib.parse import urlencode
import httpagentparser

from django.conf import settings

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

# Create your views here.

def generate_activation_url(user,type='activation'):
    payload = {
        'user_id': user.id,
        'exp': datetime.now() + timedelta(seconds=50),
        'type': type,
        'jti': str(user.id) + "_activation"  # Include a custom `jti` here (can be anything unique)

    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    base_url = settings.FRONTEND_URL  # e.g. https://example.com/signup
    query_string = urlencode({'token': token})
    return f"{base_url}/activate/?{query_string}"


def get_client_ip( request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get("REMOTE_ADDR")

def blacklist_token( token):
        """
        Blacklist the token after it has been used for activation.
        """
        try:
            untoken = UntypedToken(token)  # This will decode the token and validate it
            outstanding_token = OutstandingToken.objects.get(token=untoken)  # Get the OutstandingToken instance
            BlacklistedToken.objects.create(
                token=outstanding_token,
                blacklisted_at=timezone.now()
            )
        except OutstandingToken.DoesNotExist:
            print(f"Error: Token not found in OutstandingToken table.")
            return Response({"detail": "Token not found in OutstandingToken table."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error blacklisting token: {str(e)}")
            return Response({"detail": "Error blacklisting token.", "info": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class FunnyAPIView(APIView):
    """
    A view that provides various types of funny content.
    """
    permission_classes = [AllowAny]
    def get_chuck_norris_joke(self):
        """Fetch a random Chuck Norris joke."""
        try:
            response = requests.get("https://api.chucknorris.io/jokes/random", timeout=5)
            response.raise_for_status()  # Raise an error for bad status codes
            return response.json().get("value", "Chuck Norris is too powerful to joke about.")
        except (requests.RequestException, ValueError):
            return "Chuck Norris once roundhouse kicked a server, and it's still down."

    def get_dad_joke(self):
        """Fetch a random dad joke."""
        try:
            headers = {"Accept": "application/json"}
            response = requests.get("https://icanhazdadjoke.com/", headers=headers, timeout=5)
            response.raise_for_status()
            return response.json().get("joke", "Why don't skeletons fight each other? They don't have the guts.")
        except (requests.RequestException, ValueError):
            return "I'm reading a book on anti-gravity. It's impossible to put down!"

    def get_random_meme(self):
        """Fetch a random meme image."""
        try:
            response = requests.get("https://some-random-api.com/meme", timeout=5)
            response.raise_for_status()
            return response.json().get("image", "https://i.imgur.com/funny-meme.jpg")
        except (requests.RequestException, ValueError):
            return "https://i.imgur.com/fallback-meme.jpg"

    def get_programming_joke(self):
        """Fetch a random programming joke."""
        try:
            response = requests.get("https://official-joke-api.appspot.com/jokes/programming/random", timeout=5)
            response.raise_for_status()
            if response.json():
                return response.json()[0]
            return {"setup": "Why do programmers prefer dark mode?", "punchline": "Because light attracts bugs."}
        except (requests.RequestException, ValueError):
            return {"setup": "Why do programmers hate nature?", "punchline": "It has too many bugs."}

    def get_inspirational_quote(self):
        """Fetch a random inspirational quote."""
        try:
            response = requests.get("https://api.quotable.io/random", timeout=5)
            response.raise_for_status()
            return {
                "quote": response.json().get("content", "Stay hungry, stay foolish."),
                "author": response.json().get("author", "Steve Jobs"),
            }
        except (requests.RequestException, ValueError):
            return {
                "quote": "When something is important enough, you do it even if the odds are not in your favor.",
                "author": "Elon Musk",
            }

    """
    A fun API to return different kinds of funny content.
    """

    @swagger_auto_schema(
        operation_summary="Get a random funny content",
        operation_description="""
        Returns a funny or inspirational piece of content based on the `type` query parameter.

        Supported types:
        - `chuck_norris` → Chuck Norris joke
        - `dad_joke` → Dad joke
        - `meme` → Meme image
        - `programming_joke` → Programming joke
        - `inspirational_quote` → Inspirational quote
        """,
        manual_parameters=[
            openapi.Parameter(
                'type',
                openapi.IN_QUERY,
                description="Type of funny content to fetch",
                type=openapi.TYPE_STRING,
                enum=[
                    'chuck_norris',
                    'dad_joke',
                    'meme',
                    'programming_joke',
                    'inspirational_quote'
                ],
                default='chuck_norris',
                required=False
            )
        ],
        responses={
            200: openapi.Response(description="Funny content retrieved successfully"),
            400: "Invalid content type",
            500: "Server error fetching content"
        },
        tags=["Fun"]
    )
    def get(self, request):
        content_type = request.GET.get("type", "chuck_norris")

        content = {}
        try:
            if content_type == "chuck_norris":
                res = requests.get("https://api.chucknorris.io/jokes/random", timeout=5)
                res.raise_for_status()
                content = {"chuck_norris_joke": res.json().get("value")}
            elif content_type == "dad_joke":
                headers = {"Accept": "application/json"}
                res = requests.get("https://icanhazdadjoke.com/", headers=headers, timeout=5)
                res.raise_for_status()
                content = {"dad_joke": res.json().get("joke")}
            elif content_type == "meme":
                res = requests.get("https://some-random-api.com/meme", timeout=5)
                res.raise_for_status()
                content = {"meme": res.json().get("image")}
            elif content_type == "programming_joke":
                res = requests.get("https://official-joke-api.appspot.com/jokes/programming/random", timeout=5)
                res.raise_for_status()
                joke = res.json()[0] if res.json() else {}
                content = {"programming_joke": joke}
            elif content_type == "inspirational_quote":
                res = requests.get("https://api.quotable.io/random", timeout=5)
                res.raise_for_status()
                quote_data = res.json()
                content = {
                    "inspirational_quote": {
                        "quote": quote_data.get("content"),
                        "author": quote_data.get("author")
                    }
                }
            else:
                return Response({
                    "error": "Invalid content type.",
                    "supported_types": [
                        "chuck_norris", "dad_joke", "meme", "programming_joke", "inspirational_quote"
                    ]
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "status": "100% 🔥 Ready to roll!",
            # "message": "Welcome to the ultimate API of chaos!",
            **content,
            "DIY":"url/?type=chuck_norris"
        })


class CustomTokenRefreshView(TokenRefreshView):
    @swagger_auto_schema(
        operation_summary="Refresh a JWT token",
        operation_description="Returns a new JWT token pair using the refresh token.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh_token': openapi.Schema(type=openapi.TYPE_STRING, description="Refresh token"),
            }
        ),
        responses={
            200: openapi.Response(
                description="New token pair",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access_token': openapi.Schema(type=openapi.TYPE_STRING, description="New access token"),
                        'refresh_token': openapi.Schema(type=openapi.TYPE_STRING, description="New refresh token"),
                    }
                )
            )
        },
        tags=["Auth"]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
class CustomeTokenBlacklistView(TokenBlacklistView):
    """
    Custom view to handle token blacklisting.
    """
    @swagger_auto_schema(
        operation_summary="Blacklist a JWT token",
        operation_description="Blacklists the provided refresh token.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh_token': openapi.Schema(type=openapi.TYPE_STRING, description="Refresh token"),
            }
        ),
        responses={
            205: "Token blacklisted successfully",
            400: "Invalid token or already blacklisted"
        },
        tags=["Auth"]
    )
    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except TokenError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            return Response({"detail": "Database integrity error: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Login

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view that extends TokenObtainPairView to:
    - Support login with email, username, or phone number
    - Return user data along with tokens
    - Track login attempts and send notifications
    - Provide detailed error messages
    """

    @swagger_auto_schema(
        operation_summary="Login to obtain JWT token pair",
        operation_description="Authenticate user and return JWT tokens with user info",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['identifier', 'password'],
            properties={
                'identifier': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description="Email, username or phone number"
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="User password"
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access_token': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh_token': openapi.Schema(type=openapi.TYPE_STRING),
                        'user_info': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            401: "Invalid credentials",
            400: "Bad request"
        },
        tags=["Auth"]
    )
    def post(self, request, *args, **kwargs):
        identifier = request.data.get("identifier")
        password = request.data.get("password")

        if not identifier or not password:
            return Response(
                {"error": "Both identifier and password are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Find user by email, username or phone
                    # Try to find user by identifier
            user = User.objects.filter(
                Q(email=identifier) | Q(username=identifier) | Q(phone_number=identifier)
            ).first()

            if user is None:
                return Response(
                    {"error": "No user found with that email, username, or phone number."}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if not user.check_password(password):
                return Response(
                    {"error": "Password is incorrect."},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # if not user.is_active:
            #     return Response(
            #         {"error": "This account is inactive"}, 
            #         status=status.HTTP_401_UNAUTHORIZED
            #     )

            # Get the JWT tokens
            # response = super().post(request, *args, **kwargs)
            refresh = RefreshToken.for_user(user)

            # Get login metadata
            ip = get_client_ip(request)
            user_agent = request.META.get("HTTP_USER_AGENT", "Unknown")
            parsed = httpagentparser.detect(user_agent)
            browser = parsed.get("browser", {}).get("name", "Unknown")
            os = parsed.get("os", {}).get("name", "Unknown")

            # Send login notification
            send_login_notification(user, ip, user_agent, browser, os)

            # Update last login info
            user.last_login_ip = ip
            user.save(update_fields=['last_login_ip'])

            # Return response with tokens and user data
            return Response({
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                'user_info': UserSerializer(user).data
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response(
                {"error": "Invalid credentials"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {"error": "Login failed", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
class MeView(APIView):
    """
    View to get the current user's information.
    """
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_summary="Get current user information",
        operation_description="Returns the information of the currently authenticated user.",
        responses={
            200: openapi.Response(
                description="User information",
                schema=UserSerializer()
            ),
            401: "Unauthorized"
        },
        tags=["Auth"]
    )
    def get(self, request):
        user = request.user
        if user.is_authenticated:
            user_data = UserSerializer(user).data
            return Response(user_data, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)

class ResendActivationView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @swagger_auto_schema(
        operation_summary="Resend activation email",
        operation_description="Resends the activation email to the user.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description="User email"),
            }
        ),
        responses={
            200: openapi.Response(
                description="Activation email resent successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        },
        tags=["Auth"]
    )
    def post(self, request):
        # Scenario 1: Check if the user is authenticated via token in the header
        user = None
        if request.user.is_authenticated:
            # If the user is authenticated, we use the authenticated user
            user = request.user
        else:
            # Scenario 2: If no token is provided, fall back to the email provided in the body
            email = request.data.get("email")
            if not email:
                return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.email_verified:
            return Response({"detail": "Email already verified."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate activation URL and send activation email
        activation_url = generate_activation_url(user, "activation")
        send_welcome_email(user, activation_url)

        return Response({"detail": "Activation email resent."}, status=status.HTTP_200_OK)


class UserCreateView(APIView):
    # will have a create an get. get will be used to activate a user account using the token
    # create will be used to create a new user
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Register a new user",
        operation_description="Creates a new user with the provided information.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description="Username"),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description="Email"),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description="Password"),
                
            }
        ),
        responses={
            201: openapi.Response(
                description="User created successfully",
                schema=UserSerializer()
            ),
            400: "Invalid data"
            
        },
        tags=["Auth"]
    )
    
    def post(self, request):
        serializer = UserSerializer2(data=request.data)
        if serializer.is_valid():
            

            # send a welcome email here
            # send_activation_email(user, activation_url)
            serializer = UserSerializer2(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Check for existing users case-insensitively
            # email = serializer.validated_data['email'].lower()
            # username = serializer.validated_data['username'].lower()
            
            # if User.objects.filter(Q(email__iexact=email) | Q(username__iexact=username)).exists():
            #     return Response(
            #         {"detail": "User with this email or username already exists."},
            #         status=status.HTTP_409_CONFLICT
            #     )

            # Create inactive user until email verification
            user = serializer.save(
                is_active=True,
                email_verified=False,
                status=UserStatus.PENDING
            )
             # Attempt to send activation email
            activation_url = generate_activation_url(user)
            try:
                send_welcome_email(user, activation_url)
            except Exception as e:
                # Log error, or return with warning
                return Response({
                    "message": "User created, but email sending failed.",
                    "user": UserSerializer(user).data,
                    "error": str(e)
                }, status=status.HTTP_201_CREATED)
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    # will get a token in the url to activate the user account related with it
    
    @swagger_auto_schema(
        operation_summary="Activate a user account",
        operation_description="Activates the user account associated with the provided token.",
        manual_parameters=[
            openapi.Parameter(
                'token',
                openapi.IN_QUERY,
                description="Activation token",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="User account activated successfully",
                schema=UserSerializer()
            ),
            400: "Invalid token",
            404: "User not found"
        } ,       
        tags=["Auth"]
    )
    
    def get(self,request):        
        token = request.query_params.get('token')
        if not token:
            return Response({"detail": "Activation Token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            payload  = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.SIMPLE_JWT["ALGORITHM"]])

            user_id = payload.get('user_id')
            if user_id is None:
                return Response({"detail": "Invalid token payload."}, status=status.HTTP_400_BAD_REQUEST)
            user = get_object_or_404(User, id=user_id)
            
            # if user.email_verified:
            # blacklist_token(token)
            if user.status == UserStatus.ACTIVE:
                return Response({
                        "detail": "User activated successfully.",
                        "user": UserSerializer(user).data
                    }, status=status.HTTP_200_OK)
                return Response({"detail": "User is already active."}, status=status.HTTP_400_BAD_REQUEST)
            # print(user)
            
           
            user.is_active = True
            user.email_verified = True
            user.status = UserStatus.ACTIVE
            user.save()
            

            return Response({
                "detail": "User activated successfully.",
                "user": UserSerializer(user).data
            }, status=status.HTTP_200_OK)
            # return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
            # return Response({"detail": "User is already active."}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.ExpiredSignatureError:
            return Response({"detail": "Activation token has expired."}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.DecodeError as e:
            return Response({"detail": "Invalid activation token.", "info":str(e)}, status=status.HTTP_400_BAD_REQUEST)
        # except User.DoesNotExist:
        #     return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def blacklist_token(self, token):
        """
        Blacklist the token after it has been used for activation.
        """
        try:
            untoken = UntypedToken(token)  # This will decode the token and validate it
            outstanding_token = OutstandingToken.objects.get(token=untoken)  # Get the OutstandingToken instance
            BlacklistedToken.objects.create(
                token=outstanding_token,
                blacklisted_at=timezone.now()
            )
        except OutstandingToken.DoesNotExist:
            print(f"Error: Token not found in OutstandingToken table.")
            return Response({"detail": "Token not found in OutstandingToken table."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error blacklisting token: {str(e)}")
            return Response({"detail": "Error blacklisting token.", "info": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class UpdateEmailView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Update user email",
        operation_description="Updates user email and sends verification link",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description="New email address"
                ),
            }
        ),
        responses={
            200: "Email update initiated successfully",
            400: "Invalid email",
            409: "Email already in use",
        },
        tags=["Auth",]
    )
    
    def put(self, request):
        serializer = EmailUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            new_email = serializer.validated_data['email'].lower()
            user = request.user

            # Check if email is already in use
            # if User.objects.filter(email__iexact=new_email).exclude(id=user.id).exists():
            #     return Response(
            #         {"detail": "Email already in use."},
            #         status=status.HTTP_409_CONFLICT
            #     )

            if User.objects.filter(email=new_email).exists():
                return Response(
                    {'detail': 'Email is already in use'}, 
                    status=status.HTTP_409_CONFLICT
                )

            try:
                # Generate verification token
                # token = default_token_generator.make_token(user)
                # uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                verification_url = generate_activation_url(user)
                
                # Create verification URL
                # verification_url = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}"
                
                # Store the new email temporarily
                old_email = user.email
                # You might want to create a separate model for pending email changes
                user.email = new_email
                user.email_verified = False  # Assuming you have this field
                user.status = UserStatus.PENDING
                user.save()
                
                try:                
                    # send_email_verification(user, new_email, context)     
                    send_email_verification(user, verification_url, new_email)
               
                except Exception as e:
                    # Rollback email change if sending fails
                    # user.email = old_email
                    # user.save()
                    return Response({
                        "detail": "Failed to send verification email.",
                        "error": str(e)
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                return Response({
                    "message": "Email update initiated. Please check your new email for verification.",
                    "email": new_email
                }, status=status.HTTP_200_OK)

            except Exception as e:
                # user.email = old_email
                # user.save()
                return Response({
                    "detail": "Failed to process email update.",
                    "error": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateEmailView2(APIView):
    permission_classes = [IsAuthenticated]
    
    # Define the request body schema for Swagger
    email_request_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['email'],
        properties={
            'email': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_EMAIL,
                description='New email address'
            )
        }
    )

    @swagger_auto_schema(
        operation_summary="Update user email",
        operation_description="Updates the user's email address and sends a verification link.",
        request_body=email_request_schema,
        responses={
            200: openapi.Response(
                description="Email updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'email': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Invalid email or email already in use",
            401: "Unauthorized",
            422: "Validation error"
        },
        tags=["Auth"]
    )
    
    def put(self, request, *args, **kwargs):
        new_email = request.data.get('email')
        user = request.user

        # Validate email format
        if not new_email:
            return Response(
                {'error': 'Email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if email is already in use
        if User.objects.filter(email=new_email).exclude(id=user.id).exists():
            return Response(
                {'error': 'Email is already in use'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Store the old email for verification purposes
            old_email = user.email
            
            # Update user's email
            user.email = new_email
            user.email_verified = False  # Assuming you have this field
            user.save()

            # Send verification email
            verification_link = f"https://yoursite.com/verify-email/{generate_token(user)}"
            send_mail(
                subject="Verify Your New Email",
                message=f"Please click the following link to verify your email: {verification_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[new_email],
                fail_silently=False,
            )

            return Response({
                'message': 'Email updated successfully. Please check your new email for verification.',
                'email': new_email
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # Log the error here
            return Response(
                {'error': 'Failed to update email. Please try again.'}, 
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

    def generate_token(user):
        """Generate a secure token for email verification"""
        # You can use Django's default token generator or create your own
        from django.contrib.auth.tokens import default_token_generator
        return default_token_generator.make_token(user)
    

class PasswordResetView(APIView):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Request password reset",
        operation_description="Sends a password reset link to the user's email.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description="User's email address"
                ),
            },
            required=['email']
        ),
        responses={
            200: openapi.Response(
                description="Password reset email sent successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Success message"
                        )
                    }
                )
            ),
            400: "Invalid email",
            404: "User not found"
        },
        tags=["Auth"]
    )
    def post(self, request):
        """Handle forgot password request"""
        email = request.data.get('email')
        
        if not email:
            return Response(
                {"detail": "Email is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            user = User.objects.get(email__iexact=email)
            
            # Generate password reset token
            reset_token = generate_password_reset_token(user)
            reset_url = generate_reset_url(reset_token)
            
            # Send reset email
            try:
                send_password_reset_email(user, reset_url)
            except Exception as e:
                return Response({
                    "detail": "Failed to send reset email.",
                    "error": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            return Response({
                "detail": "Password reset instructions sent to your email."
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            # For security reasons, don't reveal if email exists
            return Response({
                "detail": "If an account exists with this email, you will receive password reset instructions."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Reset password",
        operation_description="Resets user's password using the reset token.",
        manual_parameters=[
            openapi.Parameter(
                'token',
                openapi.IN_QUERY,
                description="Password reset token",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="New password"
                ),
                'confirm_password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Confirm new password"
                )
            },
            required=['new_password', 'confirm_password']
        ),
        responses={
            200: openapi.Response(
                description="Password reset successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Success message"
                        )
                    }
                )
            ),
            400: "Invalid token or password mismatch",
            404: "User not found"
        },
        tags=["Auth"]
    )
    def put(self, request):
        """Handle password reset"""
        token = request.query_params.get('token')
        new_password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')
        
        if not token:
            return Response({
                "detail": "Reset token is required."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not new_password or not confirm_password:
            return Response({
                "detail": "Both new password and confirm password are required."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if new_password != confirm_password:
            return Response({
                "detail": "Passwords do not match."
            }, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # Decode and verify token
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.SIMPLE_JWT["ALGORITHM"]]
            )
            
            user_id = payload.get('user_id')
            if user_id is None:
                return Response({
                    "detail": "Invalid token payload."
                }, status=status.HTTP_400_BAD_REQUEST)
                
            user = get_object_or_404(User, id=user_id)
            
            # Check if token is expired
            exp = payload.get('exp')
            if exp and timezone.now().timestamp() > exp:
                return Response({
                    "detail": "Reset token has expired."
                }, status=status.HTTP_400_BAD_REQUEST)
            from django.contrib.auth.password_validation import validate_password

            # Validate password
            try:
                validate_password(new_password, user)
            except Exception as e:
                return Response({
                    "detail": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # Set new password
            user.set_password(new_password)
            user.save()
            
            # Blacklist the reset token
            self.blacklist_token(token)
            
            return Response({
                "detail": "Password reset successful."
            }, status=status.HTTP_200_OK)
            
        except jwt.ExpiredSignatureError:
            return Response({
                "detail": "Reset token has expired."
            }, status=status.HTTP_400_BAD_REQUEST)
        except jwt.DecodeError:
            return Response({
                "detail": "Invalid reset token."
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def blacklist_token(self, token):
        """Blacklist the token after password reset"""
        try:
            untoken = UntypedToken(token)
            outstanding_token = OutstandingToken.objects.get(token=untoken)
            BlacklistedToken.objects.create(
                token=outstanding_token,
                blacklisted_at=timezone.now()
            )
        except OutstandingToken.DoesNotExist:
            print(f"Error: Token not found in OutstandingToken table.")
        except Exception as e:
            print(f"Error blacklisting token: {str(e)}")

# Helper functions
def generate_password_reset_token(user):
    """Generate JWT token for password reset"""
    payload = {
        'user_id': user.id,
        'exp': timezone.now() + timezone.timedelta(hours=24),  # 24 hour expiry
        'type': 'password_reset'
    }
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.SIMPLE_JWT["ALGORITHM"]
    )

def generate_reset_url(token):
    """Generate password reset URL"""
    frontend_url = settings.FRONTEND_URL
    return f"{frontend_url}/reset-password?token={token}"

    
    
class UserProfileView(RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get user profile",
        operation_description="Returns the profile information of the specified user.",
        responses={
            200: openapi.Response(
                description="User profile information",
                schema=UserSerializer()
            ),
            404: "User not found",
            401: "Unauthorized"
        },
        tags=["Auth"]
    )

    def get_object(self):
        return self.request.user
       
class TokenVerifyViewExtended(TokenVerifyView):
    """
    Extends TokenVerifyView to also return user data along with the token's validity.
    """
    @swagger_auto_schema(
        operation_summary="Verify JWT token",
        operation_description="Verifies the provided JWT token and returns user data.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'token': openapi.Schema(type=openapi.TYPE_STRING, description="JWT token"),                
            } 
        ),
        responses={
            200: openapi.Response(
                description="Token is valid",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'valid': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            400: "Invalid token",
            401: "Unauthorized"
        },
        tags=["Auth"]
        
    )

    def post(self, request, *args, **kwargs):
        token = request.data.get("token")
        if not token:
            return Response({"detail": "Token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Decode the JWT token
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

            # Check if token is expired or invalid
            if 'exp' in decoded_token and decoded_token['exp'] < int(time.time()):
                raise TokenError("Token has expired.")

            # Fetch the user using the user id from the decoded token
            user_id = decoded_token.get('user_id')  # Assuming 'user_id' is stored in the token
            if not user_id:
                raise TokenError("No user data in token.")
            
            # Retrieve the user instance
            User = get_user_model()
            user = User.objects.get(id=user_id)

            # Call the original TokenVerifyView post method
            response = super().post(request, *args, **kwargs)

            # Return the response with user data and token validity
            response.data['valid'] = True
            response.data['user'] = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
            return response

        except jwt.ExpiredSignatureError:
            return Response({"detail": "Token has expired."}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.DecodeError:
            return Response({"detail": "Token is invalid."}, status=status.HTTP_401_UNAUTHORIZED)
        except TokenError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)





class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.

    * `list`: Returns a list of all users.
    * `retrieve`: Returns the specified user.
    * `create`: Creates a new user.
    * `update`: Updates the specified user.
    * `destroy`: Deletes the specified user.
    """
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer

    # -------------------------
    # 🟩 LIST
    # -------------------------
    @swagger_auto_schema(
        operation_summary="List all users.",
        responses={200: UserSerializer(many=True)},
        tags=["users"]
    )
    def list(self, request, *args, **kwargs):
        """
        List all users.
        """
        return super().list(request, *args, **kwargs)

    # -------------------------
    # 🟩 RETRIEVE
    # -------------------------
    @swagger_auto_schema(
        operation_summary="Retrieve a user.",
        responses={200: UserSerializer()},
        tags=["users"]
    )
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a specific user by ID.
        """
        return super().retrieve(request, *args, **kwargs)

    # -------------------------
    # 🟩 CREATE
    # -------------------------
    @swagger_auto_schema(
        operation_summary="Create a new user.",
        responses={201: UserSerializer()},
        tags=["users"]
    )
    def create(self, request, *args, **kwargs):
        """
        Create a new user.
        """
        return super().create(request, *args, **kwargs)

    # -------------------------
    # 🟩 UPDATE
    # -------------------------
    @swagger_auto_schema(
        operation_summary="Update a user.",
        responses={200: UserSerializer()},
        tags=["users"]
    )
    def update(self, request, *args, **kwargs):
        """
        Fully update a user.
        """
        return super().update(request, *args, **kwargs)

    # -------------------------
    # 🟫 PARTIAL UPDATE (PATCH)
    # -------------------------
    @swagger_auto_schema(
        operation_summary="Partially update a user.",
        responses={200: UserSerializer()},
        tags=["users"]
    )
    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a user.
        """
        return super().partial_update(request, *args, **kwargs)

    # -------------------------
    # 🟩 DESTROY
    # -------------------------
    @swagger_auto_schema(
        operation_summary="Delete a user.",
        responses={204: "No content"},
        tags=["users"]
    )
    def destroy(self, request, *args, **kwargs):
        """
        Delete a user.
        """
        return super().destroy(request, *args, **kwargs)
