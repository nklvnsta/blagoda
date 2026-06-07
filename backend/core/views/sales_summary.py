from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Count, DecimalField, F, Sum
from django.db.models.functions import Coalesce
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Receipt, Sales
from core.views.sales_common import resolve_category_ids, resolve_period, validate_shop


class SalesSummaryResponseSerializer(serializers.Serializer):
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    sold_qty = serializers.IntegerField()
    avg_ticket = serializers.DecimalField(max_digits=14, decimal_places=2)
    avg_daily_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    currency = serializers.CharField()
    quantity_unit = serializers.CharField()
    receipt_count = serializers.IntegerField(allow_null=True)
    period_code = serializers.CharField()
    period_label = serializers.CharField()
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    filters = serializers.DictField()


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class SalesSummaryView(APIView):
    """
    GET /api/sales/summary/?period=&date_from=&date_to=&shop=<uuid>&category=<uuid>

    Возвращает верхние KPI экрана "Продажи":
      - выручка
      - продано, шт.
      - средняя выручка в день
      - средний чек
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

        queryset = Sales.objects.filter(
            date__gte=period.date_from,
            date__lte=period.date_to,
        )

        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        if category_ids:
            queryset = queryset.filter(product__category_id__in=category_ids)

        totals = queryset.aggregate(
            revenue=Coalesce(
                Sum(
                    F("quantity") * F("product__price"),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
                Decimal("0.00"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
            sold_qty=Coalesce(Sum("quantity"), 0),
        )

        receipt_queryset = Receipt.objects.filter(
            date__gte=period.date_from,
            date__lte=period.date_to,
        )
        if shop_id:
            receipt_queryset = receipt_queryset.filter(shop_id=shop_id)
        if category_ids:
            receipt_queryset = receipt_queryset.filter(
                sales__product__category_id__in=category_ids,
            )

        receipt_totals = receipt_queryset.aggregate(
            receipt_count=Coalesce(Count("id", distinct=True), 0),
            receipt_amount=Coalesce(
                Sum("total_amount", output_field=DecimalField(max_digits=14, decimal_places=2)),
                Decimal("0.00"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        )

        revenue = quantize_money(totals["revenue"])
        sold_qty = totals["sold_qty"] or 0
        days_in_period = (period.date_to - period.date_from).days + 1
        avg_daily_revenue = quantize_money(revenue / Decimal(days_in_period))

        receipt_count = receipt_totals["receipt_count"] or 0
        if receipt_count:
            avg_ticket = quantize_money(
                receipt_totals["receipt_amount"] / Decimal(receipt_count),
            )
        else:
            avg_ticket = quantize_money(Decimal("0.00"))

        data = {
            "revenue": revenue,
            "sold_qty": sold_qty,
            "avg_ticket": avg_ticket,
            "avg_daily_revenue": avg_daily_revenue,
            "currency": "руб.",
            "quantity_unit": "шт.",
            "receipt_count": receipt_count,
            "period_code": period.code,
            "period_label": period.label,
            "period_start": period.date_from,
            "period_end": period.date_to,
            "filters": {
                "shop": shop_id,
                "category": category_id,
                "period": period.code,
                "date_from": period.date_from.isoformat(),
                "date_to": period.date_to.isoformat(),
            },
        }

        serializer = SalesSummaryResponseSerializer(data)
        return Response(serializer.data)
