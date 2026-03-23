import uuid
from django.db import models


class Product(models.Model):
    class Unit(models.TextChoices):
        PCS = "pcs", "шт."
        KG  = "kg",  "кг"
        L   = "l",   "л"
        G   = "g",   "г"
        ML  = "ml",  "мл"

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category        = models.ForeignKey(
        "core.Category",
        on_delete=models.PROTECT,
        related_name="products",
    )
    name            = models.CharField(max_length=255)
    sku             = models.CharField(max_length=100, unique=True, blank=True)
    unit            = models.CharField(max_length=10, choices=Unit.choices, default=Unit.PCS)
    # Срок годности в днях — используется для предупреждений по партиям
    shelf_life_days = models.PositiveIntegerField(null=True, blank=True)
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Товар"
        verbose_name_plural = "Товары"
        ordering            = ["name"]

    def __str__(self):
        return self.name