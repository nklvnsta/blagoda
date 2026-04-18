"""
Общие утилиты для эндпоинтов раздела «Сбор заказа» (picking).

Сборка магазина на сегодня = группа `BatchShipment` с `status=scheduled`
и `dispatch_date = COALESCE(planned_dispatch_date, shipped_at::date) = today`.

Pick-статусы вычисляются из (picked_quantity vs quantity_shipped):
  Строка:
    not_started  — picked == 0
    picked       — picked >= ordered
    partial      — иначе

  Группа (магазин):
    not_started  — все строки not_started
    picked       — все строки picked
    partial      — есть хотя бы одна partial-строка
    in_progress  — есть picked-строки и not_started-строки, partial нет
"""

from datetime import date as date_cls

from django.db.models import (
    Case,
    Count,
    F,
    IntegerField,
    Q,
    Sum,
    Value,
    When,
)
from rest_framework.pagination import PageNumberPagination

from core.models import BatchShipment
from core.views.supplies_common import dispatch_date_expr


# ── статусы группы сборки ────────────────────────────────────────────────────

class GroupPickStatus:
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PARTIAL     = "partial"
    PICKED      = "picked"

    CHOICES = (NOT_STARTED, IN_PROGRESS, PARTIAL, PICKED)


# ── базовые querysets ────────────────────────────────────────────────────────

def today_picking_qs(target_date: date_cls | None = None, shop_id: str | None = None):
    """
    Все scheduled-линии BatchShipment, у которых dispatch_date = target_date
    (по умолчанию — сегодня).
    """
    target_date = target_date or date_cls.today()
    qs = (
        BatchShipment.objects
        .filter(status=BatchShipment.Status.SCHEDULED)
        .annotate(dispatch_date=dispatch_date_expr())
        .filter(dispatch_date=target_date)
    )
    if shop_id:
        qs = qs.filter(shop_id=shop_id)
    return qs


# ── агрегаты по группе (магазин) ─────────────────────────────────────────────

def picking_group_aggregates() -> dict:
    """
    Набор annotation для group-by по shop_id:
      positions_count, ordered_units, picked_units,
      not_started_count, partial_count, picked_count.
    """
    return {
        "positions_count": Count("id"),
        "ordered_units": Sum("quantity_shipped"),
        "picked_units": Sum("picked_quantity"),
        "not_started_count": Sum(
            Case(
                When(picked_quantity=0, then=1),
                default=0,
                output_field=IntegerField(),
            )
        ),
        "picked_count": Sum(
            Case(
                When(picked_quantity__gte=F("quantity_shipped"), then=1),
                default=0,
                output_field=IntegerField(),
            )
        ),
        "partial_count": Sum(
            Case(
                When(
                    Q(picked_quantity__gt=0) & Q(picked_quantity__lt=F("quantity_shipped")),
                    then=1,
                ),
                default=0,
                output_field=IntegerField(),
            )
        ),
    }


def derive_group_status(
    positions_count: int,
    not_started_count: int,
    picked_count: int,
    partial_count: int,
) -> str:
    """Чистая Python-логика поверх агрегатов (см. правила в шапке файла)."""
    if positions_count <= 0:
        return GroupPickStatus.NOT_STARTED
    if partial_count > 0:
        return GroupPickStatus.PARTIAL
    if picked_count == positions_count:
        return GroupPickStatus.PICKED
    if picked_count == 0:
        return GroupPickStatus.NOT_STARTED
    return GroupPickStatus.IN_PROGRESS


def picking_group_qs(base_qs):
    """
    Группирует scheduled-линии по shop_id.
    Возвращает values-QuerySet со столбцами:
      shop_id, shop__name, positions_count, ordered_units, picked_units,
      not_started_count, partial_count, picked_count.
    """
    return (
        base_qs
        .values("shop_id", "shop__name")
        .annotate(**picking_group_aggregates())
    )


def row_from_picking_group(row: dict) -> dict:
    """Превращает строку values()-агрегата в словарь под фронт."""
    positions = row["positions_count"] or 0
    not_started = row["not_started_count"] or 0
    picked = row["picked_count"] or 0
    partial = row["partial_count"] or 0
    return {
        "shop_id":         str(row["shop_id"]),
        "shop_name":       row["shop__name"],
        "positions_count": positions,
        "ordered_units":   row["ordered_units"] or 0,
        "picked_units":    row["picked_units"] or 0,
        "pick_status":     derive_group_status(positions, not_started, picked, partial),
    }


# ── пагинация ────────────────────────────────────────────────────────────────

class PickingPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
