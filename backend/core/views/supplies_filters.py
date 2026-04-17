"""
GET /api/supplies/filters/

Лёгкий эндпоинт для фильтров страницы «Поставки»:
возвращает список активных магазинов для выпадающего списка «Магазин / Вся сеть».
"""

from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Shop


class ShopOptionSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()


class SuppliesFiltersResponseSerializer(serializers.Serializer):
    shops = ShopOptionSerializer(many=True)


class SuppliesFiltersView(APIView):
    def get(self, request: Request) -> Response:
        shops = [
            {"id": str(shop.id), "name": shop.name}
            for shop in Shop.objects.filter(is_active=True).order_by("name")
        ]
        return Response(SuppliesFiltersResponseSerializer({"shops": shops}).data)
