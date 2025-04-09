from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.db import transaction


from django.contrib.auth.hashers import check_password


from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, viewsets

from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken
# from rest_framework.exceptions import AuthenticationFailed


import requests
from decouple import config


from profiles.services.emails import send_login_email,send_custom_email,send_welcome_email
from .models import User
from .serializers import *



from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


ENVIRONMENT = config('ENVIRONMENT', default="development")

is_production = ENVIRONMENT == 'production'

# Create your views here.



class FunnyAPIView(View):
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

    def get(self, request, *args, **kwargs):
        """Handle GET requests and return a dynamic response based on the 'type' parameter."""
        content_type = request.GET.get("type", "chuck_norris")  # Default to Chuck Norris jokes

        if content_type == "chuck_norris":
            content = {"chuck_norris_joke": self.get_chuck_norris_joke()}
        elif content_type == "dad_joke":
            content = {"dad_joke": self.get_dad_joke()}
        elif content_type == "meme":
            content = {"meme": self.get_random_meme()}
        elif content_type == "programming_joke":
            content = {"programming_joke": self.get_programming_joke()}
        elif content_type == "inspirational_quote":
            content = {"inspirational_quote": self.get_inspirational_quote()}
        else:
            # Return error with documentation
            content = {
                "error": "Invalid content type specified.",
                "documentation": {
                    "supported_types": {
                        "type=chuck_norris": "Returns a Chuck Norris joke.",
                        "type=dad_joke": "Returns a dad joke.",
                        "type=meme": "Returns a random meme.",
                        "type=programming_joke": "Returns a programming joke.",
                        "type=inspirational_quote": "Returns an inspirational quote.",
                    },
                    "message": "Please use one of the supported types.",
                },
            }

        # Add a default message and status
        response_data = {
            "message": "Welcome to the ultimate API of chaos!",
            "status": "🔥 Ready to roll!",
            **content,  # Merge the content into the response
        }

        return JsonResponse(response_data)




# ----------------- Authentication Views -----------------

class AuthenticationMixin:
    def get_authenticated_user(self, request):
        # Try with access token first
        access_token = request.COOKIES.get('access')
        if access_token:
            try:
                token = AccessToken(access_token)
                user_id = token['user_id']
                return User.objects.get(id=user_id), None
            except Exception:
                # print("passed access",access_token)
                pass

        # Try with refresh token if access token is invalid
        refresh_token = request.COOKIES.get('refresh')
        if refresh_token:
            try:
                refresh = RefreshToken(refresh_token)
                user_id = refresh['user_id']
                new_access_token = str(refresh.access_token)
                response = Response()
                response.set_cookie('refresh', refresh.access_token, httponly=True, samesite='None' if is_production else 'None', secure=True)
                response.set_cookie('access', new_access_token, httponly=True, samesite='None' if is_production else 'None', secure=True)

                user = User.objects.get(id=user_id)
                return user, response
            except Exception:
                # print("passed refresh",refresh_token)
                pass

        response = Response()
        response.delete_cookie('access', samesite="None")
        response.delete_cookie('refresh', samesite="None")
        raise AuthenticationFailed('Unauthorized, please log in.')
    

# ---------------------   login   ---------------------

class CustomLoginView(APIView):
    def post(self, request):
        # Get the login credentials
        # print(request.data)
        identifier = request.data.get('identifier')
        password = request.data.get('password')
        
        if not identifier or not password:
            return Response({"error": "Both identifier and password are required."}, status=400)
        
        user = User.objects.filter(email=identifier).first() or \
               User.objects.filter(phone_number=identifier).first() or \
               User.objects.filter(username=identifier).first()

        if not user:
            raise AuthenticationFailed("User not found.")
        if not check_password(password, user.password):
            raise AuthenticationFailed("Incorrect password.")
                # Send login email
        try:
            print("will send login email here")
            # send_login_email(user.email, user.username)
        except Exception as e:
            print(f"Failed to send login email: {str(e)}")
            return Response({"error": f"Failed to send login email: {str(e)}"}, status=500)

        refresh = RefreshToken.for_user(user)
        serialized_user = UserSerializer(user).data
        response = Response({
            "message": "Login successful.",
            "User": serialized_user
        })
        response.set_cookie(
            key='access',
            value=str(refresh.access_token),
            httponly=True,
            samesite="None",
            # samesite='Lax' if is_production else 'None',
            secure=True,
        )
        response.set_cookie(
            key='refresh',
            value=str(refresh),
            httponly=True,
            samesite="None",
            secure=True
        )
        return response
    
class UserCreateView(APIView):
    def post(self, request):
        try:
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                return Response({
                    "message": "User created successfully.",
                    "user": serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": "User creation failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ResetPasswordView(APIView):
    def post(self, request):
        # take the token and the new passwords all over again
        pass
    
class ForgotPasswordView(APIView):
    def post(self, request):
        # take the email and then chack in db and send email with reset instaructiosn and link
        pass
    
# ---------------------   logout   ---------------------

class LogoutView(APIView):
    def post(self, request):
        try:
            response = Response({"message": "Logout successful."}, status=status.HTTP_200_OK)
            response.delete_cookie(key='access', samesite="None")
            response.delete_cookie(key='refresh', samesite="None")
            return response

        except Exception as e:
            return Response(
                {"error": "Something went wrong during logout.", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
      

@api_view(['POST'])
def signup(request):
    serializer = UserSerializer(data=request.data)  # Deserialize user input
    if serializer.is_valid():  # Validate input
        user = serializer.save(password=make_password(serializer.validated_data['password']))
        return Response({
            "message": "User created successfully.",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone_number": user.phone_number
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MeView(APIView, AuthenticationMixin):
    def get(self, request):
        user, response = self.get_authenticated_user(request) 
        serialized_user = UserSerializer(user).data
        
        if response:
            response.data = {'User': serialized_user}
            return response
        
        return Response({'User': serialized_user})
      
            
# ---------------    get all user2   ---------------------

class AllUserView(APIView,AuthenticationMixin):
    def get(self, request):
        try:
            user, _ = self.get_authenticated_user(request)
            users = User.objects.all()  # Assuming a related name 'records' for associated data
            # serialized_records = UserSerializer(users, many=True).data
            return Response({'users': users})
        except AuthenticationFailed as e:
            response = JsonResponse({'detail': str(e)}, status=401)
            return response
        
# ----------------------- 
            

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.

    * `list`: Returns a list of all users.
    * `retrieve`: Returns the specified user.
    * `create`: Creates a new user.
    * `update`: Updates the specified user.
    * `destroy`: Deletes the specified user.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    # -------------------------
    # 🟩 LIST
    # -------------------------
    @swagger_auto_schema(
        operation_summary="List all users.",
        responses={200: UserSerializer(many=True)},
        # tags=["users"]
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
