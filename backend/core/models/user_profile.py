from django.contrib.auth.models import User
from django.db import models


class UserRole(models.TextChoices):
    ADMIN = "admin", "Администратор"
    LOGIST = "logist", "Логист"
    PICKER = "picker", "Сборщик заказов"


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.PICKER,
    )

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self) -> str:
        return f"{self.user.username} ({self.get_role_display()})"
