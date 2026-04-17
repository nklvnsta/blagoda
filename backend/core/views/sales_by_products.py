from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db.models import Sum
from django.db.models.functions import Coalesce

from core.models import Product, Sales
from core.views.sales_common import (
    apply_search,
    resolve_category_ids,
    resolve_period,
    resolve_sort,
    validate_shop,
)


ALLOWED_PRODUCT_SORT_FIELDS = ("product_name", "sold_qty")


class ProductSalesRowSerializer(serializers.Serializer):
    product_id = serializers.CharField(help_text="UUID товара")
    product_name = serializers.CharField(help_text="Название товара")
    category_name = serializers.CharField(help_text="Категория")
    sold_qty = serializers.IntegerField(help_text="Продано, шт.")


class SalesByProductsResponseSerializer(serializers.Serializer):
    quantity_unit = serializers.CharField(help_text="Единица измерения количества")
    rows = ProductSalesRowSerializer(many=True)
    total = ProductSalesRowSerializer(help_text="Итого")
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    period_code = serializers.CharField()
    period_label = serializers.CharField()
    filters = serializers.DictField(help_text="Применённые фильтры")


class SalesByProductsView(APIView):
    """
    GET /api/sales/by-products/?period=&date_from=&date_to=&shop=<uuid>&category=<uuid>

    Продажи по товарам: товар, продано шт., категория.
    """

    def get(self, request: Request) -> Response:
        period = resolve_period(
            request.query_params.get("period"),
            request.query_params.get("date_from"),
            request.query_params.get("date_to"),
        )
        shop_id = request.query_params.get("shop")
        category_id = request.query_params.get("category")

        validate_shop(shop_id)
        category_ids = resolve_category_ids(category_id)

        search = apply_search(request.query_params.get("search"))
        sort_field, order = resolve_sort(
            request.query_params.get("sort"),
            request.query_params.get("order"),
            allowed_fields=ALLOWED_PRODUCT_SORT_FIELDS,
            default_field="sold_qty",
            default_order="desc",
        )

        products_qs = Product.objects.filter(is_active=True).select_related("category").order_by("name")
        if category_ids:
            products_qs = products_qs.filter(category_id__in=category_ids)
        if search:
            products_qs = products_qs.filter(name__icontains=search)

        sales_qs = Sales.objects.filter(
            date__gte=period.date_from,
            date__lte=period.date_to,
        )
        if shop_id:
            sales_qs = sales_qs.filter(shop_id=shop_id)
        if category_ids:
            sales_qs = sales_qs.filter(product__category_id__in=category_ids)

        qty_by_product = {
            str(row["product_id"]): int(row["sold_qty"] or 0)
            for row in sales_qs.values("product_id").annotate(
                sold_qty=Coalesce(Sum("quantity"), 0),
            )
        }

        rows = []
        total_sold_qty = 0
        for product in products_qs:
            qty = qty_by_product.get(str(product.pk), 0)
            rows.append({
                "product_id": str(product.pk),
                "product_name": product.name,
                "category_name": product.category.name,
                "sold_qty": qty,
            })
            total_sold_qty += qty

        reverse = order == "desc"
        if sort_field == "product_name":
            rows.sort(key=lambda x: x["product_name"].lower(), reverse=reverse)
        else:
            rows.sort(key=lambda x: x[sort_field], reverse=reverse)

        data = {
            "quantity_unit": "шт.",
            "rows": rows,
            "total": {
                "product_id": "",
                "product_name": "Итого",
                "category_name": "",
                "sold_qty": total_sold_qty,
            },
            "period_start": period.date_from,
            "period_end": period.date_to,
            "period_code": period.code,
            "period_label": period.label,
            "filters": {
                "shop": shop_id,
                "category": category_id,
                "period": period.code,
                "date_from": period.date_from.isoformat(),
                "date_to": period.date_to.isoformat(),
                "search": search or None,
                "sort": sort_field,
                "order": order,
            },
        }

        serializer = SalesByProductsResponseSerializer(data)
        return Response(serializer.data)
