import uuid
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Batch(models.Model):
    """
    Партия товара, поступившая на центральный склад.
    quantity_remaining показывает сколько ещё не отгружено по магазинам.
    """

    class Status(models.TextChoices):
        AVAILABLE  = "available",  "В наличии"
        PARTIAL    = "partial",    "Частично отгружена"
        DISPATCHED = "dispatched", "Полностью отгружена"
        WRITTEN_OFF = "written_off", "Списана"

    id                 = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product            = models.ForeignKey(
        "core.Product",
        on_delete=models.PROTECT,
        related_name="batches",
    )
    quantity           = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    quantity_remaining = models.PositiveIntegerField()   # сколько осталось на складе
    production_date    = models.DateField(null=True, blank=True)
    expiry_date        = models.DateField(null=True, blank=True)
    status             = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )
    received_at        = models.DateTimeField(default=timezone.now)
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Партия"
        verbose_name_plural = "Партии"
        ordering            = ["-received_at"]
        indexes             = [
            models.Index(fields=["product", "status"]),
            models.Index(fields=["expiry_date"]),
        ]

    def __str__(self):
        return f"{self.product} — {self.quantity} {self.product.unit} от {self.received_at:%d.%m.%Y}"

    def save(self, *args, **kwargs):
        # При создании quantity_remaining = quantity
        if not self.pk:
            self.quantity_remaining = self.quantity
        self._update_status()
        super().save(*args, **kwargs)

    def _update_status(self):
        if self.status == self.Status.WRITTEN_OFF:
            return  # списанную не трогаем
        if self.quantity_remaining == 0:
            self.status = self.Status.DISPATCHED
        elif self.quantity_remaining < self.quantity:
            self.status = self.Status.PARTIAL
        else:
            self.status = self.Status.AVAILABLE

    @property
    def is_expired(self) -> bool:
        from datetime import date
        return bool(self.expiry_date and self.expiry_date < date.today())

    @property
    def days_until_expiry(self) -> int | None:
        from datetime import date
        if not self.expiry_date:
            return None
        return (self.expiry_date - date.today()).days


class BatchShipment(models.Model):
    """
    Отгрузка части партии в конкретный магазин.
    Каждая запись уменьшает batch.quantity_remaining (при переходе в in_transit/delivered).
    «Поставка» в UI = группа записей по ключу (shop, dispatch_date), где
    dispatch_date = COALESCE(planned_dispatch_date, shipped_at::date).
    """

    class Status(models.TextChoices):
        SCHEDULED  = "scheduled",  "Запланирована"
        IN_TRANSIT = "in_transit", "В пути"
        DELIVERED  = "delivered",  "Доставлена"
        CANCELLED  = "cancelled",  "Отменена"

    id                    = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch                 = models.ForeignKey(
        Batch,
        on_delete=models.PROTECT,
        related_name="shipments",
    )
    shop                  = models.ForeignKey(
        "core.Shop",
        on_delete=models.PROTECT,
        related_name="batch_shipments",
    )
    quantity_shipped      = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    shipped_at            = models.DateTimeField(default=timezone.now)
    status                = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DELIVERED,
    )
    planned_dispatch_date = models.DateField(null=True, blank=True)
    planned_delivery_date = models.DateField(null=True, blank=True)
    delivered_at          = models.DateTimeField(null=True, blank=True)
    note                  = models.TextField(blank=True)

    class Meta:
        verbose_name        = "Отгрузка партии"
        verbose_name_plural = "Отгрузки партий"
        ordering            = ["-shipped_at"]
        indexes             = [
            models.Index(fields=["shop", "status"]),
            models.Index(fields=["planned_dispatch_date"]),
            models.Index(fields=["status", "planned_dispatch_date"]),
        ]

    def __str__(self):
        return f"{self.batch.product} → {self.shop} {self.quantity_shipped} {self.batch.product.unit}"

    def save(self, *args, **kwargs):
        # Определяем, нужно ли списать остаток партии сейчас.
        # Списываем только один раз — при первом переходе в состояние,
        # где товар фактически покинул склад (in_transit / delivered).
        consuming_statuses = {self.Status.IN_TRANSIT, self.Status.DELIVERED}
        was_consuming = False
        if self.pk:
            old = type(self).objects.filter(pk=self.pk).values("status").first()
            if old is not None:
                was_consuming = old["status"] in consuming_statuses

        is_consuming = self.status in consuming_statuses

        if is_consuming and not was_consuming:
            if self.quantity_shipped > self.batch.quantity_remaining:
                raise ValueError(
                    f"Нельзя отгрузить {self.quantity_shipped} шт. — "
                    f"на складе только {self.batch.quantity_remaining} шт."
                )
            self.batch.quantity_remaining -= self.quantity_shipped
            self.batch.save()

        super().save(*args, **kwargs)