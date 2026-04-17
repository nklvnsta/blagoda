from datetime import date, timedelta

from math import ceil

from django.db.models import Sum, Max, Count, Q
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

class CriticalStockSerializer(serializers.Serializer):
    product = serializers.CharField(help_text="Название товара")
    shop = serializers.CharField(help_text="Название магазина")
    deviation_qty = serializers.IntegerField(help_text="Количество отклонений")
    deviation_type = serializers.CharField(help_text="Тип отклонения")
    calculated_at = serializers.DateTimeField(help_text="Дата расчёта")


class ProblemProductSerializer(serializers.Serializer):
    product_id         = serializers.UUIDField(help_text="ID товара")
    product            = serializers.CharField(help_text="Название товара")
    total_deviation_qty = serializers.IntegerField(help_text="Суммарное отклонение (шт.)")
    deficit_qty        = serializers.IntegerField(help_text="Суммарный дефицит (шт.)")
    surplus_qty        = serializers.IntegerField(help_text="Суммарный избыток (шт.)")
    affected_shops     = serializers.IntegerField(help_text="Количество магазинов с отклонением")
    last_calculated_at = serializers.DateTimeField(help_text="Последняя дата расчёта")


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

class CriticalStockView(APIView):
    """
    GET /api/dashboard/critical-stock/?deviation_type=deficit|surplus&limit=<int>

    Возвращает критические отклонения для всех магазинов и категорий.
    Опционально фильтрует по типу (deficit/surplus) и ограничивает топ `limit`
    записями, что позволяет сразу получать нужный топ без дополнительной
    сортировки на клиенте.
    """

    ALLOWED_TYPES = {StockDeviation.Type.DEFICIT, StockDeviation.Type.SURPLUS}
    DEFAULT_LIMIT_MAX = 200

    def get(self, request: Request) -> Response:
        deviation_type = request.query_params.get("deviation_type")
        if deviation_type is not None and deviation_type not in self.ALLOWED_TYPES:
            raise ValidationError(
                {"deviation_type": f"Допустимые значения: {sorted(self.ALLOWED_TYPES)}"}
            )

        limit_raw = request.query_params.get("limit")
        limit: int | None = None
        if limit_raw is not None:
            try:
                limit = int(limit_raw)
            except ValueError as exc:
                raise ValidationError(
                    {"limit": "Должно быть целым числом > 0."}
                ) from exc
            if limit <= 0:
                raise ValidationError({"limit": "Должно быть > 0."})
            limit = min(limit, self.DEFAULT_LIMIT_MAX)

        base_qs = StockDeviation.objects.filter(is_active=True)
        max_qty = base_qs.aggregate(max_qty=Max("deviation_qty"))["max_qty"] or 0
        if max_qty <= 0:
            serializer = CriticalStockSerializer([], many=True)
            return Response(serializer.data)

        # Относительный порог: критичными считаем отклонения >= 60% от максимального.
        # Это адаптируется под текущий масштаб данных и не требует "жёсткого" числа.
        critical_threshold = ceil(max_qty * 0.6)

        stock_deviations = (
            base_qs
            .filter(deviation_qty__gte=critical_threshold)
            .select_related("inventory__product", "inventory__shop")
            .order_by("-deviation_qty")
        )
        if deviation_type:
            stock_deviations = stock_deviations.filter(deviation_type=deviation_type)
        if limit is not None:
            stock_deviations = stock_deviations[:limit]

        data = []
        for stock_deviation in stock_deviations:
            data.append({
                "product": stock_deviation.inventory.product.name,
                "shop": stock_deviation.inventory.shop.name,
                "deviation_qty": stock_deviation.deviation_qty,
                "deviation_type": stock_deviation.deviation_type,
                "calculated_at": stock_deviation.calculated_at.isoformat(),
            })
        serializer = CriticalStockSerializer(data, many=True)
        return Response(serializer.data)


class ProblemProductsView(APIView):
    """
    GET /api/dashboard/problem-products/

    Возвращает проблемные товары (агрегировано по сети) с относительным порогом:
    товар считается проблемным, если его суммарное отклонение >= 60% от максимального.
    """

    def get(self, request: Request) -> Response:
        grouped = (
            StockDeviation.objects
            .filter(is_active=True)
            .values("inventory__product_id", "inventory__product__name")
            .annotate(
                total_deviation_qty=Sum("deviation_qty"),
                deficit_qty=Sum("deviation_qty", filter=Q(deviation_type=StockDeviation.Type.DEFICIT)),
                surplus_qty=Sum("deviation_qty", filter=Q(deviation_type=StockDeviation.Type.SURPLUS)),
                affected_shops=Count("inventory__shop_id", distinct=True),
                last_calculated_at=Max("calculated_at"),
            )
            .order_by("-total_deviation_qty")
        )

        max_total = grouped.aggregate(max_total=Max("total_deviation_qty"))["max_total"] or 0
        if max_total <= 0:
            serializer = ProblemProductSerializer([], many=True)
            return Response(serializer.data)

        threshold = ceil(max_total * 0.6)
        items = []
        for row in grouped:
            if row["total_deviation_qty"] < threshold:
                continue
            items.append({
                "product_id": row["inventory__product_id"],
                "product": row["inventory__product__name"],
                "total_deviation_qty": row["total_deviation_qty"] or 0,
                "deficit_qty": row["deficit_qty"] or 0,
                "surplus_qty": row["surplus_qty"] or 0,
                "affected_shops": row["affected_shops"] or 0,
                "last_calculated_at": row["last_calculated_at"],
            })

        serializer = ProblemProductSerializer(items, many=True)
        return Response(serializer.data)
