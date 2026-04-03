from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Category, Shop
from core.views.sales_common import PERIOD_PRESETS


class PeriodOptionSerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField()


class FilterDefaultsSerializer(serializers.Serializer):
    shop = serializers.UUIDField(allow_null=True)
    category = serializers.UUIDField(allow_null=True)
    period = serializers.CharField()


class ShopOptionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()


class CategoryOptionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    children = serializers.ListField(child=serializers.DictField())


class SalesFiltersResponseSerializer(serializers.Serializer):
    defaults = FilterDefaultsSerializer()
    periods = PeriodOptionSerializer(many=True)
    shops = ShopOptionSerializer(many=True)
    categories = CategoryOptionSerializer(many=True)


def build_category_tree(parent: Category | None = None) -> list[dict]:
    categories = Category.objects.filter(parent=parent).order_by("name")
    return [
        {
            "id": category.pk,
            "name": category.name,
            "children": build_category_tree(category),
        }
        for category in categories
    ]


class SalesFiltersView(APIView):
    """
    GET /api/sales/filters/

    Возвращает опции фильтров для экрана "Продажи":
      - магазины
      - дерево категорий
      - предустановленные периоды
    """

    def get(self, request: Request) -> Response:
        data = {
            "defaults": {
                "shop": None,
                "category": None,
                "period": "last_7_days",
            },
            "periods": [
                {"code": code, "label": label}
                for code, label in PERIOD_PRESETS
            ],
            "shops": list(
                Shop.objects.filter(is_active=True)
                .order_by("name")
                .values("id", "name")
            ),
            "categories": build_category_tree(),
        }

        serializer = SalesFiltersResponseSerializer(data)
        return Response(serializer.data)
