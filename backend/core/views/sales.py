from datetime import date, timedelta

from django.db.models import F, Sum, DecimalField
from django.db.models.functions import Coalesce
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Sales, Shop, Category


class RevenueResponseSerializer(serializers.Serializer):
    revenue      = serializers.DecimalField(max_digits=14, decimal_places=2, help_text="Выручка за период")
    unit         = serializers.CharField(help_text="Валюта")
    period_start = serializers.DateField()
    period_end   = serializers.DateField()
    filters      = serializers.DictField(help_text="Применённые фильтры")


def _default_week() -> tuple[date, date]:
    today  = date.today()
    monday = today - timedelta(days=today.weekday())
    return monday, today


def _parse_date(value: str | None, default: date) -> date:
    if not value:
        return default
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError({"date": f"Неверный формат даты: {value}. Ожидается YYYY-MM-DD."})


def _get_descendant_ids(category: Category) -> list:
    """Возвращает список ID категории и всех её потомков (рекурсивно)."""
    ids = [category.pk]
    for child in Category.objects.filter(parent=category):
        ids.extend(_get_descendant_ids(child))
    return ids


def _revenue(date_from: date, date_to: date, shop_id: str | None, category_id: str | None):
    qs = Sales.objects.filter(date__gte=date_from, date__lte=date_to)

    if shop_id:
        if not Shop.objects.filter(pk=shop_id).exists():
            raise ValidationError({"shop": f"Магазин с id={shop_id} не найден."})
        qs = qs.filter(shop_id=shop_id)

    if category_id:
        try:
            category = Category.objects.get(pk=category_id)
        except Category.DoesNotExist:
            raise ValidationError({"category": f"Категория с id={category_id} не найдена."})

        category_ids = _get_descendant_ids(category)
        qs = qs.filter(product__category_id__in=category_ids)

    result = qs.aggregate(
        total=Coalesce(
            Sum(F("quantity") * F("product__price"), output_field=DecimalField()),
            0,
            output_field=DecimalField(),
        )
    )
    return result["total"]


class RevenueView(APIView):
    """
    GET /api/dashboard/revenue/?date_from=&date_to=&shop=<uuid>&category=<uuid>

    Query params (все опциональные):
      date_from  — начало периода (YYYY-MM-DD), по умолчанию понедельник текущей недели
      date_to    — конец периода (YYYY-MM-DD), по умолчанию сегодня
      shop       — UUID магазина (если не указан — вся сеть)
      category   — UUID категории (если не указана — все товары)
    """

    def get(self, request: Request) -> Response:
        default_from, default_to = _default_week()

        date_from   = _parse_date(request.query_params.get("date_from"), default_from)
        date_to     = _parse_date(request.query_params.get("date_to"), default_to)
        shop_id     = request.query_params.get("shop")
        category_id = request.query_params.get("category")

        if date_from > date_to:
            raise ValidationError({"date": "date_from не может быть позже date_to."})

        total = _revenue(date_from, date_to, shop_id, category_id)

        data = {
            "revenue":      total,
            "unit":         "руб.",
            "period_start": date_from,
            "period_end":   date_to,
            "filters": {
                "shop":     shop_id,
                "category": category_id,
            },
        }

        serializer = RevenueResponseSerializer(data)
        return Response(serializer.data)
