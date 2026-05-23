from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models.user_profile import UserProfile, UserRole


@receiver(post_save, sender=User)
def ensure_user_profile(sender, instance: User, created: bool, **kwargs) -> None:
    if hasattr(instance, "profile"):
        return
    default_role = UserRole.ADMIN if instance.is_superuser else UserRole.PICKER
    UserProfile.objects.create(user=instance, role=default_role)
