"""
GET /api/supplies/summary/?date=YYYY-MM-DD&shop=<uuid>

Возвращает 4 KPI для страницы «Поставки»:
  - shipped_qty_today       — сколько штук отгружено в выбранную дату
  - shipped_amount_today    — на какую сумму отгружено в выбранную дату
  - in_transit_deliveries   — сколько поставок сейчас в пути
  - tomorrow_positions      — сколько позиций запланировано к отгрузке завтра
"""

from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, F, Sum
from django.db.models.functions import Coalesce, TruncDate
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import BatchShipment
from core.views.supplies_common import (
    active_shipments_qs,
    parse_date_param,
    quantize_money,
    validate_shop,
)


class SuppliesSummaryResponseSerializer(serializers.Serializer):
    date = serializers.DateField()
    shipped_qty_today = serializers.IntegerField()
    shipped_amount_today = serializers.DecimalField(max_digits=14, decimal_places=2)
    in_transit_deliveries = serializers.IntegerField()
    tomorrow_positions = serializers.IntegerField()
    quantity_unit = serializers.CharField()
    currency = serializers.CharField()
    filters = serializers.DictField()


class SuppliesSummaryView(APIView):
    def get(self, request: Request) -> Response:
        target_date = parse_date_param(request.query_params.get("date"), date.today())
        tomorrow = target_date + timedelta(days=1)
        shop_id = request.query_params.get("shop")
        validate_shop(shop_id)

        base = active_shipments_qs()
        if shop_id:
            base = base.filter(shop_id=shop_id)

        shipped_today_qs = base.filter(
            status__in=[BatchShipment.Status.IN_TRANSIT, BatchShipment.Status.DELIVERED],
            shipped_at__date=target_date,
        )
        shipped_totals = shipped_today_qs.aggregate(
            qty=Coalesce(Sum("quantity_shipped"), 0),
            amount=Coalesce(
                Sum(
                    F("quantity_shipped") * F("batch__product__price"),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
                Decimal("0.00"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        )

        in_transit_count = (
            base.filter(status=BatchShipment.Status.IN_TRANSIT)
                .annotate(dispatch_date=Coalesce("planned_dispatch_date", TruncDate("shipped_at")))
                .values("shop_id", "dispatch_date")
                .distinct()
                .count()
        )

        tomorrow_positions = base.filter(
            status=BatchShipment.Status.SCHEDULED,
            planned_dispatch_date=tomorrow,
        ).aggregate(n=Count("id"))["n"] or 0

        data = {
            "date": target_date,
            "shipped_qty_today": shipped_totals["qty"] or 0,
            "shipped_amount_today": quantize_money(shipped_totals["amount"]),
            "in_transit_deliveries": in_transit_count,
            "tomorrow_positions": tomorrow_positions,
            "quantity_unit": "шт.",
            "currency": "руб.",
            "filters": {
                "date": target_date.isoformat(),
                "shop": shop_id,
            },
        }
        return Response(SuppliesSummaryResponseSerializer(data).data)
