"""
GET /api/supplies/in-transit/?shop=<uuid>&limit=3

Панель «В пути» на странице «Поставки».

Группирует линии `in_transit` по (shop, dispatch_date) и возвращает
сколько позиций сейчас едет в каждый магазин.
"""

from django.db.models import Count
from django.db.models.functions import Coalesce, TruncDate
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import BatchShipment
from core.views.supplies_common import active_shipments_qs, validate_shop


class InTransitRowSerializer(serializers.Serializer):
    shop_id = serializers.CharField()
    shop_name = serializers.CharField()
    dispatch_date = serializers.DateField()
    positions_count = serializers.IntegerField()
    status = serializers.CharField()


class SuppliesInTransitResponseSerializer(serializers.Serializer):
    rows = InTransitRowSerializer(many=True)
    total_deliveries = serializers.IntegerField()
    total_positions = serializers.IntegerField()
    filters = serializers.DictField()


class SuppliesInTransitView(APIView):
    def get(self, request: Request) -> Response:
        shop_id = request.query_params.get("shop")
        validate_shop(shop_id)

        try:
            limit = int(request.query_params.get("limit", "3"))
        except (TypeError, ValueError):
            limit = 3
        limit = max(1, min(limit, 50))

        qs = active_shipments_qs().filter(status=BatchShipment.Status.IN_TRANSIT)
        if shop_id:
            qs = qs.filter(shop_id=shop_id)

        aggregated = (
            qs.annotate(dispatch_date=Coalesce("planned_dispatch_date", TruncDate("shipped_at")))
              .values("shop_id", "shop__name", "dispatch_date")
              .annotate(positions_count=Count("id"))
              .order_by("-dispatch_date", "shop__name")
        )

        rows_all = [
            {
                "shop_id": str(item["shop_id"]),
                "shop_name": item["shop__name"],
                "dispatch_date": item["dispatch_date"],
                "positions_count": item["positions_count"],
                "status": BatchShipment.Status.IN_TRANSIT,
            }
            for item in aggregated
        ]

        data = {
            "rows": rows_all[:limit],
            "total_deliveries": len(rows_all),
            "total_positions": sum(r["positions_count"] for r in rows_all),
            "filters": {
                "shop": shop_id,
                "limit": limit,
            },
        }
        return Response(SuppliesInTransitResponseSerializer(data).data)
