from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


def user_display_name(user: User) -> str:
    parts = [user.last_name, user.first_name]
    name = " ".join(part for part in parts if part).strip()
    return name or user.username


def user_payload(user: User) -> dict:
    return {
        "id": user.pk,
        "username": user.username,
        "display_name": user_display_name(user),
    }


class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user: User):
        return super().get_token(user)

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = user_payload(self.user)
        return data


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer


class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]


class MeView(APIView):
    def get(self, request: Request) -> Response:
        return Response(user_payload(request.user))
