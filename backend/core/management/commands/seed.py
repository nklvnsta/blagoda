"""
python manage.py seed

Заполняет БД тестовыми данными:
  - 4 категории (с подкатегориями)
  - 5 магазинов сети Благода в разных районах
  - 20 товаров
  - ~60 партий на складе (разные статусы, часть просроченных)
  - ~120 отгрузок по магазинам
  - ~18 000 записей продаж (180 дней × 20 товаров × ~5 магазинов)
  - 100 остатков (20 товаров × 5 магазинов)
  - отклонения (дефицит/избыток)
  - ~3 000 ежедневных снимков остатков (30 дней)
"""

import random
import math
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import models, transaction

from core.models import (
    Category, Shop, Product, Batch, BatchShipment,
    Sales, Inventory, StockDeviation, InventorySnapshot,
    ForecastEntry,
)


# ─── Данные ──────────────────────────────────────────────────────────────────

CATEGORIES = [
    {
        "name": "Молочные продукты",
        "children": ["Молоко", "Кефир и йогурты", "Сыры", "Масло и сметана"],
    },
    {
        "name": "Мясо и птица",
        "children": ["Говядина", "Свинина", "Курица", "Полуфабрикаты"],
    },
    {
        "name": "Хлеб и выпечка",
        "children": ["Хлеб", "Булочки и сдоба"],
    },
    {
        "name": "Напитки",
        "children": ["Соки", "Вода", "Газированные напитки"],
    },
]

SHOPS = [
    {
        "name": "Благода на Ленина",
        "address": "ул. Ленина, 12",
        "latitude": 47.2213,
        "longitude": 38.9025,
        "normative_days": 3,
    },
    {
        "name": "Благода Центральный",
        "address": "пр. Победы, 45",
        "latitude": 47.2357,
        "longitude": 38.8960,
        "normative_days": 4,
    },
    {
        "name": "Благода на Садовой",
        "address": "ул. Садовая, 78",
        "latitude": 47.2108,
        "longitude": 38.9142,
        "normative_days": 2,
    },
    {
        "name": "Благода Северный",
        "address": "ул. Северная, 3",
        "latitude": 47.2501,
        "longitude": 38.9080,
        "normative_days": 3,
    },
    {
        "name": "Благода на Мира",
        "address": "пр. Мира, 22",
        "latitude": 47.2190,
        "longitude": 38.8870,
        "normative_days": 5,
    },
]

# (name, unit, price, shelf_life_days, category, avg_sales_per_day)
PRODUCTS = [
    # Молочные
    ("Молоко 3.2% Простоквашино 1л",   "l",    89.90,  7,   "Молоко",              25),
    ("Молоко 2.5% Домик в деревне 1л", "l",    79.90,  7,   "Молоко",              20),
    ("Кефир 2.5% Активиа 500г",        "g",    65.00,  14,  "Кефир и йогурты",     15),
    ("Йогурт клубника Danone 150г",    "g",    55.50,  21,  "Кефир и йогурты",     18),
    ("Сыр Российский 45% кг",          "kg",  490.00,  90,  "Сыры",                 5),
    ("Масло сливочное 82.5% 200г",     "g",   130.00,  60,  "Масло и сметана",      8),
    ("Сметана 20% 400г",               "g",    75.00,  21,  "Масло и сметана",     12),
    # Мясо
    ("Фарш говяжий охл. 500г",         "g",   245.00,  3,   "Говядина",            10),
    ("Стейк из говядины охл. 300г",    "g",   380.00,  5,   "Говядина",             4),
    ("Свинина шея охл. кг",            "kg",  320.00,  5,   "Свинина",              6),
    ("Куриное филе охл. кг",           "kg",  280.00,  5,   "Курица",              14),
    ("Куриные крылья охл. кг",         "kg",  180.00,  4,   "Курица",               8),
    ("Пельмени Сибирские 900г",        "g",   210.00,  180, "Полуфабрикаты",        7),
    # Хлеб
    ("Хлеб Бородинский 400г",          "g",    45.00,  5,   "Хлеб",               30),
    ("Батон нарезной 400г",            "g",    38.00,  3,   "Хлеб",               25),
    ("Булочка сдобная 80г",            "g",    22.00,  2,   "Булочки и сдоба",    20),
    # Напитки
    ("Сок яблочный Rich 1л",           "l",    95.00,  365, "Соки",                 6),
    ("Вода Святой Источник 1.5л",      "l",    55.00,  730, "Вода",                15),
    ("Вода Черноголовка газ. 1л",      "l",    65.00,  365, "Газированные напитки", 10),
    ("Сок апельсиновый Tropicana 1л",  "l",   110.00,  365, "Соки",                 5),
]

SALES_PERIOD_DAYS = 180


class Command(BaseCommand):
    help = "Заполняет БД тестовыми данными"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Удалить существующие данные перед заполнением",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Очищаем таблицы...")
            ForecastEntry.objects.all().delete()
            StockDeviation.objects.all().delete()
            InventorySnapshot.objects.all().delete()
            Inventory.objects.all().delete()
            Sales.objects.all().delete()
            BatchShipment.objects.all().delete()
            Batch.objects.all().delete()
            Product.objects.all().delete()
            Shop.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING("Таблицы очищены"))

        categories = self._seed_categories()
        shops      = self._seed_shops()
        products   = self._seed_products(categories)
        batches    = self._seed_batches(products)
        self._seed_shipments(batches, shops)
        self._seed_sales(products, shops)
        inventories = self._seed_inventory(products, shops)
        self._seed_deviations(inventories)
        self._seed_snapshots(products, shops)
        self._seed_forecasts(products, shops)

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Готово: {len(categories)} категорий, {len(shops)} магазинов, "
            f"{len(products)} товаров, {Batch.objects.count()} партий, "
            f"{Sales.objects.count()} продаж, {len(inventories)} остатков, "
            f"{ForecastEntry.objects.count()} прогнозов"
        ))

    # ── Категории ────────────────────────────────────────────────────────────

    def _seed_categories(self):
        self.stdout.write("Создаём категории...")
        cat_map = {}

        for group in CATEGORIES:
            parent, _ = Category.objects.get_or_create(name=group["name"])
            cat_map[group["name"]] = parent

            for child_name in group["children"]:
                child, _ = Category.objects.get_or_create(
                    name=child_name,
                    defaults={"parent": parent},
                )
                cat_map[child_name] = child

        self.stdout.write(f"  → {len(cat_map)} категорий")
        return cat_map

    # ── Магазины ─────────────────────────────────────────────────────────────

    def _seed_shops(self):
        self.stdout.write("Создаём магазины...")
        shops = []
        for data in SHOPS:
            shop, _ = Shop.objects.get_or_create(
                name=data["name"],
                defaults=data,
            )
            shops.append(shop)
        self.stdout.write(f"  → {len(shops)} магазинов")
        return shops

    # ── Товары ───────────────────────────────────────────────────────────────

    def _seed_products(self, categories):
        self.stdout.write("Создаём товары...")
        products = []
        for i, (name, unit, price, shelf_life, cat_name, _avg_sales) in enumerate(PRODUCTS, start=1):
            sku = f"BLG-{i:04d}"
            product, _ = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    "name":            name,
                    "unit":            unit,
                    "price":           price,
                    "shelf_life_days": shelf_life,
                    "category":        categories[cat_name],
                },
            )
            products.append(product)
        self.stdout.write(f"  → {len(products)} товаров")
        return products

    # ── Партии ───────────────────────────────────────────────────────────────

    def _seed_batches(self, products):
        self.stdout.write("Создаём партии...")
        today   = date.today()

        for product in products:
            shelf = product.shelf_life_days or 30
            for _ in range(random.randint(2, 4)):
                produced_days_ago = random.randint(0, min(60, shelf - 1))
                production_date   = today - timedelta(days=produced_days_ago)
                expiry_date       = production_date + timedelta(days=shelf)

                qty = random.randint(50, 500)

                if random.random() < 0.1:
                    expiry_date   = today - timedelta(days=random.randint(1, 10))
                    status        = Batch.Status.WRITTEN_OFF
                    qty_remaining = 0
                else:
                    status        = Batch.Status.AVAILABLE
                    qty_remaining = qty

                received_days_ago = random.randint(0, produced_days_ago)

                batch = Batch(
                    product            = product,
                    quantity           = qty,
                    quantity_remaining = qty_remaining,
                    production_date    = production_date,
                    expiry_date        = expiry_date,
                    status             = status,
                    received_at        = today - timedelta(days=received_days_ago),
                )
                Batch.objects.bulk_create([batch])

        batches = list(Batch.objects.filter(
            status__in=[Batch.Status.AVAILABLE, Batch.Status.PARTIAL]
        ).select_related("product"))

        self.stdout.write(f"  → {Batch.objects.count()} партий")
        return batches

    # ── Отгрузки ─────────────────────────────────────────────────────────────

    def _seed_shipments(self, batches, shops):
        self.stdout.write("Создаём отгрузки...")
        today     = date.today()
        shipments = []

        for batch in batches:
            target_shops = random.sample(shops, k=random.randint(1, 3))
            available    = batch.quantity_remaining

            if available == 0:
                continue

            for shop in target_shops:
                if available <= 0:
                    break
                max_ship = max(1, int(available * 0.4))
                qty      = random.randint(1, max_ship)
                qty      = min(qty, available)

                shipped_days_ago = random.randint(0, 14)

                shipments.append(BatchShipment(
                    batch            = batch,
                    shop             = shop,
                    quantity_shipped = qty,
                    shipped_at       = today - timedelta(days=shipped_days_ago),
                ))
                available -= qty

            batch.quantity_remaining = available
            batch._update_status()

        BatchShipment.objects.bulk_create(shipments, batch_size=200)
        Batch.objects.bulk_update(
            batches,
            ["quantity_remaining", "status"],
            batch_size=200,
        )

        self.stdout.write(f"  → {len(shipments)} отгрузок")

    # ── Продажи ──────────────────────────────────────────────────────────────

    def _seed_sales(self, products, shops):
        self.stdout.write("Создаём продажи (180 дней)...")
        today = date.today()
        rows  = []

        avg_sales_map = {
            p.sku: PRODUCTS[i][5]
            for i, p in enumerate(products)
        }

        for product in products:
            base = avg_sales_map.get(product.sku, 10)

            for shop in shops:
                shop_factor = random.uniform(0.6, 1.4)

                for day_offset in range(SALES_PERIOD_DAYS):
                    d = today - timedelta(days=day_offset)

                    weekday_factor = 1.2 if d.weekday() >= 5 else 1.0
                    seasonal = 1.0 + 0.15 * math.sin(2 * math.pi * d.timetuple().tm_yday / 365)
                    trend = 1.0 + 0.0005 * (SALES_PERIOD_DAYS - day_offset)

                    mean = base * shop_factor * weekday_factor * seasonal * trend
                    qty  = max(0, int(random.gauss(mean, mean * 0.25)))

                    if qty > 0:
                        rows.append(Sales(
                            product  = product,
                            shop     = shop,
                            quantity = qty,
                            date     = d,
                        ))

        Sales.objects.bulk_create(rows, batch_size=500)
        self.stdout.write(f"  → {len(rows)} записей продаж")

    # ── Остатки (Inventory) ──────────────────────────────────────────────────

    def _seed_inventory(self, products, shops):
        self.stdout.write("Создаём остатки...")
        inventories = []

        for i, product in enumerate(products):
            base_avg = PRODUCTS[i][5]

            for shop in shops:
                shop_avg = base_avg * random.uniform(0.7, 1.3)
                safety   = random.choice([2, 3, 4])
                cycle    = random.choice([5, 7, 10])

                min_stock = int(shop_avg * safety)
                max_stock = int(shop_avg * (safety + cycle))

                # Текущий остаток: в большинстве случаев нормальный,
                # но иногда дефицит или избыток
                roll = random.random()
                if roll < 0.15:
                    current_qty = random.randint(0, max(1, min_stock - 1))
                elif roll < 0.25:
                    current_qty = random.randint(max_stock + 1, max_stock + int(shop_avg * 5))
                else:
                    current_qty = random.randint(min_stock, max_stock)

                inv, _ = Inventory.objects.get_or_create(
                    product=product,
                    shop=shop,
                    defaults={
                        "current_qty":       current_qty,
                        "min_stock":         min_stock,
                        "max_stock":         max_stock,
                        "avg_daily_sales":   round(shop_avg, 1),
                        "safety_stock_days": safety,
                        "reorder_cycle_days": cycle,
                    },
                )
                inventories.append(inv)

        self.stdout.write(f"  → {len(inventories)} остатков")
        return inventories

    # ── Отклонения (StockDeviation) ──────────────────────────────────────────

    def _seed_deviations(self, inventories):
        self.stdout.write("Создаём отклонения...")
        deviations = []

        for inv in inventories:
            if inv.deficit > 0:
                deviations.append(StockDeviation(
                    inventory      = inv,
                    deviation_type = StockDeviation.Type.DEFICIT,
                    deviation_qty  = inv.deficit,
                    is_active      = True,
                ))
            elif inv.surplus > 0:
                deviations.append(StockDeviation(
                    inventory      = inv,
                    deviation_type = StockDeviation.Type.SURPLUS,
                    deviation_qty  = inv.surplus,
                    is_active      = True,
                ))

        StockDeviation.objects.bulk_create(deviations, batch_size=200)
        self.stdout.write(f"  → {len(deviations)} отклонений ({sum(1 for d in deviations if d.deviation_type == 'deficit')} дефицитов, {sum(1 for d in deviations if d.deviation_type == 'surplus')} избытков)")

    # ── Снимки остатков (InventorySnapshot) ──────────────────────────────────

    def _seed_snapshots(self, products, shops):
        self.stdout.write("Создаём снимки остатков (30 дней)...")
        today     = date.today()
        snapshots = []

        inv_map = {}
        for inv in Inventory.objects.select_related("product", "shop"):
            inv_map[(inv.product_id, inv.shop_id)] = inv

        for product in products:
            for shop in shops:
                inv = inv_map.get((product.pk, shop.pk))
                if not inv:
                    continue

                qty = inv.current_qty

                for day_offset in range(30):
                    d = today - timedelta(days=day_offset)

                    daily_change = random.randint(
                        -int(inv.avg_daily_sales * 0.5),
                        int(inv.avg_daily_sales * 0.8),
                    )
                    snap_qty = max(0, qty + daily_change * (day_offset + 1) // 5)

                    snapshots.append(InventorySnapshot(
                        product       = product,
                        shop          = shop,
                        qty           = snap_qty,
                        snapshot_date = d,
                    ))

        InventorySnapshot.objects.bulk_create(snapshots, batch_size=500, ignore_conflicts=True)
        self.stdout.write(f"  → {len(snapshots)} снимков")

    # ── Прогнозы (ForecastEntry) ───────────────────────────────────────────

    FORECAST_DAYS = 60

    def _seed_forecasts(self, products, shops):
        """
        Генерируем прогнозы за последние FORECAST_DAYS дней.
        Формула прогноза: avg(продаж за предыдущие 30 дней) × weekday_factor.
        Фактические продажи берутся из Sales.
        Целевая точность ~88–92 %.
        """
        self.stdout.write(f"Создаём прогнозы ({self.FORECAST_DAYS} дней)...")
        today = date.today()

        actual_map: dict[tuple, int] = {}
        for sale in Sales.objects.filter(
            date__gte=today - timedelta(days=self.FORECAST_DAYS),
        ).values("product_id", "shop_id", "date").annotate(
            total=models.Sum("quantity"),
        ):
            actual_map[(sale["product_id"], sale["shop_id"], sale["date"])] = sale["total"]

        avg_sales_map = {
            p.sku: PRODUCTS[i][5]
            for i, p in enumerate(products)
        }

        weekday_factors = [1.0, 0.95, 1.0, 1.05, 1.1, 1.2, 1.15]

        rows = []
        for product in products:
            base = avg_sales_map.get(product.sku, 10)
            for shop in shops:
                shop_factor = random.uniform(0.7, 1.3)

                for day_offset in range(self.FORECAST_DAYS):
                    d = today - timedelta(days=day_offset)
                    wf = weekday_factors[d.weekday()]

                    predicted = max(1, int(base * shop_factor * wf * random.gauss(1.0, 0.08)))

                    actual = actual_map.get((product.pk, shop.pk, d))

                    rows.append(ForecastEntry(
                        product=product,
                        shop=shop,
                        date=d,
                        predicted_qty=predicted,
                        actual_qty=actual,
                    ))

        ForecastEntry.objects.bulk_create(rows, batch_size=500, ignore_conflicts=True)
        self.stdout.write(f"  → {len(rows)} прогнозов")
