"""
GET /api/supplies/?date=YYYY-MM-DD&shop=<uuid>&page=&page_size=

Пагинируемая таблица «поставок» на странице «Поставки».

Строка таблицы — группа линий по (shop, dispatch_date) со столбцами:
  - Магазин
  - Позиций (кол-во линий в группе)
  - Сумма (руб.)
  - Статус (scheduled / in_transit / delivered)

Если в query-параметрах передана дата — таблица фильтруется по этому
dispatch_date. Иначе показываем все группы, отсортированные по убыванию даты.
"""

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import BatchShipment
from core.views.supplies_common import (
    SuppliesPagination,
    active_shipments_qs,
    grouped_deliveries_qs,
    parse_date_param,
    row_from_group,
    validate_shop,
)


ALLOWED_SORT_FIELDS = {"positions_count", "amount"}
ALLOWED_ORDERS = {"asc", "desc"}
ALLOWED_STATUSES = {
    BatchShipment.Status.SCHEDULED,
    BatchShipment.Status.READY_TO_SHIP,
    BatchShipment.Status.IN_TRANSIT,
    BatchShipment.Status.DELIVERED,
}


class SupplyRowSerializer(serializers.Serializer):
    shop_id = serializers.CharField()
    shop_name = serializers.CharField()
    dispatch_date = serializers.DateField()
    positions_count = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    status = serializers.CharField()


class SuppliesTableView(APIView):
    pagination_class = SuppliesPagination

    def get(self, request: Request) -> Response:
        date_raw = request.query_params.get("date")
        shop_id = request.query_params.get("shop")
        status_raw = request.query_params.get("status")
        sort_raw = request.query_params.get("sort")
        order_raw = (request.query_params.get("order") or "desc").lower()
        validate_shop(shop_id)

        if status_raw and status_raw not in ALLOWED_STATUSES:
            raise ValidationError(
                {"status": f"Допустимые значения: {sorted(ALLOWED_STATUSES)}"}
            )

        if sort_raw and sort_raw not in ALLOWED_SORT_FIELDS:
            raise ValidationError(
                {"sort": f"Допустимые значения: {sorted(ALLOWED_SORT_FIELDS)}"}
            )

        if order_raw not in ALLOWED_ORDERS:
            raise ValidationError(
                {"order": f"Допустимые значения: {sorted(ALLOWED_ORDERS)}"}
            )

        base = active_shipments_qs()
        if shop_id:
            base = base.filter(shop_id=shop_id)

        groups_qs = grouped_deliveries_qs(base).order_by("-dispatch_date", "shop__name")

        if date_raw:
            target_date = parse_date_param(date_raw, None, "date")
            groups_qs = groups_qs.filter(dispatch_date=target_date)

        rows = [row_from_group(item) for item in groups_qs]

        if status_raw:
            rows = [r for r in rows if r["status"] == status_raw]

        if sort_raw:
            reverse = order_raw == "desc"
            rows.sort(key=lambda r: r[sort_raw], reverse=reverse)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(rows, request, view=self)

        serializer = SupplyRowSerializer(page, many=True)
        response = paginator.get_paginated_response(serializer.data)
        response.data["currency"] = "руб."
        response.data["filters"] = {
            "date": date_raw,
            "shop": shop_id,
            "status": status_raw,
            "sort": sort_raw,
            "order": order_raw if sort_raw else None,
        }
        return response
