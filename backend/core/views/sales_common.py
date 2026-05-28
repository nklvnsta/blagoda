from dataclasses import dataclass
from datetime import date, timedelta

from rest_framework.exceptions import ValidationError

from core.models import Category, Shop


@dataclass(frozen=True)
class ResolvedPeriod:
    code: str
    label: str
    date_from: date
    date_to: date


PERIOD_PRESETS = (
    ("yesterday", "Вчера"),
    ("last_7_days", "Последняя неделя"),
    ("last_30_days", "Последние 30 дней"),
    ("this_month", "Текущий месяц"),
    ("last_month", "Последний месяц"),
    ("last_3_months", "Последние 3 месяца"),
    ("custom", "Произвольный период"),
)

PERIOD_LABELS = {code: label for code, label in PERIOD_PRESETS}


def default_period() -> tuple[date, date]:
    today = date.today()
    return today - timedelta(days=6), today


def parse_date(value: str | None, default: date, field_name: str) -> date:
    if not value:
        return default
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(
            {field_name: f"Неверный формат даты: {value}. Ожидается YYYY-MM-DD."}
        ) from exc


def resolve_period(
    period_code: str | None,
    date_from_value: str | None,
    date_to_value: str | None,
) -> ResolvedPeriod:
    has_custom_dates = bool(date_from_value or date_to_value)

    if period_code is None and not has_custom_dates:
        period_code = "last_7_days"

    if period_code is not None and period_code not in PERIOD_LABELS:
        raise ValidationError({"period": f"Неизвестный период: {period_code}."})

    if period_code == "custom" and not (date_from_value and date_to_value):
        raise ValidationError(
            {"date": "Укажите date_from и date_to для произвольного периода."}
        )

    today = date.today()

    if period_code == "yesterday":
        yesterday = today - timedelta(days=1)
        preset_from, preset_to = yesterday, yesterday
    elif period_code == "last_30_days":
        preset_from, preset_to = today - timedelta(days=29), today
    elif period_code == "this_month":
        preset_from, preset_to = today.replace(day=1), today
    elif period_code == "last_month":
        first_this_month = today.replace(day=1)
        last_day_prev = first_this_month - timedelta(days=1)
        preset_from = last_day_prev.replace(day=1)
        preset_to = last_day_prev
    elif period_code == "last_3_months":
        preset_from, preset_to = today - timedelta(days=89), today
    elif period_code == "custom":
        preset_from, preset_to = today, today
    else:
        preset_from, preset_to = default_period()

    date_from = parse_date(date_from_value, preset_from, "date_from")
    date_to = parse_date(date_to_value, preset_to, "date_to")

    if date_from > date_to:
        raise ValidationError({"date": "date_from не может быть позже date_to."})

    if has_custom_dates or period_code == "custom":
        return ResolvedPeriod(
            code="custom",
            label="Произвольный период",
            date_from=date_from,
            date_to=date_to,
        )

    return ResolvedPeriod(
        code=period_code or "last_7_days",
        label=PERIOD_LABELS[period_code or "last_7_days"],
        date_from=date_from,
        date_to=date_to,
    )


def get_descendant_ids(category: Category) -> list:
    ids = [category.pk]
    for child in Category.objects.filter(parent=category).order_by("name"):
        ids.extend(get_descendant_ids(child))
    return ids


def validate_shop(shop_id: str | None) -> None:
    if shop_id is not None and not Shop.objects.filter(pk=shop_id, is_active=True).exists():
        raise ValidationError({"shop": f"Магазин с id={shop_id} не найден."})


def resolve_category_ids(category_id: str | None) -> list | None:
    if category_id is None:
        return None

    try:
        category = Category.objects.get(pk=category_id)
    except Category.DoesNotExist as exc:
        raise ValidationError({"category": f"Категория с id={category_id} не найдена."}) from exc

    return get_descendant_ids(category)


# ── сортировка таблиц ────────────────────────────────────────────────────────

ALLOWED_ORDERS = ("asc", "desc")


def resolve_sort(
    sort_value: str | None,
    order_value: str | None,
    allowed_fields: tuple[str, ...],
    default_field: str,
    default_order: str = "desc",
) -> tuple[str, str]:
    """
    Валидирует параметры `sort` и `order`.
    Возвращает (sort_field, order). Если `sort_value` пуст — используется
    `default_field`. Если `order_value` пуст — `default_order`.
    """
    field = sort_value or default_field
    if field not in allowed_fields:
        raise ValidationError(
            {"sort": f"Допустимые значения: {list(allowed_fields)}"}
        )

    order = (order_value or default_order).lower()
    if order not in ALLOWED_ORDERS:
        raise ValidationError({"order": f"Допустимые значения: {list(ALLOWED_ORDERS)}"})

    return field, order


def apply_search(value: str | None) -> str:
    """Нормализует значение поискового параметра для `icontains`."""
    return (value or "").strip()
