import uuid
from django.db import models


class ForecastEntry(models.Model):
    """
    Прогноз спроса на конкретный товар в конкретном магазине на конкретную дату.
    Прогноз строится как avg(продажи за 30 дней) × weekday_factor.
    """
    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product           = models.ForeignKey("core.Product", on_delete=models.CASCADE, related_name="forecasts")
    shop              = models.ForeignKey("core.Shop", on_delete=models.CASCADE, related_name="forecasts")
    date              = models.DateField()
    predicted_qty     = models.IntegerField(help_text="Прогнозируемое количество продаж")
    actual_qty        = models.IntegerField(null=True, blank=True, help_text="Фактическое количество продаж")
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together     = [("product", "shop", "date")]
        verbose_name        = "Прогноз спроса"
        verbose_name_plural = "Прогнозы спроса"
        ordering            = ["-date"]
        indexes             = [
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return f"{self.product} / {self.shop} — {self.date}: прогноз {self.predicted_qty}, факт {self.actual_qty}"

    @property
    def error(self) -> float | None:
        if self.actual_qty is None or self.actual_qty == 0:
            return None
        return abs(self.actual_qty - self.predicted_qty) / self.actual_qty

    @property
    def accuracy(self) -> float | None:
        if self.error is None:
            return None
        return max(0.0, 1.0 - self.error)
