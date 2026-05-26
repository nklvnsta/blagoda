import os
from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_admin_user(apps, schema_editor):
    User = apps.get_model("auth", "User")

    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "admin12345")
    email = os.getenv("ADMIN_EMAIL", "admin@example.com")

    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "is_staff": True,
            "is_superuser": True,
            "password": make_password(password),
        },
    )

    user.email = email
    user.is_staff = True
    user.is_superuser = True
    user.password = make_password(password)
    user.save()

    print(f"Admin user ready: {username}")

class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_userprofile"),
    ]

    operations = [
        migrations.RunPython(create_admin_user),
    ]