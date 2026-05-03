"""
Базовый контракт между билдерами отчётов и рендерами (XLSX/PDF).

ReportBuilder отвечает только за вытаскивание данных и подготовку структуры
ReportData. Форматирование (XLSX/PDF) — задача рендеров, см.
core/reports/renderers/.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Literal

Align = Literal["left", "right", "center"]


@dataclass(frozen=True)
class ReportColumn:
    key: str
    title: str
    align: Align = "left"
    width: int | None = None
    is_money: bool = False


@dataclass
class ReportSection:
    title: str
    columns: list[ReportColumn]
    rows: list[dict[str, Any]] = field(default_factory=list)
    totals: dict[str, Any] | None = None
    note: str | None = None


@dataclass
class ReportData:
    title: str
    period_label: str
    shop_label: str | None
    sections: list[ReportSection]
    generated_at: datetime


class ReportBuilder(ABC):
    """
    Конкретный билдер реализует build() и возвращает ReportData.

    Конструктор принимает только то, что приходит с фронта: период и
    опциональный shop_id. Если для конкретного отчёта период не нужен
    (например, остатки на текущий момент), билдер просто игнорирует даты,
    но обязан их принять для единообразия.
    """

    kind: str = ""
    title: str = ""

    def __init__(
        self,
        *,
        date_from: date,
        date_to: date,
        shop_id: str | None = None,
    ) -> None:
        self.date_from = date_from
        self.date_to = date_to
        self.shop_id = shop_id

    @abstractmethod
    def build(self) -> ReportData:
        raise NotImplementedError

    def _period_label(self) -> str:
        return f"{self.date_from.strftime('%d.%m.%Y')} — {self.date_to.strftime('%d.%m.%Y')}"

    def _shop_label(self) -> str | None:
        if not self.shop_id:
            return None
        from core.models import Shop

        shop = Shop.objects.filter(pk=self.shop_id).only("name").first()
        return f"Магазин: {shop.name}" if shop else f"Магазин: {self.shop_id}"
