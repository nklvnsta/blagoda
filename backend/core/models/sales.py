import uuid
from django.db import models
from decimal import Decimal

class Sales(models.Model):
    """Продажа конкретного товара из магазина"""
    
    id            = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product       = models.ForeignKey("core.Product", on_delete=models.CASCADE)
    shop          = models.ForeignKey("core.Shop", on_delete=models.CASCADE)
    quantity      = models.IntegerField()

    # Цена в момент продажи
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2, help_text="Цена за единицу в момент продажи")

    # Связь с чеком (Many-to-One)
    receipt       = models.ForeignKey("core.Receipt", on_delete=models.CASCADE, null=True, blank=True, related_name="sales", help_text="Чек, в котором была совершена продажа")

    date          = models.DateField(db_index=True)

    class Meta:
        verbose_name        = "Продажа"
        verbose_name_plural = "Продажи"
        ordering            = ["-date"]
        indexes = [
            models.Index(fields=["product", "shop", "date"]),
            models.Index(fields=["receipt"]),
        ]

    def __str__(self):
        return f"{self.product} / {self.shop} — {self.quantity} {self.product.unit} / {self.date}"
