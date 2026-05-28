"""Метрики прогноза, согласованные с графиком demand-chart (дневные суммы)."""

from datetime import timedelta

from django.db.models import Sum
from django.db.models.functions import Coalesce

from core.models import ForecastEntry, Sales


def daily_actual_qty(date_from, date_to, shop_id, category_ids) -> dict:
    qs = Sales.objects.filter(date__gte=date_from, date__lte=date_to)
    if shop_id:
        qs = qs.filter(shop_id=shop_id)
    if category_ids:
        qs = qs.filter(product__category_id__in=category_ids)

    rows = (
        qs.values("date")
        .annotate(total=Coalesce(Sum("quantity"), 0))
        .order_by("date")
    )
    return {row["date"]: row["total"] for row in rows}


def daily_forecast_qty(date_from, date_to, shop_id, category_ids) -> dict:
    qs = ForecastEntry.objects.filter(date__gte=date_from, date__lte=date_to)
    if shop_id:
        qs = qs.filter(shop_id=shop_id)
    if category_ids:
        qs = qs.filter(product__category_id__in=category_ids)

    rows = (
        qs.values("date")
        .annotate(total=Coalesce(Sum("predicted_qty"), 0))
        .order_by("date")
    )
    return {row["date"]: row["total"] for row in rows}


def compute_chart_accuracy_pct(
    date_from,
    date_to,
    shop_id: str | None,
    category_ids: list | None,
) -> tuple[float, int]:
    """
    Точность по той же агрегации, что и график:
    для каждого дня периода сравниваются суммарный факт (Sales)
    и суммарный прогноз (ForecastEntry).
    """
    actual_map = daily_actual_qty(date_from, date_to, shop_id, category_ids)
    forecast_map = daily_forecast_qty(date_from, date_to, shop_id, category_ids)

    errors: list[float] = []
    cursor = date_from
    while cursor <= date_to:
        actual = actual_map.get(cursor, 0)
        if cursor in forecast_map and actual > 0:
            forecast = forecast_map[cursor]
            errors.append(abs(actual - forecast) / actual)
        cursor += timedelta(days=1)

    if not errors:
        return 0.0, 0

    mean_error = sum(errors) / len(errors)
    return round(max(0.0, 1.0 - mean_error) * 100, 1), len(errors)
