"""
GET  /api/supplies/items/?shop_id=<uuid>&dispatch_date=YYYY-MM-DD
     Возвращает список отдельных линий BatchShipment для конкретной группы
     (магазин + дата отгрузки) с информацией о продукте и количестве.

PATCH /api/supplies/items/<uuid>/
     Изменяет quantity_shipped для одной линии.
     Допустимо только для линий со статусом «scheduled».
"""
from __future__ import annotations

import uuid as _uuid

from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import BatchShipment
from core.views.supplies_common import (
    active_shipments_qs,
    dispatch_date_expr,
    parse_date_param,
    validate_shop,
)


# ── Сериализаторы ─────────────────────────────────────────────────────────────

class SupplyItemSerializer(serializers.Serializer):
    id               = serializers.UUIDField()
    product_name     = serializers.CharField()
    product_sku      = serializers.CharField()
    unit             = serializers.CharField()
    quantity_shipped = serializers.IntegerField()
    price            = serializers.DecimalField(max_digits=14, decimal_places=2)
    amount           = serializers.DecimalField(max_digits=14, decimal_places=2)
    status           = serializers.CharField()
    editable         = serializers.BooleanField()


class SupplyItemPatchSerializer(serializers.Serializer):
    quantity_shipped = serializers.IntegerField(min_value=1)


# ── Хелпер ────────────────────────────────────────────────────────────────────

def _item_to_dict(line: BatchShipment) -> dict:
    price = line.batch.product.price
    qty   = line.quantity_shipped
    return {
        "id":               line.id,
        "product_name":     line.batch.product.name,
        "product_sku":      line.batch.product.sku,
        "unit":             line.batch.product.unit,
        "quantity_shipped": qty,
        "price":            price,
        "amount":           price * qty,
        "status":           line.status,
        "editable":         line.status == BatchShipment.Status.SCHEDULED,
    }


# ── GET /api/supplies/items/ ──────────────────────────────────────────────────

class SupplyItemsListView(APIView):
    """Список позиций одной группы поставок (shop + dispatch_date)."""

    def get(self, request: Request) -> Response:
        shop_id  = request.query_params.get("shop_id")
        date_raw = request.query_params.get("dispatch_date")

        if not shop_id:
            raise ValidationError({"shop_id": "Обязательный параметр."})
        if not date_raw:
            raise ValidationError({"dispatch_date": "Обязательный параметр."})

        validate_shop(shop_id)
        target_date = parse_date_param(date_raw, None, "dispatch_date")

        lines = (
            active_shipments_qs()
            .filter(shop_id=shop_id)
            .annotate(dispatch_date=dispatch_date_expr())
            .filter(dispatch_date=target_date)
            .select_related("batch__product")
            .order_by("batch__product__name")
        )

        data = [_item_to_dict(line) for line in lines]
        serializer = SupplyItemSerializer(data, many=True)
        return Response({"results": serializer.data, "count": len(data)})


# ── PATCH /api/supplies/items/<uuid>/ ─────────────────────────────────────────

class SupplyItemPatchView(APIView):
    """Изменение quantity_shipped для одной запланированной позиции."""

    def patch(self, request: Request, item_id: _uuid.UUID) -> Response:
        try:
            line = (
                BatchShipment.objects
                .select_related("batch__product")
                .get(pk=item_id)
            )
        except BatchShipment.DoesNotExist:
            raise NotFound("Позиция не найдена.")

        if line.status != BatchShipment.Status.SCHEDULED:
            raise PermissionDenied(
                f"Нельзя изменить количество: статус позиции «{line.get_status_display()}». "
                "Редактирование допустимо только для запланированных позиций."
            )

        ser = SupplyItemPatchSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        line.quantity_shipped = ser.validated_data["quantity_shipped"]
        line.save(update_fields=["quantity_shipped"])

        return Response(SupplyItemSerializer(_item_to_dict(line)).data)
