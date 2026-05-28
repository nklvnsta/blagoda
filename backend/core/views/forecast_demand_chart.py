from datetime import timedelta

from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.views.forecast_chart_metrics import daily_actual_qty, daily_forecast_qty
from core.views.sales_common import resolve_category_ids, resolve_period, validate_shop


class DailyDemandPointSerializer(serializers.Serializer):
    date = serializers.DateField(help_text="Дата")
    actual = serializers.IntegerField(help_text="Фактические продажи, шт.")
    forecast = serializers.IntegerField(
        allow_null=True,
        help_text="Прогноз продаж, шт. (null — нет данных)",
    )


class DemandChartResponseSerializer(serializers.Serializer):
    unit = serializers.CharField(help_text="Единица измерения")
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    points = DailyDemandPointSerializer(many=True)
    filters = serializers.DictField(help_text="Применённые фильтры")


class ForecastDemandChartView(APIView):
    """
    GET /api/forecast/demand-chart/?shop=<uuid>&category=<uuid>&period=last_7_days

    Ежедневные данные за выбранный период:
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

        actual_map = daily_actual_qty(
            period.date_from, period.date_to, shop_id, category_ids,
        )
        forecast_map = daily_forecast_qty(
            period.date_from, period.date_to, shop_id, category_ids,
        )

        points = []
        cursor = period.date_from
        while cursor <= period.date_to:
            points.append({
                "date": cursor,
                "actual": actual_map.get(cursor, 0),
                "forecast": forecast_map.get(cursor),
            })
            cursor += timedelta(days=1)

        data = {
            "unit": "шт.",
            "period_start": period.date_from,
            "period_end": period.date_to,
            "points": points,
            "filters": {
                "shop": shop_id,
                "category": category_id,
                "period": period.code,
                "date_from": period.date_from.isoformat(),
                "date_to": period.date_to.isoformat(),
            },
        }

        serializer = DemandChartResponseSerializer(data)
        return Response(serializer.data)
