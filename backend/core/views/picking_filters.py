"""
GET /api/picking/filters/

Возвращает список магазинов, у которых есть scheduled-поставки на сегодня —
для дропдауна на странице «Сбор заказа».
"""

from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Shop
from core.views.picking_common import today_picking_qs


class ShopOptionSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()


class PickingFiltersResponseSerializer(serializers.Serializer):
    shops = ShopOptionSerializer(many=True)


class PickingFiltersView(APIView):
    def get(self, request: Request) -> Response:
        shop_ids = (
            today_picking_qs()
            .values_list("shop_id", flat=True)
            .distinct()
        )
        shops = [
            {"id": str(shop.id), "name": shop.name}
            for shop in Shop.objects.filter(id__in=list(shop_ids), is_active=True).order_by("name")
        ]
        return Response(PickingFiltersResponseSerializer({"shops": shops}).data)
