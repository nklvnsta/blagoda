"""
Общие утилиты для эндпоинтов страницы «Поставки».

Концепция «поставки» в UI — это группа записей `BatchShipment`
по ключу `(shop_id, dispatch_date)`, где
`dispatch_date = COALESCE(planned_dispatch_date, shipped_at::date)`.

Статус группы:
  - если среди линий есть scheduled  → scheduled
  - иначе если есть in_transit       → in_transit
  - иначе                            → delivered
  (cancelled-линии исключаются из расчётов)
"""

from dataclasses import dataclass
from datetime import date as date_cls
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import (
    Case,
    DecimalField,
    F,
    IntegerField,
    Q,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce, TruncDate
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination

from core.models import BatchShipment


# ── парсинг параметров ───────────────────────────────────────────────────────

def parse_date_param(value: str | None, default: date_cls, field_name: str = "date") -> date_cls:
    if not value:
        return default
    try:
        return date_cls.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(
            {field_name: f"Неверный формат даты: {value}. Ожидается YYYY-MM-DD."}
        ) from exc


# ── выражения под ORM ────────────────────────────────────────────────────────

def dispatch_date_expr():
    """
    SQL-выражение `dispatch_date`, по которому группируются линии в «поставку»:
    Coalesce(planned_dispatch_date, shipped_at::date).
    """
    return Coalesce("planned_dispatch_date", TruncDate("shipped_at"))


def line_amount_expr():
    """Сумма по линии отгрузки: quantity_shipped * batch.product.price."""
    return F("quantity_shipped") * F("batch__product__price")


def active_shipments_qs():
    """Исключаем отменённые записи из всех подсчётов."""
    return BatchShipment.objects.exclude(status=BatchShipment.Status.CANCELLED)


# ── агрегация статуса группы ─────────────────────────────────────────────────

def group_status_annotation():
    """
    Аннотация для GROUP BY `(shop_id, dispatch_date)`:
    принимает агрегированные счётчики scheduled/in_transit/delivered и
    возвращает строковый статус группы.
    """
    return Case(
        When(scheduled_count__gt=0, then=Value(BatchShipment.Status.SCHEDULED)),
        When(in_transit_count__gt=0, then=Value(BatchShipment.Status.IN_TRANSIT)),
        default=Value(BatchShipment.Status.DELIVERED),
        output_field=BatchShipment._meta.get_field("status"),
    )


def group_status_counters():
    """Счётчики по статусам внутри группы — для вычисления group_status."""
    Status = BatchShipment.Status
    return {
        "scheduled_count": Sum(
            Case(
                When(status=Status.SCHEDULED, then=1),
                default=0,
                output_field=IntegerField(),
            )
        ),
        "in_transit_count": Sum(
            Case(
                When(status=Status.IN_TRANSIT, then=1),
                default=0,
                output_field=IntegerField(),
            )
        ),
        "delivered_count": Sum(
            Case(
                When(status=Status.DELIVERED, then=1),
                default=0,
                output_field=IntegerField(),
            )
        ),
    }


def group_amount_annotation():
    return Coalesce(
        Sum(
            line_amount_expr(),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ),
        Decimal("0.00"),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )


# ── форматирование ───────────────────────────────────────────────────────────

def quantize_money(value: Decimal) -> Decimal:
    return (value or Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ── группировка «поставок» ───────────────────────────────────────────────────

@dataclass(frozen=True)
class DeliveryGroup:
    shop_id: str
    shop_name: str
    dispatch_date: date_cls
    positions_count: int
    amount: Decimal
    status: str


def grouped_deliveries_qs(base_qs=None):
    """
    Группирует линии отгрузок по (shop, dispatch_date).
    Возвращает QuerySet со столбцами:
      shop_id, shop_name, dispatch_date, positions_count, amount, group_status
    """
    qs = base_qs if base_qs is not None else active_shipments_qs()
    return (
        qs.annotate(dispatch_date=dispatch_date_expr())
          .values("shop_id", "shop__name", "dispatch_date")
          .annotate(
              positions_count=Sum(Value(1, output_field=IntegerField())),
              amount=group_amount_annotation(),
              **group_status_counters(),
          )
          .annotate(group_status=group_status_annotation())
    )


def row_from_group(row: dict) -> dict:
    return {
        "shop_id":         str(row["shop_id"]),
        "shop_name":       row["shop__name"],
        "dispatch_date":   row["dispatch_date"],
        "positions_count": row["positions_count"] or 0,
        "amount":          quantize_money(row["amount"] or Decimal("0.00")),
        "status":          row["group_status"],
    }


# ── пагинация ────────────────────────────────────────────────────────────────

class SuppliesPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


# reuse validate_shop из общих утилит продаж
from core.views.sales_common import validate_shop  # noqa: E402,F401
