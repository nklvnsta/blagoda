"""
GET /api/picking/<uuid:shop_id>/

Детальный экран сборки магазина на сегодня:
  shop          — { id, name }
  dispatch_date — дата отгрузки
  pick_status   — общий статус группы (not_started/in_progress/partial/picked)
  totals        — { ordered_units, picked_units }
  items[]      — строки сборки (по одной на BatchShipment)
"""

from datetime import date as date_cls

from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Shop
from core.views.picking_common import (
    derive_group_status,
    today_picking_qs,
)


class PickingItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    position_no = serializers.IntegerField()
    product_id = serializers.CharField()
    product_name = serializers.CharField()
    unit = serializers.CharField()
    ordered_quantity = serializers.IntegerField()
    picked_quantity = serializers.IntegerField()
    pick_status = serializers.CharField()


class PickingShopSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()


class PickingTotalsSerializer(serializers.Serializer):
    ordered_units = serializers.IntegerField()
    picked_units = serializers.IntegerField()


class PickingDetailResponseSerializer(serializers.Serializer):
    shop = PickingShopSerializer()
    dispatch_date = serializers.DateField()
    pick_status = serializers.CharField()
    totals = PickingTotalsSerializer()
    items = PickingItemSerializer(many=True)


def build_detail_payload(shop: Shop, target_date: date_cls) -> dict:
    """Собирает ответ детального экрана для (shop, target_date)."""
    lines = list(
        today_picking_qs(target_date=target_date, shop_id=str(shop.id))
        .select_related("batch__product")
        .order_by("batch__product__name", "id")
    )

    items = []
    ordered_total = 0
    picked_total = 0
    not_started = picked = partial = 0

    for idx, line in enumerate(lines, start=1):
        ordered = line.quantity_shipped or 0
        pq = line.picked_quantity or 0
        ordered_total += ordered
        picked_total += pq

        if pq <= 0:
            not_started += 1
        elif pq >= ordered:
            picked += 1
        else:
            partial += 1

        product = line.batch.product
        items.append({
            "id":               str(line.id),
            "position_no":      idx,
            "product_id":       str(product.id),
            "product_name":     product.name,
            "unit":             product.unit,
            "ordered_quantity": ordered,
            "picked_quantity":  pq,
            "pick_status":      line.pick_status,
        })

    pick_status = derive_group_status(len(lines), not_started, picked, partial)

    return {
        "shop": {"id": str(shop.id), "name": shop.name},
        "dispatch_date": target_date,
        "pick_status": pick_status,
        "totals": {"ordered_units": ordered_total, "picked_units": picked_total},
        "items": items,
    }


class PickingDetailView(APIView):
    def get(self, request: Request, shop_id) -> Response:
        shop = get_object_or_404(Shop, pk=shop_id)
        target_date = date_cls.today()

        if not today_picking_qs(target_date=target_date, shop_id=str(shop.id)).exists():
            raise NotFound(
                f"Для магазина {shop.name} нет запланированных поставок на {target_date.isoformat()}."
            )

        payload = build_detail_payload(shop, target_date)
        return Response(PickingDetailResponseSerializer(payload).data)
