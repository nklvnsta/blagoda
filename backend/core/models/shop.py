import uuid
from django.db import models
from django.core.validators import MinValueValidator


class Shop(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name            = models.CharField(max_length=255)
    address         = models.CharField(max_length=500)
    latitude        = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude       = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    # Страховой запас в днях — сколько дней товара должно быть в наличии
    normative_days  = models.PositiveIntegerField(default=3, validators=[MinValueValidator(1)])
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Магазин"
        verbose_name_plural = "Магазины"
        ordering            = ["name"]

    def __str__(self):
        return self.name