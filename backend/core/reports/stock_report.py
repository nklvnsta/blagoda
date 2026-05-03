"""
Отчёт по остаткам.

Период игнорируется — отчёт показывает срез «на сейчас» из Inventory.
Разделы:
  1. Сводка (всего позиций, в дефиците, в избытке, в норме).
  2. Дефицитные позиции (current_qty < min_stock).
  3. Избыточные позиции (current_qty > max_stock).
  4. Все остатки.
"""

from datetime import datetime

from core.models import Inventory
from core.reports.base import (
    ReportBuilder,
    ReportColumn,
    ReportData,
    ReportSection,
)


class StockReport(ReportBuilder):
    kind = "stock"
    title = "Отчет по остаткам"

    def build(self) -> ReportData:
        qs = (
            Inventory.objects.select_related("product", "product__category", "shop")
            .order_by("shop__name", "product__name")
        )
        if self.shop_id:
            qs = qs.filter(shop_id=self.shop_id)

        inventories = list(qs)

        deficit_rows: list[dict] = []
        surplus_rows: list[dict] = []
        all_rows: list[dict] = []
        normal_count = 0

        for inv in inventories:
            row = {
                "shop_name": inv.shop.name,
                "product_name": inv.product.name,
                "sku": inv.product.sku or "",
                "category_name": inv.product.category.name if inv.product.category else "",
                "current_qty": inv.current_qty,
                "min_stock": inv.min_stock,
                "max_stock": inv.max_stock,
                "deficit": inv.deficit,
                "surplus": inv.surplus,
                "unit": inv.product.unit or "",
            }
            all_rows.append(row)
            if inv.deficit > 0:
                deficit_rows.append(row)
            elif inv.surplus > 0:
                surplus_rows.append(row)
            else:
                normal_count += 1

        deficit_rows.sort(key=lambda r: r["deficit"], reverse=True)
        surplus_rows.sort(key=lambda r: r["surplus"], reverse=True)

        sections = [
            self._summary_section(
                total=len(all_rows),
                deficit=len(deficit_rows),
                surplus=len(surplus_rows),
                normal=normal_count,
            ),
            self._deficit_section(deficit_rows),
            self._surplus_section(surplus_rows),
            self._all_section(all_rows),
        ]

        return ReportData(
            title=self.title,
            period_label=f"На {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            shop_label=self._shop_label(),
            sections=sections,
            generated_at=datetime.now(),
        )

    def _summary_section(self, *, total: int, deficit: int, surplus: int, normal: int) -> ReportSection:
        return ReportSection(
            title="Сводка по остаткам",
            columns=[
                ReportColumn("name", "Показатель", align="left", width=44),
                ReportColumn("value", "Значение", align="right", width=20),
            ],
            rows=[
                {"name": "Всего позиций", "value": total},
                {"name": "В дефиците", "value": deficit},
                {"name": "В избытке", "value": surplus},
                {"name": "В норме", "value": normal},
            ],
        )

    def _common_columns(self) -> list[ReportColumn]:
        return [
            ReportColumn("shop_name", "Магазин", align="left", width=24),
            ReportColumn("product_name", "Товар", align="left", width=36),
            ReportColumn("sku", "SKU", align="left", width=14),
            ReportColumn("category_name", "Категория", align="left", width=20),
            ReportColumn("current_qty", "Остаток", align="right", width=12),
            ReportColumn("unit", "Ед.", align="left", width=8),
            ReportColumn("min_stock", "Мин.", align="right", width=10),
            ReportColumn("max_stock", "Макс.", align="right", width=10),
        ]

    def _deficit_section(self, rows: list[dict]) -> ReportSection:
        cols = self._common_columns() + [
            ReportColumn("deficit", "Дефицит", align="right", width=12),
        ]
        total_deficit = sum(r["deficit"] for r in rows)
        return ReportSection(
            title="Дефицитные позиции",
            columns=cols,
            rows=rows,
            totals={
                "shop_name": "",
                "product_name": "Итого",
                "sku": "",
                "category_name": "",
                "current_qty": "",
                "unit": "",
                "min_stock": "",
                "max_stock": "",
                "deficit": total_deficit,
            },
            note=("Нет позиций в дефиците" if not rows else None),
        )

    def _surplus_section(self, rows: list[dict]) -> ReportSection:
        cols = self._common_columns() + [
            ReportColumn("surplus", "Избыток", align="right", width=12),
        ]
        total_surplus = sum(r["surplus"] for r in rows)
        return ReportSection(
            title="Избыточные позиции",
            columns=cols,
            rows=rows,
            totals={
                "shop_name": "",
                "product_name": "Итого",
                "sku": "",
                "category_name": "",
                "current_qty": "",
                "unit": "",
                "min_stock": "",
                "max_stock": "",
                "surplus": total_surplus,
            },
            note=("Нет позиций в избытке" if not rows else None),
        )

    def _all_section(self, rows: list[dict]) -> ReportSection:
        return ReportSection(
            title="Все остатки",
            columns=self._common_columns()
            + [
                ReportColumn("deficit", "Дефицит", align="right", width=12),
                ReportColumn("surplus", "Избыток", align="right", width=12),
            ],
            rows=rows,
        )
