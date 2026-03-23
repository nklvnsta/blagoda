from datetime import date, timedelta
from decimal import Decimal

from django.db.models import F, Sum, DecimalField
from django.db.models.functions import Coalesce, TruncWeek
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Sales, ForecastEntry, Shop, Category


class WeekPointSerializer(serializers.Serializer):
    week_start    = serializers.DateField(help_text="Понедельник недели")
    actual        = serializers.DecimalField(max_digits=12, decimal_places=1, help_text="Факт, тыс. руб.")
    forecast      = serializers.DecimalField(
        max_digits=12, decimal_places=1,
        allow_null=True,
        help_text="Прогноз, тыс. руб. (null — нет данных)",
    )


class SalesChartResponseSerializer(serializers.Serializer):
    unit         = serializers.CharField(help_text="Единица измерения (тыс. руб.)")
    period_start = serializers.DateField()
    period_end   = serializers.DateField()
    points       = WeekPointSerializer(many=True)
    filters      = serializers.DictField(help_text="Применённые фильтры")


CHART_WEEKS = 26


def _get_descendant_ids(category: Category) -> list:
    ids = [category.pk]
    for child in Category.objects.filter(parent=category):
        ids.extend(_get_descendant_ids(child))
    return ids


class SalesChartView(APIView):
    """
    GET /api/dashboard/sales-chart/?shop=<uuid>&category=<uuid>

    Возвращает понедельные данные за последние 6 месяцев (26 недель):
      actual   — фактическая выручка (тыс. руб.)
      forecast — прогнозная выручка (тыс. руб.)

    Query params (все опциональные):
      shop     — UUID магазина
      category — UUID категории (включая дочерние)
    """

    def get(self, request: Request) -> Response:
        shop_id     = request.query_params.get("shop")
        category_id = request.query_params.get("category")
        category_ids = None

        if shop_id and not Shop.objects.filter(pk=shop_id).exists():
            raise ValidationError({"shop": f"Магазин с id={shop_id} не найден."})

        if category_id:
            try:
                category = Category.objects.get(pk=category_id)
            except Category.DoesNotExist:
                raise ValidationError({"category": f"Категория с id={category_id} не найдена."})
            category_ids = _get_descendant_ids(category)

        today = date.today()
        period_start = today - timedelta(weeks=CHART_WEEKS)
        period_start -= timedelta(days=period_start.weekday())

        actual_map = self._actual_revenue(period_start, today, shop_id, category_ids)
        forecast_map = self._forecast_revenue(period_start, today, shop_id, category_ids)

        points = []
        cursor = period_start
        while cursor <= today:
            actual_val = actual_map.get(cursor, Decimal(0))
            forecast_val = forecast_map.get(cursor)

            points.append({
                "week_start": cursor,
                "actual":     round(actual_val / 1000, 1),
                "forecast":   round(forecast_val / 1000, 1) if forecast_val is not None else None,
            })
            cursor += timedelta(weeks=1)

        data = {
            "unit":         "тыс. руб.",
            "period_start": period_start,
            "period_end":   today,
            "points":       points,
            "filters": {
                "shop":     shop_id,
                "category": category_id,
            },
        }

        serializer = SalesChartResponseSerializer(data)
        return Response(serializer.data)

    @staticmethod
    def _actual_revenue(
        date_from: date,
        date_to: date,
        shop_id: str | None,
        category_ids: list | None,
    ) -> dict[date, Decimal]:
        qs = Sales.objects.filter(date__gte=date_from, date__lte=date_to)
        if shop_id:
            qs = qs.filter(shop_id=shop_id)
        if category_ids:
            qs = qs.filter(product__category_id__in=category_ids)

        rows = (
            qs
            .annotate(week=TruncWeek("date"))
            .values("week")
            .annotate(
                total=Coalesce(
                    Sum(F("quantity") * F("product__price"), output_field=DecimalField()),
                    Decimal(0),
                    output_field=DecimalField(),
                )
            )
            .order_by("week")
        )
        return {row["week"]: row["total"] for row in rows}

    @staticmethod
    def _forecast_revenue(
        date_from: date,
        date_to: date,
        shop_id: str | None,
        category_ids: list | None,
    ) -> dict[date, Decimal]:
        qs = ForecastEntry.objects.filter(date__gte=date_from, date__lte=date_to)
        if shop_id:
            qs = qs.filter(shop_id=shop_id)
        if category_ids:
            qs = qs.filter(product__category_id__in=category_ids)

        rows = (
            qs
            .annotate(week=TruncWeek("date"))
            .values("week")
            .annotate(
                total=Coalesce(
                    Sum(F("predicted_qty") * F("product__price"), output_field=DecimalField()),
                    Decimal(0),
                    output_field=DecimalField(),
                )
            )
            .order_by("week")
        )
        return {row["week"]: row["total"] for row in rows}
