"""
Bulk-операции для одной сборки (магазин, dispatch_date=today):

  POST /api/picking/<uuid:shop_id>/save/
    Bulk-обновление picked_quantity по списку items.
    Body: { "items": [ { "id": "<uuid>", "picked_quantity": <int>=0 }, ... ] }

  POST /api/picking/<uuid:shop_id>/dispatch/
    Завершение сборки: переводит все scheduled-строки группы:
      picked_quantity == 0  → status = cancelled
      picked_quantity > 0   → quantity_shipped := picked_quantity, status = ready_to_ship
    Списание остатков партии происходит позже при отправке с страницы «Поставки».
"""

from datetime import date as date_cls

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import BatchShipment, Shop
from core.views.picking_common import today_picking_qs
from core.views.picking_items import _group_summary


# ── /save/ ───────────────────────────────────────────────────────────────────

class PickingItemPayloadSerializer(serializers.Serializer):
    id = serializers.CharField()
    picked_quantity = serializers.IntegerField(min_value=0)


class PickingBulkSaveSerializer(serializers.Serializer):
    items = PickingItemPayloadSerializer(many=True)


class PickingBulkSaveResponseSerializer(serializers.Serializer):
    updated_count = serializers.IntegerField()
    totals = serializers.DictField()
    pick_status = serializers.CharField()


class PickingSaveView(APIView):
    def post(self, request: Request, shop_id) -> Response:
        get_object_or_404(Shop, pk=shop_id)
        target_date = date_cls.today()

        payload = PickingBulkSaveSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        items = payload.validated_data["items"]

        if not items:
            totals, pick_status = _group_summary(str(shop_id), target_date)
            return Response({
                "updated_count": 0,
                "totals": totals,
                "pick_status": pick_status,
            })

        ids = [it["id"] for it in items]
        qty_by_id = {it["id"]: it["picked_quantity"] for it in items}

        scheduled_qs = (
            today_picking_qs(target_date=target_date, shop_id=str(shop_id))
            .filter(pk__in=ids)
        )
        existing_ids = {str(line.pk): line for line in scheduled_qs}

        unknown = [i for i in ids if i not in existing_ids]
        if unknown:
            raise ValidationError({
                "items": (
                    f"Строки {unknown} не относятся к сборке магазина {shop_id} "
                    f"на {target_date.isoformat()} или не находятся в статусе scheduled."
                )
            })

        with transaction.atomic():
            for line_id, line in existing_ids.items():
                line.picked_quantity = qty_by_id[line_id]
                line.save(update_fields=["picked_quantity"])

        totals, pick_status = _group_summary(str(shop_id), target_date)
        return Response(PickingBulkSaveResponseSerializer({
            "updated_count": len(existing_ids),
            "totals": totals,
            "pick_status": pick_status,
        }).data)


# ── /dispatch/ ───────────────────────────────────────────────────────────────

class PickingDispatchView(APIView):
    def post(self, request: Request, shop_id) -> Response:
        shop = get_object_or_404(Shop, pk=shop_id)
        target_date = date_cls.today()

        scheduled_lines = list(
            today_picking_qs(target_date=target_date, shop_id=str(shop.id))
            .select_related("batch__product")
        )
        if not scheduled_lines:
            raise NotFound(
                f"Для магазина {shop.name} нет запланированных строк на {target_date.isoformat()}."
            )

        cancelled_count = 0
        dispatched_count = 0
        with transaction.atomic():
            for line in scheduled_lines:
                pq = line.picked_quantity or 0
                if pq == 0:
                    line.status = BatchShipment.Status.CANCELLED
                    line.save(update_fields=["status"])
                    cancelled_count += 1
                else:
                    line.quantity_shipped = pq
                    line.status = BatchShipment.Status.READY_TO_SHIP
                    line.save(update_fields=["quantity_shipped", "status"])
                    dispatched_count += 1

        return Response({
            "shop": {"id": str(shop.id), "name": shop.name},
            "dispatch_date": target_date,
            "ready_count": dispatched_count,
            "cancelled_count": cancelled_count,
        })
