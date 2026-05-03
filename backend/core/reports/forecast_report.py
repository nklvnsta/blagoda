"""
Отчёт по прогнозу спроса.

Один раздел «По товарам»: на горизонте [date_from; date_to] суммируем
predicted_qty и (где есть) actual_qty, считаем отклонение и точность.
"""

from datetime import datetime
from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import Coalesce

from core.models import ForecastEntry
from core.reports.base import (
    ReportBuilder,
    ReportColumn,
    ReportData,
    ReportSection,
)


def _accuracy_pct(predicted: int, actual: int | None) -> Decimal | None:
    if actual is None or actual <= 0:
        return None
    diff = abs(actual - predicted)
    err = Decimal(diff) / Decimal(actual)
    acc = max(Decimal("0"), Decimal("1") - err)
    return (acc * Decimal("100")).quantize(Decimal("0.01"))


class ForecastReport(ReportBuilder):
    kind = "forecast"
    title = "Отчет по прогнозу спроса"

    def build(self) -> ReportData:
        qs = ForecastEntry.objects.filter(
            date__gte=self.date_from,
            date__lte=self.date_to,
        )
        if self.shop_id:
            qs = qs.filter(shop_id=self.shop_id)

        agg = (
            qs.values(
                "product_id",
                "product__name",
                "product__sku",
                "product__category__name",
                "product__unit",
            )
            .annotate(
                predicted=Coalesce(Sum("predicted_qty"), 0),
                actual=Coalesce(Sum("actual_qty"), 0),
            )
            .order_by("-predicted", "product__name")
        )

        rows: list[dict] = []
        total_predicted = 0
        total_actual = 0

        for row in agg:
            predicted = row["predicted"] or 0
            actual = row["actual"] or 0
            deviation = actual - predicted
            accuracy = _accuracy_pct(predicted, actual if actual > 0 else None)
            rows.append({
                "sku": row["product__sku"] or "",
                "product_name": row["product__name"],
                "category_name": row["product__category__name"] or "",
                "unit": row["product__unit"] or "",
                "predicted": predicted,
                "actual": actual,
                "deviation": deviation,
                "accuracy_pct": accuracy if accuracy is not None else "—",
            })
            total_predicted += predicted
            total_actual += actual

        section = ReportSection(
            title="Прогноз по товарам",
            columns=[
                ReportColumn("sku", "SKU", align="left", width=14),
                ReportColumn("product_name", "Товар", align="left", width=40),
                ReportColumn("category_name", "Категория", align="left", width=24),
                ReportColumn("unit", "Ед.", align="left", width=8),
                ReportColumn("predicted", "Прогноз", align="right", width=12),
                ReportColumn("actual", "Факт", align="right", width=12),
                ReportColumn("deviation", "Отклонение", align="right", width=14),
                ReportColumn("accuracy_pct", "Точность, %", align="right", width=14),
            ],
            rows=rows,
            totals={
                "sku": "",
                "product_name": "Итого",
                "category_name": "",
                "unit": "",
                "predicted": total_predicted,
                "actual": total_actual,
                "deviation": total_actual - total_predicted,
                "accuracy_pct": "",
            },
            note=("Нет прогнозов за выбранный период" if not rows else None),
        )

        return ReportData(
            title=self.title,
            period_label=self._period_label(),
            shop_label=self._shop_label(),
            sections=[section],
            generated_at=datetime.now(),
        )
