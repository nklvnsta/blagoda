FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "python manage.py migrate && python manage.py shell -c \"import os; from django.contrib.auth import get_user_model; User=get_user_model(); username=os.getenv('ADMIN_USERNAME','admin'); password=os.getenv('ADMIN_PASSWORD','admin12345'); email=os.getenv('ADMIN_EMAIL','admin@example.com'); user, created = User.objects.get_or_create(username=username, defaults={'email': email}); user.email=email; user.is_staff=True; user.is_superuser=True; user.set_password(password); user.save(); print('Admin user ready:', username)\" && python manage.py runserver 0.0.0.0:8000"]