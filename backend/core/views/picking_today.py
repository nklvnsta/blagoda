"""
GET /api/picking/today/?shop=&page=&page_size=&sort=&order=&status=

Пагинируемая таблица магазинов к сборке на сегодня.

Строка таблицы:
  shop_id, shop_name, positions_count, ordered_units, picked_units, pick_status

Параметры:
  shop    — UUID магазина (опционально)
  status  — один из not_started / in_progress / partial / picked
  sort    — shop_name | positions_count | ordered_units
  order   — asc | desc (по умолчанию asc для shop_name, иначе desc)
"""

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.views.picking_common import (
    GroupPickStatus,
    PickingPagination,
    picking_group_qs,
    row_from_picking_group,
    today_picking_qs,
)
from core.views.sales_common import apply_search, resolve_sort, validate_shop


ALLOWED_SORT_FIELDS = ("shop_name", "positions_count", "ordered_units", "picked_units")
ALLOWED_STATUSES = set(GroupPickStatus.CHOICES)


class PickingShopRowSerializer(serializers.Serializer):
    shop_id = serializers.CharField()
    shop_name = serializers.CharField()
    positions_count = serializers.IntegerField()
    ordered_units = serializers.IntegerField()
    picked_units = serializers.IntegerField()
    pick_status = serializers.CharField()


class PickingTodayView(APIView):
    pagination_class = PickingPagination

    def get(self, request: Request) -> Response:
        shop_id = request.query_params.get("shop")
        status_raw = request.query_params.get("status")
        sort_raw = request.query_params.get("sort")
        order_raw = request.query_params.get("order")
        search_raw = apply_search(request.query_params.get("search"))

        validate_shop(shop_id)

        if status_raw and status_raw not in ALLOWED_STATUSES:
            raise ValidationError(
                {"status": f"Допустимые значения: {sorted(ALLOWED_STATUSES)}"}
            )

        default_order = "asc" if (sort_raw == "shop_name" or not sort_raw) else "desc"
        sort_field, order = resolve_sort(
            sort_raw,
            order_raw,
            ALLOWED_SORT_FIELDS,
            default_field="shop_name",
            default_order=default_order,
        )

        base = today_picking_qs(shop_id=shop_id)
        if search_raw:
            base = base.filter(shop__name__icontains=search_raw)

        groups = picking_group_qs(base)
        rows = [row_from_picking_group(item) for item in groups]

        if status_raw:
            rows = [r for r in rows if r["pick_status"] == status_raw]

        rows.sort(
            key=lambda r: (r[sort_field], r["shop_name"]),
            reverse=(order == "desc"),
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(rows, request, view=self)

        serializer = PickingShopRowSerializer(page, many=True)
        response = paginator.get_paginated_response(serializer.data)
        response.data["filters"] = {
            "shop": shop_id,
            "status": status_raw,
            "search": search_raw or None,
            "sort": sort_field,
            "order": order,
        }
        return response
