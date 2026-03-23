from datetime import date, timedelta

from django.db.models import Sum
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Shop, Category, StockDeviation


class WeekDataSerializer(serializers.Serializer):
    qty          = serializers.IntegerField(help_text="Количество отклонений за период")
    unit         = serializers.CharField(help_text="Единица измерения")
    period_start = serializers.DateField()
    period_end   = serializers.DateField()


class DeviationResponseSerializer(serializers.Serializer):
    current_week  = WeekDataSerializer()
    previous_week = WeekDataSerializer()
    change_pct    = serializers.FloatField(help_text="Изменение к прошлой неделе, %")
    filters       = serializers.DictField(help_text="Применённые фильтры")


def _week_range(weeks_ago: int) -> tuple[date, date]:
    today  = date.today()
    monday = today - timedelta(days=today.weekday()) - timedelta(weeks=weeks_ago)
    sunday = monday + timedelta(days=6)
    return monday, sunday


def _get_descendant_ids(category: Category) -> list:
    ids = [category.pk]
    for child in Category.objects.filter(parent=category):
        ids.extend(_get_descendant_ids(child))
    return ids


def _deviation_qty(
    deviation_type: str,
    date_from: date,
    date_to: date,
    shop_id: str | None,
    category_ids: list | None,
) -> int:
    qs = StockDeviation.objects.filter(
        deviation_type=deviation_type,
        calculated_at__date__gte=date_from,
        calculated_at__date__lte=date_to,
    )
    if shop_id:
        qs = qs.filter(inventory__shop_id=shop_id)
    if category_ids:
        qs = qs.filter(inventory__product__category_id__in=category_ids)

    return qs.aggregate(total=Sum("deviation_qty"))["total"] or 0


def _validate_shop(shop_id: str | None) -> None:
    if shop_id is not None and not Shop.objects.filter(pk=shop_id).exists():
        raise ValidationError({"shop": f"Магазин с id={shop_id} не найден."})


def _validate_category(category_id: str | None) -> list | None:
    if category_id is None:
        return None
    try:
        category = Category.objects.get(pk=category_id)
    except Category.DoesNotExist:
        raise ValidationError({"category": f"Категория с id={category_id} не найдена."})
    return _get_descendant_ids(category)


def _build_data(
    deviation_type: str,
    shop_id: str | None,
    category_ids: list | None,
    filters: dict,
) -> dict:
    cur_start, cur_end   = _week_range(weeks_ago=0)
    prev_start, prev_end = _week_range(weeks_ago=1)

    current_qty  = _deviation_qty(deviation_type, cur_start, cur_end, shop_id, category_ids)
    previous_qty = _deviation_qty(deviation_type, prev_start, prev_end, shop_id, category_ids)

    if previous_qty > 0:
        change_pct = round((current_qty - previous_qty) / previous_qty * 100, 1)
    elif current_qty > 0:
        change_pct = 100.0
    else:
        change_pct = 0.0

    return {
        "current_week": {
            "qty":          current_qty,
            "unit":         "шт.",
            "period_start": cur_start,
            "period_end":   cur_end,
        },
        "previous_week": {
            "qty":          previous_qty,
            "unit":         "шт.",
            "period_start": prev_start,
            "period_end":   prev_end,
        },
        "change_pct": change_pct,
        "filters":    filters,
    }


class DeficitView(APIView):
    """
    GET /api/dashboard/deficit/?shop=<uuid>&category=<uuid>

    Query params (все опциональные):
      shop     — UUID магазина
      category — UUID категории (включая дочерние)
    """

    def get(self, request: Request) -> Response:
        shop_id     = request.query_params.get("shop")
        category_id = request.query_params.get("category")

        _validate_shop(shop_id)
        category_ids = _validate_category(category_id)

        filters = {"shop": shop_id, "category": category_id}
        data = _build_data(StockDeviation.Type.DEFICIT, shop_id, category_ids, filters)
        serializer = DeviationResponseSerializer(data)
        return Response(serializer.data)


class SurplusView(APIView):
    """
    GET /api/dashboard/surplus/?shop=<uuid>&category=<uuid>

    Query params (все опциональные):
      shop     — UUID магазина
      category — UUID категории (включая дочерние)
    """

    def get(self, request: Request) -> Response:
        shop_id     = request.query_params.get("shop")
        category_id = request.query_params.get("category")

        _validate_shop(shop_id)
        category_ids = _validate_category(category_id)

        filters = {"shop": shop_id, "category": category_id}
        data = _build_data(StockDeviation.Type.SURPLUS, shop_id, category_ids, filters)
        serializer = DeviationResponseSerializer(data)
        return Response(serializer.data)
