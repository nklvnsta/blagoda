"""
GET /api/supplies/scheduled/?date=YYYY-MM-DD&shop=<uuid>&limit=3

Панель «К отгрузке завтра» на странице «Поставки».

По умолчанию date = today + 1. Группирует линии со статусом `scheduled`
по магазину и возвращает сколько позиций назначено в каждый магазин.
"""

from datetime import date, timedelta

from django.db.models import Count
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import BatchShipment
from core.views.supplies_common import (
    active_shipments_qs,
    parse_date_param,
    validate_shop,
)


class ScheduledShopRowSerializer(serializers.Serializer):
    shop_id = serializers.CharField()
    shop_name = serializers.CharField()
    positions_count = serializers.IntegerField()


class SuppliesScheduledResponseSerializer(serializers.Serializer):
    date = serializers.DateField()
    rows = ScheduledShopRowSerializer(many=True)
    total_positions = serializers.IntegerField()
    total_shops = serializers.IntegerField()
    filters = serializers.DictField()


class SuppliesScheduledView(APIView):
    def get(self, request: Request) -> Response:
        target_date = parse_date_param(
            request.query_params.get("date"),
            date.today() + timedelta(days=1),
        )
        shop_id = request.query_params.get("shop")
        validate_shop(shop_id)

        try:
            limit = int(request.query_params.get("limit", "3"))
        except (TypeError, ValueError):
            limit = 3
        limit = max(1, min(limit, 50))

        qs = active_shipments_qs().filter(
            status=BatchShipment.Status.SCHEDULED,
            planned_dispatch_date=target_date,
        )
        if shop_id:
            qs = qs.filter(shop_id=shop_id)

        aggregated = (
            qs.values("shop_id", "shop__name")
              .annotate(positions_count=Count("id"))
              .order_by("-positions_count", "shop__name")
        )

        rows_all = [
            {
                "shop_id": str(item["shop_id"]),
                "shop_name": item["shop__name"],
                "positions_count": item["positions_count"],
            }
            for item in aggregated
        ]
        total_positions = sum(r["positions_count"] for r in rows_all)
        total_shops = len(rows_all)

        data = {
            "date": target_date,
            "rows": rows_all[:limit],
            "total_positions": total_positions,
            "total_shops": total_shops,
            "filters": {
                "date": target_date.isoformat(),
                "shop": shop_id,
                "limit": limit,
            },
        }
        return Response(SuppliesScheduledResponseSerializer(data).data)
