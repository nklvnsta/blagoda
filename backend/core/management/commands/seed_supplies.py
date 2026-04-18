"""
python manage.py seed_supplies [--clear]

Создаёт демо-данные для страницы «Поставки»:
  - scheduled-отгрузки, запланированные на завтра (для панели «К отгрузке завтра»)
  - in_transit-отгрузки, отправленные сегодня (для панели «В пути»)
  - несколько delivered-отгрузок, прибывших сегодня (для KPI «Отгружено сегодня»)

Команду можно запускать после обычного `seed` — она использует уже созданные
партии и магазины. Пустые/просроченные партии пропускаются.
"""

import random
from datetime import date, timedelta, datetime, time
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import Batch, BatchShipment, Shop


class Command(BaseCommand):
    help = "Наполняет демо-данными страницу «Поставки» (scheduled / in_transit / delivered за сегодня)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Удалить ранее созданные scheduled/in_transit-записи (delivered не трогаются)",
        )
        parser.add_argument(
            "--scheduled-shops",
            type=int,
            default=3,
            help="Сколько магазинов получат поставку завтра (по умолчанию 3)",
        )
        parser.add_argument(
            "--in-transit-shops",
            type=int,
            default=3,
            help="Сколько магазинов имеют поставку в пути (по умолчанию 3)",
        )
        parser.add_argument(
            "--delivered-shops",
            type=int,
            default=1,
            help="Сколько магазинов уже получили поставку сегодня (по умолчанию 1)",
        )
        parser.add_argument(
            "--picking-shops",
            type=int,
            default=8,
            help="Сколько магазинов получат сборку на сегодня (по умолчанию 8)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        today    = date.today()
        tomorrow = today + timedelta(days=1)

        if options["clear"]:
            removed = BatchShipment.objects.filter(
                status__in=[
                    BatchShipment.Status.SCHEDULED,
                    BatchShipment.Status.IN_TRANSIT,
                ]
            ).delete()
            self.stdout.write(self.style.WARNING(
                f"Удалено scheduled/in_transit записей: {removed[0]}"
            ))

        shops = list(Shop.objects.filter(is_active=True).order_by("name"))
        if not shops:
            self.stdout.write(self.style.ERROR(
                "Нет активных магазинов. Сначала запустите `python manage.py seed`."
            ))
            return

        available_batches = list(
            Batch.objects
            .filter(status__in=[Batch.Status.AVAILABLE, Batch.Status.PARTIAL])
            .filter(quantity_remaining__gt=0)
            .select_related("product")
        )
        if not available_batches:
            self.stdout.write(self.style.ERROR(
                "Нет партий с остатком на складе. Сначала запустите `python manage.py seed`."
            ))
            return

        scheduled = self._create_group(
            batches=available_batches,
            shops=random.sample(shops, k=min(options["scheduled_shops"], len(shops))),
            status=BatchShipment.Status.SCHEDULED,
            planned_dispatch_date=tomorrow,
            planned_delivery_date=tomorrow + timedelta(days=1),
            shipped_at=timezone.make_aware(datetime.combine(tomorrow, time(8, 0))),
            delivered_at=None,
            positions_per_shop=(8, 20),
        )

        in_transit = self._create_group(
            batches=available_batches,
            shops=random.sample(shops, k=min(options["in_transit_shops"], len(shops))),
            status=BatchShipment.Status.IN_TRANSIT,
            planned_dispatch_date=today,
            planned_delivery_date=today,
            shipped_at=timezone.now(),
            delivered_at=None,
            positions_per_shop=(6, 15),
        )

        delivered = self._create_group(
            batches=available_batches,
            shops=random.sample(shops, k=min(options["delivered_shops"], len(shops))),
            status=BatchShipment.Status.DELIVERED,
            planned_dispatch_date=today,
            planned_delivery_date=today,
            shipped_at=timezone.now() - timedelta(hours=4),
            delivered_at=timezone.now() - timedelta(hours=1),
            positions_per_shop=(4, 10),
        )

        # Сборки на сегодня для страницы «Сбор заказа»: scheduled-строки с
        # dispatch_date = today и заранее проставленным picked_quantity,
        # чтобы среди магазинов встретились все 4 статуса группы.
        picking = self._create_picking_today(
            batches=available_batches,
            shops=random.sample(
                shops, k=min(options["picking_shops"], len(shops))
            ),
            today=today,
        )

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Готово:\n"
            f"  К отгрузке завтра:   {scheduled} позиций\n"
            f"  В пути:              {in_transit} позиций\n"
            f"  Доставлено сегодня:  {delivered} позиций\n"
            f"  К сборке на сегодня: {picking} позиций"
        ))

    # ── helpers ──────────────────────────────────────────────────────────────

    def _create_group(
        self,
        batches,
        shops,
        status,
        planned_dispatch_date,
        planned_delivery_date,
        shipped_at,
        delivered_at,
        positions_per_shop,
    ) -> int:
        """
        Для каждого магазина выбираем случайный набор партий и создаём
        BatchShipment-линии с заданным статусом. Возвращает общее число линий.
        """
        if not shops or not batches:
            return 0

        total_lines = 0
        consuming = status in (
            BatchShipment.Status.IN_TRANSIT,
            BatchShipment.Status.DELIVERED,
        )

        for shop in shops:
            lines_count = random.randint(*positions_per_shop)
            picked = random.sample(batches, k=min(lines_count, len(batches)))

            for batch in picked:
                if batch.quantity_remaining <= 0:
                    continue
                max_qty = max(1, int(batch.quantity_remaining * 0.3))
                qty = random.randint(1, max(1, min(max_qty, batch.quantity_remaining)))

                BatchShipment.objects.create(
                    batch                 = batch,
                    shop                  = shop,
                    quantity_shipped      = qty,
                    status                = status,
                    planned_dispatch_date = planned_dispatch_date,
                    planned_delivery_date = planned_delivery_date,
                    shipped_at            = shipped_at,
                    delivered_at          = delivered_at,
                )
                total_lines += 1

                if consuming:
                    batch.refresh_from_db(fields=["quantity_remaining"])

        return total_lines

    def _create_picking_today(self, batches, shops, today) -> int:
        """
        Создаёт scheduled-строки на сегодня и проставляет picked_quantity так,
        чтобы среди магазинов встретились все 4 статуса группы:
          not_started / in_progress / partial / picked.
        Распределение: ~3 not_started, ~2 picked, ~2 partial, остальные mixed.
        """
        if not shops or not batches:
            return 0

        if len(shops) < 4:
            patterns = ["not_started", "picked", "partial", "in_progress"][: len(shops)]
        else:
            patterns = (
                ["not_started"] * max(1, len(shops) // 3)
                + ["picked"] * max(1, len(shops) // 4)
                + ["partial"] * max(1, len(shops) // 4)
            )
            while len(patterns) < len(shops):
                patterns.append("in_progress")
            patterns = patterns[: len(shops)]
        random.shuffle(patterns)

        ship_at = timezone.make_aware(datetime.combine(today, time(8, 0)))
        total_lines = 0

        for shop, pattern in zip(shops, patterns):
            lines_count = random.randint(5, 12)
            picked_batches = random.sample(batches, k=min(lines_count, len(batches)))

            created_lines: list[BatchShipment] = []
            for batch in picked_batches:
                if batch.quantity_remaining <= 0:
                    continue
                max_qty = max(1, int(batch.quantity_remaining * 0.3))
                qty = random.randint(1, max(1, min(max_qty, batch.quantity_remaining)))

                line = BatchShipment.objects.create(
                    batch                 = batch,
                    shop                  = shop,
                    quantity_shipped      = qty,
                    status                = BatchShipment.Status.SCHEDULED,
                    planned_dispatch_date = today,
                    planned_delivery_date = today,
                    shipped_at            = ship_at,
                    picked_quantity       = 0,
                )
                created_lines.append(line)

            self._apply_pick_pattern(created_lines, pattern)
            total_lines += len(created_lines)

        return total_lines

    def _apply_pick_pattern(self, lines: list, pattern: str) -> None:
        """Заполняет picked_quantity у строк по выбранному паттерну группы."""
        if not lines:
            return

        if pattern == "not_started":
            # все строки picked == 0 (default), ничего не делаем
            return

        if pattern == "picked":
            for line in lines:
                line.picked_quantity = line.quantity_shipped
                line.save(update_fields=["picked_quantity"])
            return

        if pattern == "partial":
            # хотя бы одна partial-строка; остальные — random not_started/picked
            partial_idx = random.randrange(len(lines))
            for i, line in enumerate(lines):
                if i == partial_idx:
                    line.picked_quantity = max(1, line.quantity_shipped // 2)
                else:
                    line.picked_quantity = (
                        line.quantity_shipped if random.random() < 0.5 else 0
                    )
                line.save(update_fields=["picked_quantity"])
            return

        if pattern == "in_progress":
            # есть picked-строки и not_started-строки, но нет partial.
            # Гарантируем хотя бы по одной такой строке.
            picked_idx = random.randrange(len(lines))
            for i, line in enumerate(lines):
                if i == picked_idx:
                    line.picked_quantity = line.quantity_shipped
                else:
                    line.picked_quantity = (
                        line.quantity_shipped if random.random() < 0.5 else 0
                    )
                line.save(update_fields=["picked_quantity"])
            return
