import os
from django.contrib.auth import get_user_model

User = get_user_model()

username = os.getenv("ADMIN_USERNAME", "admin")
password = os.getenv("ADMIN_PASSWORD", "12345")
email = os.getenv("ADMIN_EMAIL", "admin@example.com")

user, created = User.objects.get_or_create(
    username=username,
    defaults={"email": emamil}
)

user.email = email
user.is_staff = True
user.is_superuser = True
user.set_password(password)
user.save()

print(f"Admin user ready: {username}")