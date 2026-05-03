"""
XYZ-анализ: оценка стабильности спроса по товарам.

Алгоритм:
1. По периоду собираем недельные продажи по каждому товару.
2. Дополняем нулями недели без продаж (важно для корректного CV).
3. Считаем среднее, стандартное отклонение и коэффициент вариации (CV).
4. Класс:
   - CV ≤ 10%             → X (стабильный спрос)
   - 10% < CV ≤ 25%       → Y (умеренный)
   - CV > 25% или mean=0  → Z (нестабильный/нерегулярный)
"""

import statistics
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Iterable

from django.db.models import Sum
from django.db.models.functions import Coalesce, TruncWeek

from core.models import Sales
from core.reports.base import (
    ReportBuilder,
    ReportColumn,
    ReportData,
    ReportSection,
)


def _classify(cv_ratio: float | None, mean: float) -> str:
    if mean <= 0 or cv_ratio is None:
        return "Z"
    if cv_ratio <= 0.10:
        return "X"
    if cv_ratio <= 0.25:
        return "Y"
    return "Z"


def _week_starts(start, end) -> list:
    """Все понедельники в [start; end]."""
    days_to_monday = (start.weekday()) % 7
    first = start - timedelta(days=days_to_monday)
    weeks = []
    cur = first
    while cur <= end:
        weeks.append(cur)
        cur += timedelta(days=7)
    return weeks


class XYZReport(ReportBuilder):
    kind = "xyz"
    title = "XYZ-анализ"

    def build(self) -> ReportData:
        qs = Sales.objects.filter(
            date__gte=self.date_from,
            date__lte=self.date_to,
        )
        if self.shop_id:
            qs = qs.filter(shop_id=self.shop_id)

        weekly = (
            qs.annotate(week=TruncWeek("date"))
            .values(
                "product_id",
                "product__name",
                "product__sku",
                "product__category__name",
                "product__unit",
                "week",
            )
            .annotate(qty=Coalesce(Sum("quantity"), 0))
            .order_by("product__name", "week")
        )

        weeks = _week_starts(self.date_from, self.date_to)
        n_weeks = len(weeks)
        week_index = {w: i for i, w in enumerate(weeks)}

        series_by_product: dict = {}
        meta_by_product: dict = {}

        for row in weekly:
            pid = row["product_id"]
            if pid not in series_by_product:
                series_by_product[pid] = [0] * n_weeks
                meta_by_product[pid] = {
                    "product_name": row["product__name"],
                    "sku": row["product__sku"] or "",
                    "category_name": row["product__category__name"] or "",
                    "unit": row["product__unit"] or "",
                }
            week_value = row["week"]
            if hasattr(week_value, "date"):
                week_value = week_value.date()
            idx = week_index.get(week_value)
            if idx is not None:
                series_by_product[pid][idx] = row["qty"] or 0

        rows: list[dict] = []
        class_counts = {"X": 0, "Y": 0, "Z": 0}

        for pid, series in series_by_product.items():
            mean = statistics.fmean(series) if series else 0.0
            stdev = statistics.pstdev(series) if len(series) > 1 else 0.0
            cv_ratio = (stdev / mean) if mean > 0 else None
            cls = _classify(cv_ratio, mean)
            class_counts[cls] += 1

            meta = meta_by_product[pid]
            rows.append({
                "sku": meta["sku"],
                "product_name": meta["product_name"],
                "category_name": meta["category_name"],
                "unit": meta["unit"],
                "weeks": n_weeks,
                "mean_per_week": Decimal(str(round(mean, 2))),
                "stdev": Decimal(str(round(stdev, 2))),
                "cv_pct": (
                    Decimal(str(round(cv_ratio * 100, 2))) if cv_ratio is not None else "—"
                ),
                "cls": cls,
            })

        rows.sort(key=lambda r: (r["cls"], r["product_name"]))

        sections = [
            self._summary_section(
                total=len(rows),
                weeks=n_weeks,
                class_counts=class_counts,
            ),
            ReportSection(
                title="XYZ-классификация по товарам",
                columns=[
                    ReportColumn("sku", "SKU", align="left", width=14),
                    ReportColumn("product_name", "Товар", align="left", width=40),
                    ReportColumn("category_name", "Категория", align="left", width=24),
                    ReportColumn("unit", "Ед.", align="left", width=8),
                    ReportColumn("weeks", "Недель", align="right", width=10),
                    ReportColumn("mean_per_week", "Среднее/нед.", align="right", width=14),
                    ReportColumn("stdev", "Stddev", align="right", width=12),
                    ReportColumn("cv_pct", "CV, %", align="right", width=10),
                    ReportColumn("cls", "Класс", align="center", width=8),
                ],
                rows=rows,
                note=("Нет продаж за выбранный период" if not rows else None),
            ),
        ]

        return ReportData(
            title=self.title,
            period_label=self._period_label(),
            shop_label=self._shop_label(),
            sections=sections,
            generated_at=datetime.now(),
        )

    def _summary_section(
        self, *, total: int, weeks: int, class_counts: dict
    ) -> ReportSection:
        return ReportSection(
            title="Сводка XYZ",
            columns=[
                ReportColumn("name", "Показатель", align="left", width=44),
                ReportColumn("value", "Значение", align="right", width=20),
            ],
            rows=[
                {"name": "Товаров с продажами", "value": total},
                {"name": "Недель в периоде", "value": weeks},
                {"name": "X (стабильный спрос, CV ≤ 10%)", "value": class_counts["X"]},
                {"name": "Y (умеренный, 10–25%)", "value": class_counts["Y"]},
                {"name": "Z (нестабильный, > 25%)", "value": class_counts["Z"]},
            ],
        )
