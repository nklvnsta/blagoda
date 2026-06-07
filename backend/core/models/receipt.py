import uuid 
from django.db import models

class Receipt(models.Model):
    """Модель для хранения информации о чеках, связанных с продажами"""

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop            = models.ForeignKey("core.Shop", on_delete=models.CASCADE, related_name="receipts")
    date            = models.DateField(null=True, blank=True, db_index=True)
    total_amount    = models.DecimalField(max_digits=10, decimal_places=2)  # общая сумма чека
    item_count      = models.IntegerField(default=0)  # количество позиций в чеке
    total_qty       = models.IntegerField(default=0)  # общее количество товаров в чеке
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Чек"
        verbose_name_plural = "Чеки"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["shop", "created_at"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Чек #{self.id} / {self.shop} — {self.total_amount} руб. от {self.created_at:%d.%m.%Y %H:%M}"