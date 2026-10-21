"""Register, log in, log out, and 'who am I' endpoints (session-based)."""

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserPreference
from .serializers import RegisterSerializer, user_payload

User = get_user_model()


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CsrfView(APIView):
    """The React app calls this once on startup so the browser receives the CSRF cookie."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'detail': 'CSRF cookie set.'})


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # bad input becomes a 400 with clear messages
        data = serializer.validated_data

        # create_user hashes the password; we never store it in plain text
        user = User.objects.create_user(
            username=data['username'], email=data.get('email', ''), password=data['password'])
        UserPreference.objects.get_or_create(user=user)

        login(request, user)  # sign them in straight away
        return Response(user_payload(user), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = str(request.data.get('username', '')).strip()
        password = str(request.data.get('password', ''))

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({'detail': 'Incorrect username or password.'},
                            status=status.HTTP_400_BAD_REQUEST)

        login(request, user)
        return Response(user_payload(user))


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response({'detail': 'You have been logged out.'})


class MeView(APIView):
    """Lets the frontend ask 'am I logged in?' without getting an error when the answer is no."""

    permission_classes = [AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            return Response({'is_authenticated': True, 'user': user_payload(request.user)})
        return Response({'is_authenticated': False, 'user': None})