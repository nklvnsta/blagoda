from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Count, DecimalField, F, Sum
from django.db.models.functions import Coalesce, TruncDate
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Receipt, Sales
from core.views.sales_common import resolve_category_ids, resolve_period, validate_shop


class DailyRevenuePointSerializer(serializers.Serializer):
    date = serializers.DateField(help_text="Дата")
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2, help_text="Выручка, руб.")
    avg_ticket = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        allow_null=True,
        help_text="Средний чек, руб."
    )


class SalesRevenueChartResponseSerializer(serializers.Serializer):
    unit = serializers.CharField(help_text="Единица измерения выручки")
    average_unit = serializers.CharField(help_text="Единица измерения среднего чека")
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    points = DailyRevenuePointSerializer(many=True)
    filters = serializers.DictField(help_text="Применённые фильтры")


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class SalesRevenueChartView(APIView):
    """
    GET /api/sales/sales-chart/?period=&date_from=&date_to=&shop=<uuid>&category=<uuid>

    Возвращает ежедневную выручку и средний чек за выбранный период.
    Фильтры: магазин, категория, период
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

        revenue_map = self._daily_revenue(
            period.date_from,
            period.date_to,
            shop_id,
            category_ids,
        )
        avg_ticket_map = self._daily_avg_ticket(
            period.date_from,
            period.date_to,
            shop_id,
            category_ids,
        )

        points = []
        cursor = period.date_from
        while cursor <= period.date_to:
            points.append({
                "date": cursor,
                "revenue": revenue_map.get(cursor, Decimal("0.00")),
                "avg_ticket": avg_ticket_map.get(cursor),
            })
            cursor += timedelta(days=1)

        data = {
            "unit": "руб.",
            "average_unit": "руб.",
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

        serializer = SalesRevenueChartResponseSerializer(data)
        return Response(serializer.data)

    @staticmethod
    def _daily_revenue(
        date_from: object,
        date_to: object,
        shop_id: str | None,
        category_ids: list | None,
    ) -> dict:
        queryset = Sales.objects.filter(date__gte=date_from, date__lte=date_to)
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        if category_ids:
            queryset = queryset.filter(product__category_id__in=category_ids)

        rows = (
            queryset
            .values("date")
            .annotate(
                amount=Coalesce(
                    Sum(
                        F("quantity") * F("product__price"),
                        output_field=DecimalField(max_digits=14, decimal_places=2),
                    ),
                    Decimal("0.00"),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                )
            )
            .order_by("date")
        )
        return {row["date"]: row["amount"] for row in rows}

    @staticmethod
    def _daily_avg_ticket(
        date_from: object,
        date_to: object,
        shop_id: str | None,
        category_ids: list | None,
    ) -> dict:
        queryset = Receipt.objects.filter(
            date__gte=date_from,
            date__lte=date_to,
        )
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        if category_ids:
            queryset = queryset.filter(sales__product__category_id__in=category_ids)

        queryset = queryset.distinct()

        rows = (
            queryset
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(
                receipt_count=Count("id", distinct=True),
                receipt_amount=Coalesce(
                    Sum(
                        "total_amount",
                        output_field=DecimalField(max_digits=14, decimal_places=2),
                    ),
                    Decimal("0.00"),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
            )
            .order_by("day")
        )

        result = {}
        for row in rows:
            receipt_count = row["receipt_count"] or 0
            avg_ticket = (
                quantize_money(row["receipt_amount"] / Decimal(receipt_count))
                if receipt_count
                else None
            )
            result[row["day"]] = avg_ticket

        return result
