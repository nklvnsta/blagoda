import uuid
from django.db import models

class Inventory(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product         = models.ForeignKey("core.Product", on_delete=models.CASCADE, related_name="inventory_items")
    shop            = models.ForeignKey("core.Shop", on_delete=models.CASCADE, related_name="inventory_items")
    current_qty     = models.IntegerField(default=0)

    min_stock          = models.IntegerField(default=0) # минимальный запас
    max_stock          = models.IntegerField(default=0) # максимальный запас
    avg_daily_sales    = models.FloatField(default=0.0) # среднее количество продаж в день
    safety_stock_days  = models.IntegerField(default=3) # страховой запас в днях
    reorder_cycle_days = models.IntegerField(default=7) # цикл заказа в 
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together     = [("product", "shop")]
        verbose_name        = "Остаток"
        verbose_name_plural = "Остатки"

    def __str__(self):
        return f"{self.product} / {self.shop} — {self.current_qty} шт."
 
    @property
    def deficit(self):
        return max(0, self.min_stock - self.current_qty)
 
    @property
    def surplus(self):
        return max(0, self.current_qty - self.max_stock)

class StockDeviation(models.Model):
    class Type(models.TextChoices):
        DEFICIT = "deficit", "Недостаток"
        SURPLUS = "surplus", "Избыток"

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inventory       = models.ForeignKey("core.Inventory", on_delete=models.CASCADE, related_name="deviations")
    deviation_type  = models.CharField(max_length=20, choices=Type.choices)
    deviation_qty   = models.IntegerField()
    is_active       = models.BooleanField(default=True)
    calculated_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Отклонение"
        verbose_name_plural = "Отклонения"
        indexes = [
            models.Index(fields=["is_active", "deviation_type"]),
            models.Index(fields=["calculated_at"]),
        ]

class InventorySnapshot(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product         = models.ForeignKey("core.Product", on_delete=models.CASCADE)
    shop            = models.ForeignKey("core.Shop", on_delete=models.CASCADE)
    qty             = models.IntegerField()
    snapshot_date   = models.DateField()  

    class Meta:
        unique_together = [("product", "shop", "snapshot_date")]
        verbose_name    = "Снимок остатка"
        verbose_name_plural = "Снимки остатков"