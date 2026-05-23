from rest_framework.permissions import BasePermission

from core.models import UserRole

ROLE_PREFIXES: dict[str, tuple[str, ...] | None] = {
    UserRole.ADMIN: None,
    UserRole.LOGIST: ("dashboard", "sales", "forecast", "supplies"),
    UserRole.PICKER: ("picking",),
}

ALWAYS_ALLOWED_PREFIXES = ("auth",)


def _api_resource(path: str) -> str:
    normalized = path.strip("/")
    if normalized.startswith("api/"):
        normalized = normalized[4:]
    return normalized.split("/", 1)[0] if normalized else ""


class RolePermission(BasePermission):
    message = "Недостаточно прав для этого действия."

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return True

        profile = getattr(user, "profile", None)
        role = profile.role if profile else UserRole.PICKER
        allowed = ROLE_PREFIXES.get(role, ())

        if allowed is None:
            return True

        resource = _api_resource(request.path)
        if resource in ALWAYS_ALLOWED_PREFIXES:
            return True
        return resource in allowed
