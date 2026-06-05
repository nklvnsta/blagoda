"""
python manage.py seed

Заполняет БД тестовыми данными:
  - 2 категории (с подкатегориями)
  - 10 магазинов сети Благода в ПМР
  - 30 товаров
  - ~90 партий на складе (разные статусы, часть просроченных)
  - ~200 отгрузок по магазинам
  - ~54 000 записей продаж (180 дней × 30 товаров × 10 магазинов)
  - 300 остатков (30 товаров × 10 магазинов)
  - отклонения (дефицит/избыток)
  - ~9 000 ежедневных снимков остатков (30 дней)
  - 18 000 прогнозов (60 дней × 30 × 10), точность >75 %
"""

import random
import math
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import models, transaction
from django.db.models import Avg, F, FloatField
from django.db.models.functions import Abs, Coalesce

from core.models import (
    Category, Shop, Product, Batch, BatchShipment,
    Sales, Receipt, Inventory, StockDeviation, InventorySnapshot,
    ForecastEntry,
)


# Данные 

CATEGORIES = [
    {
        "name": "Молочные продукты",
        "children": ["Молоко", "Кефир и йогурты", "Сыры", "Масло и сметана", "Творог"],
    },
    {
        "name": "Мясо и птица",
        "children": ["Колбасные изделия", "Курица", "Полуфабрикаты", "Консервы"],
    },
]

SHOPS = [
    {
        "name": "Благода Тирасполь, Юности",
        "address": "Тирасполь, ул. Юности 53",
        "latitude": 46.8480,
        "longitude": 29.6280,
        "normative_days": 3,
    },
    {
        "name": "Благода Тирасполь, Центральный рынок",
        "address": "Тирасполь, центральный рынок",
        "latitude": 46.8550,
        "longitude": 29.6350,
        "normative_days": 2,
    },
    {
        "name": "Благода Тирасполь, Каховская",
        "address": "Тирасполь, ул. Каховская 4/1",
        "latitude": 46.8420,
        "longitude": 29.6200,
        "normative_days": 3,
    },
    {
        "name": "Благода Бендеры, Победы",
        "address": "Бендеры, ул. Победы 1",
        "latitude": 46.8310,
        "longitude": 29.4770,
        "normative_days": 3,
    },
    {
        "name": "Благода Бендеры, Центральный рынок",
        "address": "Бендеры, Центральный рынок",
        "latitude": 46.8350,
        "longitude": 29.4820,
        "normative_days": 2,
    },
    {
        "name": "Благода Парканы, Гоголя",
        "address": "Парканы, ул. Гоголя 1",
        "latitude": 46.8670,
        "longitude": 29.6330,
        "normative_days": 4,
    },
    {
        "name": "Благода Рыбница, Мичурина",
        "address": "Рыбница, ул. Мичурина 43",
        "latitude": 47.7660,
        "longitude": 29.0030,
        "normative_days": 3,
    },
    {
        "name": "Благода Дубоссары, Ломоносова",
        "address": "Дубоссары, ул. Ломоносова 43",
        "latitude": 47.2650,
        "longitude": 29.1670,
        "normative_days": 3,
    },
    {
        "name": "Благода Григориополь, К. Маркса",
        "address": "Григориополь, ул. К. Маркса 172",
        "latitude": 47.1550,
        "longitude": 29.3000,
        "normative_days": 4,
    },
    {
        "name": "Благода Слободзея, Ленина",
        "address": "Слободзея, ул. Ленина 103",
        "latitude": 46.7330,
        "longitude": 29.7000,
        "normative_days": 3,
    },
]


PRODUCTS = [
    # Молочные
    ("Молоко Благода пастер. 2.5% 1л пак.",          "l",   16.00,   7,  "Молоко",               6),
    ("Молоко Благода пастер. 3.2% 1л пак.",          "l",   16.50,   7,  "Молоко",               6),
    ("Кефир Благода 2.5% 1л пак.",                   "l",   15.00,  14,  "Кефир и йогурты",      5),
    ("Ряженка Благода 2.5% 500мл пак.",              "g",   13.00,  14,  "Кефир и йогурты",      3),
    ("Сметана Благода 15% 200г стак.",               "g",   14.00,  21,  "Масло и сметана",      3),
    ("Сметана Благода 20% 500г пак.",                "g",   21.00,  21,  "Масло и сметана",      3),
    ("Творог Благода 9% 200г",                       "g",   19.50,  14,  "Творог",               3),
    ("Йогурт Благода 2.8% Клубника 150г стак.",      "g",   11.50,  21,  "Кефир и йогурты",      4),
    ("Йогурт Благода питьев 2.8% Персик 400мл пак.", "g",   17.00,  21,  "Кефир и йогурты",      3),
    ("Сыр Благода Российский 50%, кг",               "kg", 115.00,  60,  "Сыры",                 2),
    ("Сыр Благода Гауда 45%, кг",                    "kg", 106.00,  60,  "Сыры",                 1),
    ("Сыр Брынза Благода 250г",                      "g",   32.00,  45,  "Сыры",                 2),
    # Колбасные изделия
    ("Колбаса Докторская в/с, кг",                   "kg",  70.00,  10,  "Колбасные изделия",    2),
    ("Колбаса Молочная вареная в/с, кг",             "kg",  75.00,  10,  "Колбасные изделия",    2),
    ("Колбаса Краковская п/к в/с, кг",               "kg",  92.00,  14,  "Колбасные изделия",    2),
    ("Колбаса Сервелат Финский п/к 1с, кг",          "kg", 112.00,  21,  "Колбасные изделия",    1),
    ("Колбаса Пеперони с/к, кг",                     "kg", 128.00,  30,  "Колбасные изделия",    1),
    ("Колбаса Московская в/к в/с, кг",               "kg", 101.00,  21,  "Колбасные изделия",    2),
    ("Сосиски Докторские в/с, кг",                   "kg",  68.00,  10,  "Колбасные изделия",    3),
    ("Сосиски Баварские с сыром 1с, кг",             "kg",  86.00,  14,  "Колбасные изделия",    2),
    ("Сардельки Докторские в/с, кг",                 "kg",  62.00,  10,  "Колбасные изделия",    2),
    # Курица
    ("Бедро куриное Благода охлажд, кг",             "kg",  43.00,   5,  "Курица",               3),
    ("Голень куриная подложка, кг",                  "kg",  36.00,   5,  "Курица",               2),
    ("Филе куриное Благода заморож., кг",            "kg",  63.00, 180,  "Курица",               3),
    # Полуфабрикаты
    ("Пельмени Классические 900г",                   "g",   54.00, 180,  "Полуфабрикаты",        2),
    ("Пельмени Куриные 450г",                        "g",   36.00, 180,  "Полуфабрикаты",        2),
    ("Вареники с картофелем 600г",                   "g",   30.00, 180,  "Полуфабрикаты",        2),
    ("Вареники с творогом 600г",                     "g",   32.00, 180,  "Полуфабрикаты",        1),
    ("Котлета куриная заморож, кг",                  "kg",  48.00, 180,  "Полуфабрикаты",        3),
    # Консервы
    ("Говядина тушеная ГОСТ 338г ж/б",               "g",   41.00, 730,  "Консервы",             1),
]

SALES_PERIOD_DAYS = 180
FORECAST_DAYS = 60
FORECAST_NOISE = 0.05
SALES_NOISE_STDEV = 0.18
ROLLING_WINDOW_DAYS = 30

WEEKDAY_FACTORS = [1.0, 0.95, 1.0, 1.05, 1.1, 1.2, 1.15]


def _shop_factor(product_sku: str, shop_name: str) -> float:
    rng = random.Random(hash((product_sku, shop_name)) % (2**32))
    return rng.uniform(0.6, 1.4)


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
        random.seed(42)

        if options["clear"]:
            self.stdout.write("Очищаем таблицы...")
            ForecastEntry.objects.all().delete()
            StockDeviation.objects.all().delete()
            InventorySnapshot.objects.all().delete()
            Inventory.objects.all().delete()
            Sales.objects.all().delete()
            Receipt.objects.all().delete()
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

        accuracy_pct = self._verify_forecast_accuracy(min_pct=75.0)
        if accuracy_pct < 75.0:
            self.stdout.write(self.style.WARNING(
                f"  Точность {accuracy_pct}% ниже 75%, пересчитываем прогнозы с меньшим шумом..."
            ))
            for noise in (0.03, 0.01, 0.0):
                random.seed(42)
                self._recalculate_forecast_predictions(products, shops, noise_stdev=noise)
                accuracy_pct = self._verify_forecast_accuracy(min_pct=75.0)
                if accuracy_pct >= 75.0:
                    break

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Готово: {len(categories)} категорий, {len(shops)} магазинов, "
            f"{len(products)} товаров, {Batch.objects.count()} партий, "
            f"{Receipt.objects.count()} чеков, {Sales.objects.count()} продаж, "
            f"{len(inventories)} остатков, {ForecastEntry.objects.count()} прогнозов, "
            f"точность прогноза {accuracy_pct}%"
        ))

    # Категории 
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

    #  Магазины 
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

    #  Товары 
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

    #  Партии 
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

    #  Отгрузки 
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

    #  Продажи 
    def _seed_sales(self, products, shops):
        self.stdout.write("Создаём продажи (180 дней) и чеки...")
        today = date.today()
        sales_data = []

        avg_sales_map = {
            p.sku: PRODUCTS[i][5]
            for i, p in enumerate(products)
        }

        for product in products:
            base = avg_sales_map.get(product.sku, 10)

            for shop in shops:
                shop_factor = _shop_factor(product.sku, shop.name)

                for day_offset in range(SALES_PERIOD_DAYS):
                    d = today - timedelta(days=day_offset)

                    weekday_factor = WEEKDAY_FACTORS[d.weekday()]    #считается продажа за день
                    seasonal = 1.0 + 0.15 * math.sin(2 * math.pi * d.timetuple().tm_yday / 365)  #недельная сезонность   
                    trend = 1.0 + 0.0005 * (SALES_PERIOD_DAYS - day_offset)   

                    mean = base * shop_factor * weekday_factor * seasonal * trend
                    qty  = max(0, int(random.gauss(mean, mean * SALES_NOISE_STDEV)))   #примерное среднее значение

                    if qty > 0:
                        sales_data.append((product, shop, qty, d, product.price))

        from collections import defaultdict
        receipts_by_shop_date = defaultdict(list)

        for product, shop, qty, d, price_at_sale in sales_data:
            receipts_by_shop_date[(shop.id, d)].append({
                'product': product,
                'quantity': qty,
                'price_at_sale': price_at_sale,
                'shop': shop,
                'date': d,
            })

        receipts_list = []

        for (shop_id, sale_date), sales_in_group in receipts_by_shop_date.items():
            # Один чек = одна покупка клиента: 2–5 позиций, qty=1 на строку.
            # Суточный объём (sales_in_group) разбиваем на отдельные транзакции.
            items_per_receipt = random.randint(2, 5)
            current_receipt_items = []

            for sale_item in sales_in_group:
                current_receipt_items.append(sale_item)

                if len(current_receipt_items) >= items_per_receipt or sale_item == sales_in_group[-1]:
                    # Сумма чека считается как price × 1 (один товар на позицию)
                    total_amount = sum(
                        float(item['price_at_sale'])
                        for item in current_receipt_items
                    )
                    receipt = Receipt(
                        shop_id=shop_id,
                        total_amount=total_amount,
                        item_count=len(current_receipt_items),
                        total_qty=len(current_receipt_items),
                    )
                    receipts_list.append((receipt, current_receipt_items))
                    current_receipt_items = []
                    items_per_receipt = random.randint(2, 5)

        receipt_objects = [r[0] for r in receipts_list]
        Receipt.objects.bulk_create(receipt_objects, batch_size=200)

        created_receipts = Receipt.objects.filter(shop__in=shops).order_by('-created_at')[:len(receipt_objects)]
        receipt_list = list(created_receipts)

        sales_list = []
        receipt_idx = 0
        for receipt in receipt_list:
            if receipt_idx < len(receipts_list):
                _, sales_items = receipts_list[receipt_idx]
                for item in sales_items:
                    sales_list.append(Sales(
                        product=item['product'],
                        shop=item['shop'],
                        quantity=item['quantity'],
                        date=item['date'],
                        price_at_sale=item['price_at_sale'],
                        receipt=receipt,
                    ))
                receipt_idx += 1

        Sales.objects.bulk_create(sales_list, batch_size=500)

        self.stdout.write(f"  → {len(receipt_list)} чеков, {len(sales_list)} записей продаж")

        return (sales_list, receipt_list)

    #  Остатки (Inventory) 
    def _seed_inventory(self, products, shops):
        self.stdout.write("Создаём остатки...")
        inventories = []

        for i, product in enumerate(products):
            base_avg = PRODUCTS[i][5]

            for shop in shops:
                shop_avg = base_avg * _shop_factor(product.sku, shop.name)
                safety   = random.choice([2, 3, 4])   
                cycle    = random.choice([5, 7, 10])

                min_stock = int(shop_avg * safety)   #сред продажа за день * на запас в 2-4 дня
                max_stock = int(shop_avg * (safety + cycle))   #сред продажа в день * запас на бол кол-во дней

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

    #  Отклонения (StockDeviation) 
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

    #  Снимки остатков (InventorySnapshot) 
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

    #  Прогнозы
    def _build_sales_index(self, days_back: int) -> dict[tuple, int]:
        today = date.today()
        sales_index: dict[tuple, int] = {}
        for sale in Sales.objects.filter(
            date__gte=today - timedelta(days=days_back),
        ).values("product_id", "shop_id", "date").annotate(
            total=models.Sum("quantity"),
        ):
            sales_index[(sale["product_id"], sale["shop_id"], sale["date"])] = sale["total"]
        return sales_index

    def _rolling_avg(     
        self,
        sales_index: dict[tuple, int],
        product_id,
        shop_id,
        d: date,
        fallback: float,
    ) -> float:
        total = sum(   #средне скользящее
            sales_index.get((product_id, shop_id, d - timedelta(days=i)), 0)
            for i in range(1, ROLLING_WINDOW_DAYS + 1)
        )
        if total == 0:    
            return fallback
        return total / ROLLING_WINDOW_DAYS

    def _predict_qty(        #средн скольз * коэфиц дня недели * небольш случ шум 
        self,
        rolling_avg: float,
        weekday: int,
        noise_stdev: float,
    ) -> int:
        wf = WEEKDAY_FACTORS[weekday]
        return max(1, int(rolling_avg * wf * random.gauss(1.0, noise_stdev)))

    def _seed_forecasts(self, products, shops):
        """
        Генерируем прогнозы за последние FORECAST_DAYS дней.
        Формула: avg(продаж за предыдущие 30 дней) × weekday_factor × шум.
        Фактические продажи берутся из Sales. Целевая точность >75 %.
        """
        self.stdout.write(f"Создаём прогнозы ({FORECAST_DAYS} дней)...")
        today = date.today()

        sales_index = self._build_sales_index(FORECAST_DAYS + ROLLING_WINDOW_DAYS)

        avg_sales_map = {
            p.sku: PRODUCTS[i][5]
            for i, p in enumerate(products)
        }

        rows = []
        for product in products:
            base = avg_sales_map.get(product.sku, 10)
            for shop in shops:
                fallback = base * _shop_factor(product.sku, shop.name)

                for day_offset in range(FORECAST_DAYS):
                    d = today - timedelta(days=day_offset)
                    rolling_avg = self._rolling_avg(
                        sales_index, product.pk, shop.pk, d, fallback,
                    )
                    predicted = self._predict_qty(rolling_avg, d.weekday(), FORECAST_NOISE)
                    actual = sales_index.get((product.pk, shop.pk, d))

                    rows.append(ForecastEntry(
                        product=product,
                        shop=shop,
                        date=d,
                        predicted_qty=predicted,
                        actual_qty=actual,
                    ))

        ForecastEntry.objects.bulk_create(rows, batch_size=500, ignore_conflicts=True)
        self.stdout.write(f"  → {len(rows)} прогнозов")

    def _recalculate_forecast_predictions(self, products, shops, noise_stdev: float):
        today = date.today()
        sales_index = self._build_sales_index(FORECAST_DAYS + ROLLING_WINDOW_DAYS)

        avg_sales_map = {
            p.sku: PRODUCTS[i][5]
            for i, p in enumerate(products)
        }

        to_update = []
        for entry in ForecastEntry.objects.select_related("product", "shop").filter(
            date__gte=today - timedelta(days=FORECAST_DAYS),
        ):
            base = avg_sales_map.get(entry.product.sku, 10)
            fallback = base * _shop_factor(entry.product.sku, entry.shop.name)
            rolling_avg = self._rolling_avg(
                sales_index, entry.product_id, entry.shop_id, entry.date, fallback,
            )
            entry.predicted_qty = self._predict_qty(rolling_avg, entry.date.weekday(), noise_stdev)
            to_update.append(entry)

        ForecastEntry.objects.bulk_update(to_update, ["predicted_qty"], batch_size=500)
        self.stdout.write(f"  → пересчитано {len(to_update)} прогнозов (шум σ={noise_stdev})")

    def _verify_forecast_accuracy(self, min_pct: float = 75.0) -> float:
        result = ForecastEntry.objects.filter(
            actual_qty__isnull=False,
            actual_qty__gt=0,
        ).aggregate(
            mean_error=Coalesce(
                Avg(
                    Abs(F("actual_qty") - F("predicted_qty")) * 1.0 / F("actual_qty"),
                    output_field=FloatField(),
                ),
                0.0,
                output_field=FloatField(),
            ),
        )
        mean_error = result["mean_error"] or 0.0
        accuracy_pct = round(max(0.0, (1.0 - mean_error)) * 100, 1)    #точность прогноза
        style = self.style.SUCCESS if accuracy_pct >= min_pct else self.style.WARNING
        self.stdout.write(style(f"  → Точность прогноза: {accuracy_pct}%"))
        return accuracy_pct
