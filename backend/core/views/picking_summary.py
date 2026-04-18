"""
GET /api/picking/summary/?shop=<uuid>

KPI для шапки страницы «Сбор заказа»:
  total_shops        — всего магазинов к сборке на сегодня
  picked_count       — из них «собрано полностью»
  partial_count      — «собрано частично»
  in_progress_count  — «в сборке»
  not_started_count  — «не начато»
"""

from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.views.picking_common import (
    picking_group_qs,
    row_from_picking_group,
    today_picking_qs,
)
from core.views.sales_common import validate_shop


class PickingSummaryResponseSerializer(serializers.Serializer):
    total_shops = serializers.IntegerField()
    not_started_count = serializers.IntegerField()
    in_progress_count = serializers.IntegerField()
    partial_count = serializers.IntegerField()
    picked_count = serializers.IntegerField()
    filters = serializers.DictField()


class PickingSummaryView(APIView):
    def get(self, request: Request) -> Response:
        shop_id = request.query_params.get("shop")
        validate_shop(shop_id)

        groups = picking_group_qs(today_picking_qs(shop_id=shop_id))
        rows = [row_from_picking_group(item) for item in groups]

        counters = {
            "not_started_count": 0,
            "in_progress_count": 0,
            "partial_count":     0,
            "picked_count":      0,
        }
        for r in rows:
            counters[f"{r['pick_status']}_count"] += 1

        data = {
            "total_shops": len(rows),
            **counters,
            "filters": {"shop": shop_id},
        }
        return Response(PickingSummaryResponseSerializer(data).data)
