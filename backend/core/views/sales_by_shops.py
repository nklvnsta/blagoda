from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Count, DecimalField, F, Sum
from django.db.models.functions import Coalesce
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Receipt, Sales, Shop
from core.views.sales_common import resolve_category_ids, resolve_period, validate_shop


class ShopSalesRowSerializer(serializers.Serializer):
    shop_id = serializers.CharField(help_text="UUID магазина")
    shop_name = serializers.CharField(help_text="Название магазина")
    revenue = serializers.DecimalField(max_digits=14, decimal_places=2, help_text="Выручка, руб.")
    sold_qty = serializers.IntegerField(help_text="Продано, шт.")
    receipt_count = serializers.IntegerField(help_text="Количество чеков")


class SalesByShopsResponseSerializer(serializers.Serializer):
    currency = serializers.CharField(help_text="Единица измерения выручки")
    quantity_unit = serializers.CharField(help_text="Единица измерения количества")
    rows = ShopSalesRowSerializer(many=True)
    total = ShopSalesRowSerializer(help_text="Итого по всем магазинам")
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    period_code = serializers.CharField()
    period_label = serializers.CharField()
    filters = serializers.DictField(help_text="Применённые фильтры")


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class SalesByShopsView(APIView):
    """
    GET /api/sales/by-shops/?period=&date_from=&date_to=&category=<uuid>

    Возвращает таблицу с данными продаж по магазинам:
      - выручка
      - продано, шт.
      - количество чеков
    """

    def get(self, request: Request) -> Response:
        period = resolve_period(
            request.query_params.get("period"),
            request.query_params.get("date_from"),
            request.query_params.get("date_to"),
        )
        category_id = request.query_params.get("category")
        category_ids = resolve_category_ids(category_id)

        # Получаем все активные магазины
        shops = Shop.objects.filter(is_active=True).order_by("name")

        rows = []
        total_revenue = Decimal("0.00")
        total_sold_qty = 0
        total_receipt_count = 0

        for shop in shops:
            sales_qs = Sales.objects.filter(
                shop=shop,
                date__gte=period.date_from,
                date__lte=period.date_to,
            )
            if category_ids:
                sales_qs = sales_qs.filter(product__category_id__in=category_ids)

            sales_totals = sales_qs.aggregate(
                revenue=Coalesce(
                    Sum(
                        F("quantity") * F("product__price"),
                        output_field=DecimalField(max_digits=14, decimal_places=2),
                    ),
                    Decimal("0.00"),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
                sold_qty=Coalesce(Sum("quantity"), 0),
            )

            receipt_qs = Receipt.objects.filter(
                shop=shop,
                created_at__date__gte=period.date_from,
                created_at__date__lte=period.date_to,
            )
            if category_ids:
                receipt_qs = receipt_qs.filter(sales__product__category_id__in=category_ids)

            receipt_count = receipt_qs.values("id").distinct().count()

            revenue = sales_totals["revenue"]
            sold_qty = sales_totals["sold_qty"] or 0

            rows.append({
                "shop_id": str(shop.id),
                "shop_name": shop.name,
                "revenue": quantize_money(revenue),
                "sold_qty": sold_qty,
                "receipt_count": receipt_count,
            })

            total_revenue += revenue
            total_sold_qty += sold_qty
            total_receipt_count += receipt_count

        # Сортируем по выручке (убывание)
        rows.sort(key=lambda x: x["revenue"], reverse=True)

        data = {
            "currency": "руб.",
            "quantity_unit": "шт.",
            "rows": rows,
            "total": {
                "shop_id": "",
                "shop_name": "Итого",
                "revenue": quantize_money(total_revenue),
                "sold_qty": total_sold_qty,
                "receipt_count": total_receipt_count,
            },
            "period_start": period.date_from,
            "period_end": period.date_to,
            "period_code": period.code,
            "period_label": period.label,
            "filters": {
                "category": category_id,
                "period": period.code,
                "date_from": period.date_from.isoformat(),
                "date_to": period.date_to.isoformat(),
            },
        }

        serializer = SalesByShopsResponseSerializer(data)
        return Response(serializer.data)
