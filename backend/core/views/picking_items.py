"""
PATCH /api/picking/items/<uuid:item_id>/

Обновляет поле picked_quantity у одной строки сборки (BatchShipment).
Доступно только для строк со статусом scheduled.

Body: { "picked_quantity": <int >= 0> }
Response: { item, totals, pick_status }
"""

from datetime import date as date_cls

from django.shortcuts import get_object_or_404
from rest_framework import serializers, status as http_status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import BatchShipment
from core.views.picking_common import (
    derive_group_status,
    today_picking_qs,
)
from core.views.picking_detail import (
    PickingItemSerializer,
    PickingTotalsSerializer,
)


class PickingItemPatchSerializer(serializers.Serializer):
    picked_quantity = serializers.IntegerField(min_value=0)


class PickingItemPatchResponseSerializer(serializers.Serializer):
    item = PickingItemSerializer()
    totals = PickingTotalsSerializer()
    pick_status = serializers.CharField()


def _serialize_item(line: BatchShipment, position_no: int | None = None) -> dict:
    product = line.batch.product
    return {
        "id":               str(line.id),
        "position_no":      position_no or 0,
        "product_id":       str(product.id),
        "product_name":     product.name,
        "unit":             product.unit,
        "ordered_quantity": line.quantity_shipped or 0,
        "picked_quantity":  line.picked_quantity or 0,
        "pick_status":      line.pick_status,
    }


def _group_summary(shop_id: str, target_date: date_cls) -> tuple[dict, str]:
    """Возвращает totals и pick_status группы для (shop_id, target_date)."""
    lines = list(today_picking_qs(target_date=target_date, shop_id=shop_id))
    ordered_total = sum(l.quantity_shipped or 0 for l in lines)
    picked_total = sum(l.picked_quantity or 0 for l in lines)

    not_started = sum(1 for l in lines if (l.picked_quantity or 0) <= 0)
    picked = sum(1 for l in lines if (l.picked_quantity or 0) >= (l.quantity_shipped or 0))
    partial = sum(
        1 for l in lines
        if 0 < (l.picked_quantity or 0) < (l.quantity_shipped or 0)
    )

    pick_status = derive_group_status(len(lines), not_started, picked, partial)
    totals = {"ordered_units": ordered_total, "picked_units": picked_total}
    return totals, pick_status


class PickingItemPatchView(APIView):
    def patch(self, request: Request, item_id) -> Response:
        line = get_object_or_404(
            BatchShipment.objects.select_related("batch__product"),
            pk=item_id,
        )

        if line.status != BatchShipment.Status.SCHEDULED:
            raise ValidationError(
                {"status": "Редактировать сборку можно только у запланированных строк."}
            )

        serializer = PickingItemPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        line.picked_quantity = serializer.validated_data["picked_quantity"]
        line.save(update_fields=["picked_quantity"])

        totals, pick_status = _group_summary(str(line.shop_id), date_cls.today())

        payload = {
            "item":   _serialize_item(line),
            "totals": totals,
            "pick_status": pick_status,
        }
        return Response(
            PickingItemPatchResponseSerializer(payload).data,
            status=http_status.HTTP_200_OK,
        )
