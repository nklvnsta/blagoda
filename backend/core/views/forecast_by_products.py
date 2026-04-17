from datetime import timedelta

from django.db.models import Sum
from django.db.models.functions import Coalesce
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import ForecastEntry, Product, Sales
from core.views.sales_common import (
    apply_search,
    resolve_category_ids,
    resolve_period,
    resolve_sort,
    validate_shop,
)


ALLOWED_FORECAST_SORT_FIELDS = (
    "product_name",
    "forecast_qty",
    "previous_qty",
    "deviation_qty",
)


class ForecastProductRowSerializer(serializers.Serializer):
    product_id = serializers.CharField(help_text="UUID товара")
    product_name = serializers.CharField(help_text="Название товара")
    forecast_qty = serializers.IntegerField(help_text="Прогноз продаж, шт.")
    previous_qty = serializers.IntegerField(help_text="Продажи за прошлый аналогичный период, шт.")
    deviation_qty = serializers.IntegerField(help_text="Отклонение (прогноз − факт прошл.), шт.")


class ForecastByProductsResponseSerializer(serializers.Serializer):
    quantity_unit = serializers.CharField(help_text="Единица измерения")
    rows = ForecastProductRowSerializer(many=True)
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    period_code = serializers.CharField()
    period_label = serializers.CharField()
    filters = serializers.DictField(help_text="Применённые фильтры")


class ForecastByProductsView(APIView):
    """
    GET /api/forecast/by-products/?shop=<uuid>&category=<uuid>&period=last_7_days

    Таблица прогноза по товарам:
      - товар
      - прогноз продаж (сумма predicted_qty за период)
      - продажи за прошлый аналогичный период
      - отклонение = прогноз − продажи прошлого периода
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
            allowed_fields=ALLOWED_FORECAST_SORT_FIELDS,
            default_field="forecast_qty",
            default_order="desc",
        )

        period_length = (period.date_to - period.date_from).days + 1
        prev_date_to = period.date_from - timedelta(days=1)
        prev_date_from = prev_date_to - timedelta(days=period_length - 1)

        products_qs = (
            Product.objects
            .filter(is_active=True)
            .select_related("category")
            .order_by("name")
        )
        if category_ids:
            products_qs = products_qs.filter(category_id__in=category_ids)
        if search:
            products_qs = products_qs.filter(name__icontains=search)

        forecast_qs = ForecastEntry.objects.filter(
            date__gte=period.date_from,
            date__lte=period.date_to,
        )
        if shop_id:
            forecast_qs = forecast_qs.filter(shop_id=shop_id)
        if category_ids:
            forecast_qs = forecast_qs.filter(product__category_id__in=category_ids)

        forecast_by_product = {
            str(row["product_id"]): row["total"]
            for row in forecast_qs.values("product_id").annotate(
                total=Coalesce(Sum("predicted_qty"), 0),
            )
        }

        prev_sales_qs = Sales.objects.filter(
            date__gte=prev_date_from,
            date__lte=prev_date_to,
        )
        if shop_id:
            prev_sales_qs = prev_sales_qs.filter(shop_id=shop_id)
        if category_ids:
            prev_sales_qs = prev_sales_qs.filter(product__category_id__in=category_ids)

        prev_by_product = {
            str(row["product_id"]): row["total"]
            for row in prev_sales_qs.values("product_id").annotate(
                total=Coalesce(Sum("quantity"), 0),
            )
        }

        rows = []
        for product in products_qs:
            pk = str(product.pk)
            forecast_qty = forecast_by_product.get(pk, 0)
            previous_qty = prev_by_product.get(pk, 0)
            if forecast_qty == 0 and previous_qty == 0:
                continue
            rows.append({
                "product_id": pk,
                "product_name": product.name,
                "forecast_qty": forecast_qty,
                "previous_qty": previous_qty,
                "deviation_qty": forecast_qty - previous_qty,
            })

        reverse = order == "desc"
        if sort_field == "product_name":
            rows.sort(key=lambda r: r["product_name"].lower(), reverse=reverse)
        else:
            rows.sort(key=lambda r: r[sort_field], reverse=reverse)

        data = {
            "quantity_unit": "шт.",
            "rows": rows,
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

        serializer = ForecastByProductsResponseSerializer(data)
        return Response(serializer.data)
