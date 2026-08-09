from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer
from .tasks import send_password_reset_email


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = LoginSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        return Response(s.validated_data)


class LogoutView(APIView):
    def post(self, request):
        try:
            RefreshToken(request.data["refresh"]).blacklist()
        except (KeyError, TokenError):
            return Response(
                {
                    "error": {
                        "code": "invalid_token",
                        "details": "Refresh token inválido.",
                    }
                },
                status=400,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user = (
            get_user_model()
            .objects.filter(
                email=str(request.data.get("email", "")).strip().lower(), is_active=True
            )
            .first()
        )
        if user:
            send_password_reset_email.delay(
                user.email,
                urlsafe_base64_encode(force_bytes(user.pk)),
                default_token_generator.make_token(user),
            )
        return Response({"detail": "Se o email existir, enviaremos as instruções."})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            user = get_user_model().objects.get(
                pk=force_str(urlsafe_base64_decode(request.data.get("uid", "")))
            )
        except Exception:
            return Response({"detail": "Token inválido ou expirado."}, status=400)
        if not default_token_generator.check_token(user, request.data.get("token", "")):
            return Response({"detail": "Token inválido ou expirado."}, status=400)
        try:
            validate_password(request.data.get("password", ""), user)
        except ValidationError as exc:
            return Response({"password": exc.messages}, status=400)
        user.set_password(request.data["password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Senha redefinida."})
