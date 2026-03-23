"""
python manage.py seed

Заполняет БД тестовыми данными:
  - 4 категории (с подкатегориями)
  - 5 магазинов сети Благода в разных районах
  - 20 товаров
  - ~60 партий на складе (разные статусы, часть просроченных)
  - ~120 отгрузок по магазинам
"""

import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Category, Shop, Product, Batch, BatchShipment


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

# (name, unit, shelf_life_days, подкатегория)
PRODUCTS = [
    # Молочные
    ("Молоко 3.2% Простоквашино 1л",   "l",   7,   "Молоко"),
    ("Молоко 2.5% Домик в деревне 1л", "l",   7,   "Молоко"),
    ("Кефир 2.5% Активиа 500г",        "g",   14,  "Кефир и йогурты"),
    ("Йогурт клубника Danone 150г",    "g",   21,  "Кефир и йогурты"),
    ("Сыр Российский 45% кг",          "kg",  90,  "Сыры"),
    ("Масло сливочное 82.5% 200г",     "g",   60,  "Масло и сметана"),
    ("Сметана 20% 400г",               "g",   21,  "Масло и сметана"),
    # Мясо
    ("Фарш говяжий охл. 500г",         "g",   3,   "Говядина"),
    ("Стейк из говядины охл. 300г",    "g",   5,   "Говядина"),
    ("Свинина шея охл. кг",            "kg",  5,   "Свинина"),
    ("Куриное филе охл. кг",           "kg",  5,   "Курица"),
    ("Куриные крылья охл. кг",         "kg",  4,   "Курица"),
    ("Пельмени Сибирские 900г",        "g",   180, "Полуфабрикаты"),
    # Хлеб
    ("Хлеб Бородинский 400г",          "g",   5,   "Хлеб"),
    ("Батон нарезной 400г",            "g",   3,   "Хлеб"),
    ("Булочка сдобная 80г",            "g",   2,   "Булочки и сдоба"),
    # Напитки
    ("Сок яблочный Rich 1л",           "l",   365, "Соки"),
    ("Вода Святой Источник 1.5л",      "l",   730, "Вода"),
    ("Вода Черноголовка газ. 1л",      "l",   365, "Газированные напитки"),
    ("Сок апельсиновый Tropicana 1л",  "l",   365, "Соки"),
]


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
            BatchShipment.objects.all().delete()
            Batch.objects.all().delete()
            Product.objects.all().delete()
            Shop.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING("Таблицы очищены"))

        categories  = self._seed_categories()
        shops       = self._seed_shops()
        products    = self._seed_products(categories)
        batches     = self._seed_batches(products)
        self._seed_shipments(batches, shops)

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Готово: {len(categories)} категорий, {len(shops)} магазинов, "
            f"{len(products)} товаров, {len(batches)} партий"
        ))

    # ── Категории ────────────────────────────────────────────────────────────

    def _seed_categories(self):
        self.stdout.write("Создаём категории...")
        cat_map = {}  # name → Category instance

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
        for i, (name, unit, shelf_life, cat_name) in enumerate(PRODUCTS, start=1):
            sku = f"BLG-{i:04d}"
            product, _ = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    "name":            name,
                    "unit":            unit,
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
        batches = []

        for product in products:
            shelf = product.shelf_life_days or 30
            # 2-4 партии на каждый товар
            for _ in range(random.randint(2, 4)):
                # Дата производства — от 60 дней назад до сегодня
                produced_days_ago  = random.randint(0, min(60, shelf - 1))
                production_date    = today - timedelta(days=produced_days_ago)
                expiry_date        = production_date + timedelta(days=shelf)

                qty = random.randint(50, 500)

                # Намеренно создаём несколько просроченных партий
                if random.random() < 0.1:
                    expiry_date = today - timedelta(days=random.randint(1, 10))
                    status      = Batch.Status.WRITTEN_OFF
                    qty_remaining = 0
                else:
                    status        = Batch.Status.AVAILABLE
                    qty_remaining = qty  # будет скорректировано при отгрузках

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
                # Обходим save() чтобы не трогать quantity_remaining автоматически
                Batch.objects.bulk_create([batch])
                batches.append(batch)

        # Перечитываем из БД чтобы получить pk
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
            # Каждая партия частично отгружена в 1-3 магазина
            target_shops   = random.sample(shops, k=random.randint(1, 3))
            available      = batch.quantity_remaining

            if available == 0:
                continue

            for shop in target_shops:
                if available <= 0:
                    break
                # Отгружаем от 10% до 40% партии в каждый магазин
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

            # Обновляем quantity_remaining и статус партии
            batch.quantity_remaining = available
            batch._update_status()

        # Сохраняем всё разом
        BatchShipment.objects.bulk_create(shipments, batch_size=200)
        Batch.objects.bulk_update(
            batches,
            ["quantity_remaining", "status"],
            batch_size=200,
        )

        self.stdout.write(f"  → {len(shipments)} отгрузок")