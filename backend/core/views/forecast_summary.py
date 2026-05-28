from django.db.models import Sum
from django.db.models.functions import Coalesce
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import ForecastEntry
from core.views.forecast_chart_metrics import compute_chart_accuracy_pct
from core.views.sales_common import resolve_category_ids, resolve_period, validate_shop


class ForecastSummaryResponseSerializer(serializers.Serializer):
    expected_sales = serializers.IntegerField(help_text="Ожидаемые продажи, шт.")
    expected_sales_unit = serializers.CharField()
    accuracy_pct = serializers.FloatField(help_text="Точность прогноза по дневным суммам (как на графике), %")
    total_forecasts = serializers.IntegerField(help_text="Кол-во дней, учтённых в расчёте точности")
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    period_code = serializers.CharField()
    period_label = serializers.CharField()
    filters = serializers.DictField(help_text="Применённые фильтры")


class ForecastSummaryView(APIView):
    """
    GET /api/forecast/summary/?shop=<uuid>&category=<uuid>&period=last_7_days

    KPI для экрана "Прогноз спроса":
      - ожидаемые продажи (сумма predicted_qty за период)
      - точность прогноза по дневным суммам факт/прогноз (как на графике demand-chart)
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

        base_qs = ForecastEntry.objects.filter(
            date__gte=period.date_from,
            date__lte=period.date_to,
        )
        if shop_id:
            base_qs = base_qs.filter(shop_id=shop_id)
        if category_ids:
            base_qs = base_qs.filter(product__category_id__in=category_ids)

        expected_sales = base_qs.aggregate(
            total=Coalesce(Sum("predicted_qty"), 0),
        )["total"]

        accuracy, days_count = compute_chart_accuracy_pct(
            period.date_from,
            period.date_to,
            shop_id,
            category_ids,
        )

        data = {
            "expected_sales": expected_sales,
            "expected_sales_unit": "шт.",
            "accuracy_pct": accuracy,
            "total_forecasts": days_count,
            "period_start": period.date_from,
            "period_end": period.date_to,
            "period_code": period.code,
            "period_label": period.label,
            "filters": {
                "shop": shop_id,
                "category": category_id,
                "period": period.code,
                "date_from": period.date_from.isoformat(),
                "date_to": period.date_to.isoformat(),
            },
        }

        serializer = ForecastSummaryResponseSerializer(data)
        return Response(serializer.data)
