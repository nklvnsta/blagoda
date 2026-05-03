"""Локализация значений ячеек для отчётов (RU)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any


def format_cell(value: Any, *, is_money: bool = False) -> str:
    """Превращает Python-значение в строку для XLSX/PDF (RU-стиль)."""
    if value is None or value == "":
        return "—" if value is None else ""
    if isinstance(value, bool):
        return "Да" if value else "Нет"
    if isinstance(value, Decimal):
        return _format_number(value, money=is_money)
    if isinstance(value, (int,)):
        return _format_int(value)
    if isinstance(value, float):
        return _format_number(Decimal(str(value)), money=is_money)
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y")
    return str(value)


def _format_int(value: int) -> str:
    sign = "-" if value < 0 else ""
    abs_str = str(abs(value))
    groups = []
    while abs_str:
        groups.append(abs_str[-3:])
        abs_str = abs_str[:-3]
    return sign + "\u00a0".join(reversed(groups))


def _format_number(value: Decimal, *, money: bool) -> str:
    if money:
        value = value.quantize(Decimal("0.01"))
    sign = "-" if value < 0 else ""
    value = abs(value)
    int_part, _, frac_part = format(value, "f").partition(".")
    grouped = []
    while int_part:
        grouped.append(int_part[-3:])
        int_part = int_part[:-3]
    int_str = "\u00a0".join(reversed(grouped))
    if money:
        frac_part = frac_part or "00"
        frac_part = (frac_part + "00")[:2]
        return f"{sign}{int_str},{frac_part}"
    if frac_part and frac_part.rstrip("0"):
        return f"{sign}{int_str},{frac_part.rstrip('0')}"
    return f"{sign}{int_str}"
