"""
POST /api/supplies/dispatch/

Отправка поставки с страницы «Поставки»:
переводит все линии группы (shop, dispatch_date) из ready_to_ship → in_transit.
Списание остатков партии выполняется через BatchShipment.save().

Body: { "shop_id": "<uuid>", "dispatch_date": "YYYY-MM-DD" }
"""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import BatchShipment, Shop
from core.views.supplies_common import (
    active_shipments_qs,
    dispatch_date_expr,
    validate_shop,
)


class SuppliesDispatchSerializer(serializers.Serializer):
    shop_id = serializers.UUIDField()
    dispatch_date = serializers.DateField()


class SuppliesDispatchView(APIView):
    def post(self, request: Request) -> Response:
        payload = SuppliesDispatchSerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        shop_id = str(payload.validated_data["shop_id"])
        dispatch_date = payload.validated_data["dispatch_date"]

        validate_shop(shop_id)
        shop = get_object_or_404(Shop, pk=shop_id)

        lines = list(
            active_shipments_qs()
            .filter(shop_id=shop_id, status=BatchShipment.Status.READY_TO_SHIP)
            .annotate(dispatch_date=dispatch_date_expr())
            .filter(dispatch_date=dispatch_date)
            .select_related("batch__product")
        )

        if not lines:
            raise NotFound(
                f"Для магазина «{shop.name}» нет поставок «готов к отправке» "
                f"на {dispatch_date.isoformat()}."
            )

        dispatched_count = 0
        with transaction.atomic():
            for line in lines:
                line.status = BatchShipment.Status.IN_TRANSIT
                line.save()  # триггерит списание batch.quantity_remaining
                dispatched_count += 1

        return Response({
            "shop_id": shop_id,
            "shop_name": shop.name,
            "dispatch_date": dispatch_date.isoformat(),
            "dispatched_count": dispatched_count,
        })
