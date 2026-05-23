from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.models import UserRole


def user_display_name(user: User) -> str:
    parts = [user.last_name, user.first_name]
    name = " ".join(part for part in parts if part).strip()
    return name or user.username


def get_user_role(user: User) -> str:
    profile = getattr(user, "profile", None)
    if profile is None:
        return UserRole.PICKER
    return profile.role


def user_payload(user: User) -> dict:
    role = get_user_role(user)
    return {
        "id": user.pk,
        "username": user.username,
        "display_name": user_display_name(user),
        "role": role,
        "role_label": UserRole(role).label,
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
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        return Response(user_payload(request.user))
