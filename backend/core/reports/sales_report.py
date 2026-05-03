"""
Отчёт по продажам.

Структура:
  1. Лист «Сводка KPI» — те же показатели, что в /api/sales/summary/.
  2. Лист «По магазинам» — выручка / qty / чеки по магазинам.
  3. Лист «По товарам» — продано шт. по товарам.

Логика агрегации повторяет код из sales_summary / sales_by_shops /
sales_by_products, поэтому без зависимости от их сериализаторов и без
лишнего HTTP — просто прямые запросы к Sales/Receipt.
"""

from datetime import datetime
from decimal import Decimal

from django.db.models import Count, DecimalField, F, Sum
from django.db.models.functions import Coalesce

from core.models import Receipt, Sales, Shop
from core.reports.base import (
    ReportBuilder,
    ReportColumn,
    ReportData,
    ReportSection,
)


def _q(value: Decimal | int | None) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if not isinstance(value, Decimal):
        value = Decimal(value)
    return value.quantize(Decimal("0.01"))


class SalesReport(ReportBuilder):
    kind = "sales"
    title = "Отчет по продажам"

    def build(self) -> ReportData:
        sales_qs = Sales.objects.filter(
            date__gte=self.date_from,
            date__lte=self.date_to,
        )
        receipt_qs = Receipt.objects.filter(
            created_at__date__gte=self.date_from,
            created_at__date__lte=self.date_to,
        )
        if self.shop_id:
            sales_qs = sales_qs.filter(shop_id=self.shop_id)
            receipt_qs = receipt_qs.filter(shop_id=self.shop_id)

        kpi_section = self._build_kpi_section(sales_qs, receipt_qs)
        shops_section = self._build_shops_section(sales_qs, receipt_qs)
        products_section = self._build_products_section(sales_qs)

        return ReportData(
            title=self.title,
            period_label=self._period_label(),
            shop_label=self._shop_label(),
            sections=[kpi_section, shops_section, products_section],
            generated_at=datetime.now(),
        )

    def _build_kpi_section(self, sales_qs, receipt_qs) -> ReportSection:
        totals = sales_qs.aggregate(
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
        receipts = receipt_qs.aggregate(
            count=Coalesce(Count("id", distinct=True), 0),
            amount=Coalesce(
                Sum("total_amount", output_field=DecimalField(max_digits=14, decimal_places=2)),
                Decimal("0.00"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        )

        revenue = _q(totals["revenue"])
        sold_qty = totals["sold_qty"] or 0
        days = (self.date_to - self.date_from).days + 1
        avg_daily = _q(revenue / Decimal(days)) if days else Decimal("0.00")
        receipt_count = receipts["count"] or 0
        avg_ticket = (
            _q(receipts["amount"] / Decimal(receipt_count))
            if receipt_count
            else Decimal("0.00")
        )

        rows = [
            {"name": "Выручка, руб.", "value": revenue},
            {"name": "Продано, шт.", "value": sold_qty},
            {"name": "Чеков", "value": receipt_count},
            {"name": "Средний чек, руб.", "value": avg_ticket},
            {"name": "Средняя выручка в день, руб.", "value": avg_daily},
            {"name": "Дней в периоде", "value": days},
        ]
        return ReportSection(
            title="Сводка",
            columns=[
                ReportColumn("name", "Показатель", align="left", width=44),
                ReportColumn("value", "Значение", align="right", width=20),
            ],
            rows=rows,
        )

    def _build_shops_section(self, sales_qs, receipt_qs) -> ReportSection:
        rows: list[dict] = []
        total_revenue = Decimal("0.00")
        total_qty = 0
        total_receipts = 0

        shops_qs = Shop.objects.filter(is_active=True).order_by("name")
        if self.shop_id:
            shops_qs = shops_qs.filter(pk=self.shop_id)

        for shop in shops_qs:
            shop_sales = sales_qs.filter(shop_id=shop.pk).aggregate(
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
            shop_receipts = (
                receipt_qs.filter(shop_id=shop.pk).aggregate(
                    count=Coalesce(Count("id", distinct=True), 0),
                )["count"]
                or 0
            )
            revenue = _q(shop_sales["revenue"])
            qty = shop_sales["sold_qty"] or 0
            if revenue == Decimal("0.00") and qty == 0 and shop_receipts == 0:
                continue
            rows.append({
                "shop_name": shop.name,
                "revenue": revenue,
                "sold_qty": qty,
                "receipt_count": shop_receipts,
            })
            total_revenue += revenue
            total_qty += qty
            total_receipts += shop_receipts

        rows.sort(key=lambda r: r["revenue"], reverse=True)

        totals = {
            "shop_name": "Итого",
            "revenue": _q(total_revenue),
            "sold_qty": total_qty,
            "receipt_count": total_receipts,
        }

        return ReportSection(
            title="Продажи по магазинам",
            columns=[
                ReportColumn("shop_name", "Магазин", align="left", width=36),
                ReportColumn("revenue", "Выручка, руб.", align="right", width=18, is_money=True),
                ReportColumn("sold_qty", "Продано, шт.", align="right", width=16),
                ReportColumn("receipt_count", "Чеков", align="right", width=12),
            ],
            rows=rows,
            totals=totals,
        )

    def _build_products_section(self, sales_qs) -> ReportSection:
        agg = (
            sales_qs.values(
                "product_id",
                "product__name",
                "product__sku",
                "product__category__name",
                "product__unit",
            )
            .annotate(
                sold_qty=Coalesce(Sum("quantity"), 0),
                revenue=Coalesce(
                    Sum(
                        F("quantity") * F("product__price"),
                        output_field=DecimalField(max_digits=14, decimal_places=2),
                    ),
                    Decimal("0.00"),
                    output_field=DecimalField(max_digits=14, decimal_places=2),
                ),
            )
            .order_by("-revenue", "product__name")
        )

        rows: list[dict] = []
        total_qty = 0
        total_revenue = Decimal("0.00")
        for row in agg:
            qty = row["sold_qty"] or 0
            revenue = _q(row["revenue"])
            rows.append({
                "sku": row["product__sku"] or "",
                "product_name": row["product__name"],
                "category_name": row["product__category__name"] or "",
                "sold_qty": qty,
                "unit": row["product__unit"] or "",
                "revenue": revenue,
            })
            total_qty += qty
            total_revenue += revenue

        return ReportSection(
            title="Продажи по товарам",
            columns=[
                ReportColumn("sku", "SKU", align="left", width=14),
                ReportColumn("product_name", "Товар", align="left", width=40),
                ReportColumn("category_name", "Категория", align="left", width=24),
                ReportColumn("sold_qty", "Продано", align="right", width=12),
                ReportColumn("unit", "Ед.", align="left", width=8),
                ReportColumn("revenue", "Выручка, руб.", align="right", width=18, is_money=True),
            ],
            rows=rows,
            totals={
                "sku": "",
                "product_name": "Итого",
                "category_name": "",
                "sold_qty": total_qty,
                "unit": "",
                "revenue": _q(total_revenue),
            },
        )
