from datetime import date, timedelta

from django.db.models import Sum
from django.db.models.functions import Coalesce, TruncWeek
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import ForecastEntry, Sales
from core.views.sales_common import resolve_category_ids, resolve_period, validate_shop

CHART_WEEKS = 26


class DemandWeekPointSerializer(serializers.Serializer):
    week_start = serializers.DateField(help_text="Понедельник недели")
    actual = serializers.IntegerField(help_text="Фактические продажи, шт.")
    forecast = serializers.IntegerField(
        allow_null=True,
        help_text="Прогноз продаж, шт. (null — нет данных)",
    )


class DemandChartResponseSerializer(serializers.Serializer):
    unit = serializers.CharField(help_text="Единица измерения")
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    points = DemandWeekPointSerializer(many=True)
    filters = serializers.DictField(help_text="Применённые фильтры")


class ForecastDemandChartView(APIView):
    """
    GET /api/forecast/demand-chart/?shop=<uuid>&category=<uuid>&period=last_7_days

    Понедельные данные за последние 26 недель:
      actual   — фактические продажи (шт.)
      forecast — прогнозируемый спрос (шт.)
    """

    def get(self, request: Request) -> Response:
        period = resolve_period(
            request.query_params.get("period"),
            request.query_params.get("date_from"),
            request.query_params.get("date_to"),
        )
        shop_id = request.query_params.get("shop")
        category_id = request.query_params.get("category")

        validate_shop(shop_id)
        category_ids = resolve_category_ids(category_id)

        today = date.today()
        chart_start = today - timedelta(weeks=CHART_WEEKS)
        chart_start -= timedelta(days=chart_start.weekday())

        actual_map = self._actual_qty(chart_start, today, shop_id, category_ids)
        forecast_map = self._forecast_qty(chart_start, today, shop_id, category_ids)

        points = []
        cursor = chart_start
        while cursor <= today:
            points.append({
                "week_start": cursor,
                "actual": actual_map.get(cursor, 0),
                "forecast": forecast_map.get(cursor),
            })
            cursor += timedelta(weeks=1)

        data = {
            "unit": "шт.",
            "period_start": chart_start,
            "period_end": today,
            "points": points,
            "filters": {
                "shop": shop_id,
                "category": category_id,
                "period": period.code,
            },
        }

        serializer = DemandChartResponseSerializer(data)
        return Response(serializer.data)

    @staticmethod
    def _actual_qty(
        date_from: date,
        date_to: date,
        shop_id: str | None,
        category_ids: list | None,
    ) -> dict[date, int]:
        qs = Sales.objects.filter(date__gte=date_from, date__lte=date_to)
        if shop_id:
            qs = qs.filter(shop_id=shop_id)
        if category_ids:
            qs = qs.filter(product__category_id__in=category_ids)

        rows = (
            qs
            .annotate(week=TruncWeek("date"))
            .values("week")
            .annotate(total=Coalesce(Sum("quantity"), 0))
            .order_by("week")
        )
        return {row["week"]: row["total"] for row in rows}

    @staticmethod
    def _forecast_qty(
        date_from: date,
        date_to: date,
        shop_id: str | None,
        category_ids: list | None,
    ) -> dict[date, int | None]:
        qs = ForecastEntry.objects.filter(date__gte=date_from, date__lte=date_to)
        if shop_id:
            qs = qs.filter(shop_id=shop_id)
        if category_ids:
            qs = qs.filter(product__category_id__in=category_ids)

        rows = (
            qs
            .annotate(week=TruncWeek("date"))
            .values("week")
            .annotate(total=Coalesce(Sum("predicted_qty"), 0))
            .order_by("week")
        )
        return {row["week"]: row["total"] for row in rows}
