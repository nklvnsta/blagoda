import uuid
from django.db import models

class Sales(models.Model):
    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product      = models.ForeignKey("core.Product", on_delete=models.CASCADE)
    shop         = models.ForeignKey("core.Shop", on_delete=models.CASCADE)
    quantity     = models.IntegerField()
    date         = models.DateField()

    class Meta:
        verbose_name        = "Продажа"
        verbose_name_plural = "Продажи"
        ordering            = ["-date"]

    def __str__(self):
        return f"{self.product} / {self.shop} — {self.quantity} {self.product.unit} / {self.date}"
