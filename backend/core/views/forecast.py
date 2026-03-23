from datetime import date, timedelta

from django.db.models import Avg, F, FloatField, Case, When, Value
from django.db.models.functions import Abs, Coalesce
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import ForecastEntry, Shop, Category


class ForecastAccuracyResponseSerializer(serializers.Serializer):
    accuracy_pct = serializers.FloatField(help_text="Точность прогноза, %")
    period_start = serializers.DateField()
    period_end   = serializers.DateField()
    total_forecasts = serializers.IntegerField(help_text="Кол-во прогнозов с фактом")
    filters      = serializers.DictField(help_text="Применённые фильтры")


def _default_period() -> tuple[date, date]:
    today = date.today()
    return today - timedelta(days=30), today


def _parse_date(value: str | None, default: date) -> date:
    if not value:
        return default
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValidationError({"date": f"Неверный формат даты: {value}. Ожидается YYYY-MM-DD."})


def _get_descendant_ids(category: Category) -> list:
    ids = [category.pk]
    for child in Category.objects.filter(parent=category):
        ids.extend(_get_descendant_ids(child))
    return ids


class ForecastAccuracyView(APIView):
    """
    GET /api/dashboard/forecast-accuracy/?date_from=&date_to=&shop=<uuid>&category=<uuid>

    Точность прогноза = 1 - avg(|actual - predicted| / actual) по всем записям.
    Возвращает процент (0–100).

    Query params (все опциональные):
      date_from  — начало периода (YYYY-MM-DD), по умолчанию 30 дней назад
      date_to    — конец периода (YYYY-MM-DD), по умолчанию сегодня
      shop       — UUID магазина
      category   — UUID категории (включая дочерние)
    """

    def get(self, request: Request) -> Response:
        default_from, default_to = _default_period()

        date_from   = _parse_date(request.query_params.get("date_from"), default_from)
        date_to     = _parse_date(request.query_params.get("date_to"), default_to)
        shop_id     = request.query_params.get("shop")
        category_id = request.query_params.get("category")

        if date_from > date_to:
            raise ValidationError({"date": "date_from не может быть позже date_to."})

        qs = ForecastEntry.objects.filter(
            date__gte=date_from,
            date__lte=date_to,
            actual_qty__isnull=False,
            actual_qty__gt=0,
        )

        if shop_id:
            if not Shop.objects.filter(pk=shop_id).exists():
                raise ValidationError({"shop": f"Магазин с id={shop_id} не найден."})
            qs = qs.filter(shop_id=shop_id)

        if category_id:
            try:
                category = Category.objects.get(pk=category_id)
            except Category.DoesNotExist:
                raise ValidationError({"category": f"Категория с id={category_id} не найдена."})
            qs = qs.filter(product__category_id__in=_get_descendant_ids(category))

        result = qs.aggregate(
            mean_error=Coalesce(
                Avg(
                    Abs(F("actual_qty") - F("predicted_qty")) * 1.0 / F("actual_qty"),
                    output_field=FloatField(),
                ),
                0.0,
                output_field=FloatField(),
            ),
            count=Coalesce(
                Avg(Value(1), output_field=FloatField()),
                Value(0.0),
            ),
        )

        total_count = qs.count()
        mean_error = result["mean_error"] or 0.0
        accuracy = round(max(0.0, (1.0 - mean_error)) * 100, 1)

        data = {
            "accuracy_pct":   accuracy,
            "period_start":   date_from,
            "period_end":     date_to,
            "total_forecasts": total_count,
            "filters": {
                "shop":     shop_id,
                "category": category_id,
            },
        }

        serializer = ForecastAccuracyResponseSerializer(data)
        return Response(serializer.data)
