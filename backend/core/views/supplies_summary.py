"""
GET /api/supplies/summary/?date=YYYY-MM-DD&shop=<uuid>

4 KPI для страницы «Поставки» на выбранную дату:
  - to_dispatch_count  — к отгрузке: кол-во поставок (distinct shop) со статусом scheduled/ready_to_ship
  - to_dispatch_amount — на сумму (руб.) для тех же поставок
  - shipped_count      — отгружено: кол-во поставок со статусом in_transit/delivered
  - shipped_amount     — на сумму (руб.) для отгружённых поставок
"""

from datetime import date
from decimal import Decimal

from django.db.models import Count, DecimalField, F, Sum
from django.db.models.functions import Coalesce
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import BatchShipment
from core.views.supplies_common import (
    active_shipments_qs,
    dispatch_date_expr,
    parse_date_param,
    quantize_money,
    validate_shop,
)


class SuppliesSummaryResponseSerializer(serializers.Serializer):
    date = serializers.DateField()
    to_dispatch_count = serializers.IntegerField()
    to_dispatch_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    shipped_count = serializers.IntegerField()
    shipped_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    currency = serializers.CharField()
    filters = serializers.DictField()


class SuppliesSummaryView(APIView):
    def get(self, request: Request) -> Response:
        target_date = parse_date_param(request.query_params.get("date"), date.today())
        shop_id = request.query_params.get("shop")
        validate_shop(shop_id)

        base = (
            active_shipments_qs()
            .annotate(dispatch_date=dispatch_date_expr())
            .filter(dispatch_date=target_date)
        )
        if shop_id:
            base = base.filter(shop_id=shop_id)

        def amount_expr():
            return Coalesce(
                Sum(
                    F("quantity_shipped") * F("batch__product__price"),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
                Decimal("0.00"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )

        to_dispatch_qs = base.filter(
            status__in=[
                BatchShipment.Status.SCHEDULED,
                BatchShipment.Status.READY_TO_SHIP,
            ]
        )
        to_dispatch = to_dispatch_qs.aggregate(
            count=Count("shop_id", distinct=True),
            amount=amount_expr(),
        )

        shipped_qs = base.filter(
            status__in=[
                BatchShipment.Status.IN_TRANSIT,
                BatchShipment.Status.DELIVERED,
            ]
        )
        shipped = shipped_qs.aggregate(
            count=Count("shop_id", distinct=True),
            amount=amount_expr(),
        )

        data = {
            "date": target_date,
            "to_dispatch_count": to_dispatch["count"] or 0,
            "to_dispatch_amount": quantize_money(to_dispatch["amount"]),
            "shipped_count": shipped["count"] or 0,
            "shipped_amount": quantize_money(shipped["amount"]),
            "currency": "руб.",
            "filters": {
                "date": target_date.isoformat(),
                "shop": shop_id,
            },
        }
        return Response(SuppliesSummaryResponseSerializer(data).data)
