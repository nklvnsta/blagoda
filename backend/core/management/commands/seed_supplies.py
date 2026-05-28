"""
python manage.py seed_supplies [--clear]

Демо-данные для страниц «Поставки» и «Сбор заказа»:

  На сегодня (разные магазины, без пересечений):
    - delivered   — уже доставлены
    - in_transit  — в пути
    - ready_to_ship — сборка завершена, ждут отправки
    - scheduled   — ещё не собраны (в очереди сборки)

  На завтра (отдельные магазины):
    - scheduled   — запланированы к отгрузке

Важно: магазины для каждой группы не пересекаются, чтобы в таблице
«Поставки» групповой статус корректно отражал реальный статус поставки,
а не «scheduled» из-за наличия хотя бы одной scheduled-линии.
"""

import random
from datetime import timedelta, datetime, time
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.timezone import localdate

from core.models import Batch, BatchShipment, Shop


class Command(BaseCommand):
    help = "Наполняет демо-данными страницы «Поставки» и «Сбор заказа»"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Удалить ранее созданные активные отгрузки перед заполнением",
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
            help="Сколько магазинов имеют поставку в пути сегодня (по умолчанию 3)",
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
            default=6,
            help="Сколько магазинов получат сборку на сегодня (по умолчанию 6)",
        )
        parser.add_argument(
            "--ready-shops",
            type=int,
            default=2,
            help="Из picking-shops: сколько будут переведены в ready_to_ship (по умолчанию 2)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        today    = localdate()
        tomorrow = today + timedelta(days=1)

        if options["clear"]:
            removed = BatchShipment.objects.filter(
                status__in=[
                    BatchShipment.Status.SCHEDULED,
                    BatchShipment.Status.READY_TO_SHIP,
                    BatchShipment.Status.IN_TRANSIT,
                ]
            ).delete()
            self.stdout.write(self.style.WARNING(
                f"Удалено записей: {removed[0]}"
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

        # Разбиваем магазины на непересекающиеся группы, чтобы в таблице
        # «Поставки» групповой статус совпадал с реальным.
        pool = list(shops)
        random.shuffle(pool)
        idx = 0

        def take(n: int) -> list:
            nonlocal idx
            n = min(n, len(pool) - idx)
            chunk = pool[idx: idx + n]
            idx += n
            return chunk

        n_delivered = options["delivered_shops"]
        n_in_transit = options["in_transit_shops"]
        n_picking = options["picking_shops"]
        n_ready = min(options["ready_shops"], n_picking)
        n_scheduled_tomorrow = options["scheduled_shops"]

        delivered_shops       = take(n_delivered)
        in_transit_shops      = take(n_in_transit)
        picking_all_shops     = take(n_picking)
        tomorrow_shops        = take(n_scheduled_tomorrow)

        # Из picking_all_shops часть будет переведена в ready_to_ship
        ready_shops    = picking_all_shops[:n_ready]
        picking_shops  = picking_all_shops[n_ready:]

        # ── создаём группы ────────────────────────────────────────────────

        delivered_cnt = self._create_group(
            batches=available_batches,
            shops=delivered_shops,
            status=BatchShipment.Status.DELIVERED,
            planned_dispatch_date=today,
            planned_delivery_date=today,
            shipped_at=timezone.now() - timedelta(hours=4),
            delivered_at=timezone.now() - timedelta(hours=1),
            positions_per_shop=(4, 10),
        )

        in_transit_cnt = self._create_group(
            batches=available_batches,
            shops=in_transit_shops,
            status=BatchShipment.Status.IN_TRANSIT,
            planned_dispatch_date=today,
            planned_delivery_date=today,
            shipped_at=timezone.now(),
            delivered_at=None,
            positions_per_shop=(6, 15),
        )

        scheduled_tomorrow_cnt = self._create_group(
            batches=available_batches,
            shops=tomorrow_shops,
            status=BatchShipment.Status.SCHEDULED,
            planned_dispatch_date=tomorrow,
            planned_delivery_date=tomorrow + timedelta(days=1),
            shipped_at=timezone.make_aware(datetime.combine(tomorrow, time(8, 0))),
            delivered_at=None,
            positions_per_shop=(8, 20),
        )

        # Сборки: создаём scheduled-строки с picked_quantity-паттернами
        picking_cnt = self._create_picking_today(
            batches=available_batches,
            shops=picking_shops,
            today=today,
        )

        # ready_to_ship: сначала создаём как «полностью собранные» scheduled,
        # затем переводим в ready_to_ship
        ready_picking_cnt = self._create_picking_today(
            batches=available_batches,
            shops=ready_shops,
            today=today,
            force_pattern="picked",
        )
        ready_cnt = self._promote_to_ready(shops=ready_shops, today=today)

        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Готово:\n"
            f"  Доставлено сегодня:  {delivered_cnt} позиций\n"
            f"  В пути сегодня:      {in_transit_cnt} позиций\n"
            f"  Готов к отправке:    {ready_cnt} позиций  (из {ready_picking_cnt} собранных)\n"
            f"  К сборке (scheduled):{picking_cnt} позиций\n"
            f"  К отгрузке завтра:   {scheduled_tomorrow_cnt} позиций"
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
        if not shops or not batches:
            return 0

        consuming = status in (
            BatchShipment.Status.IN_TRANSIT,
            BatchShipment.Status.DELIVERED,
        )
        total_lines = 0

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

    def _create_picking_today(
        self, batches, shops, today, force_pattern: str | None = None
    ) -> int:
        """
        Создаёт scheduled-строки на сегодня с проставленным picked_quantity.
        force_pattern — если задан, применяется ко всем магазинам.
        """
        if not shops or not batches:
            return 0

        if force_pattern:
            patterns = [force_pattern] * len(shops)
        elif len(shops) < 4:
            patterns = ["not_started", "picked", "partial", "in_progress"][: len(shops)]
        else:
            patterns = (
                ["not_started"] * max(1, len(shops) // 3)
                + ["picked"]      * max(1, len(shops) // 4)
                + ["partial"]     * max(1, len(shops) // 4)
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

    def _promote_to_ready(self, shops, today) -> int:
        """
        Переводит scheduled-строки с picked_quantity > 0 в ready_to_ship.
        Списания не происходит — оно выполнится при отправке с «Поставок».
        """
        if not shops:
            return 0

        total = 0
        for shop in shops:
            lines = list(
                BatchShipment.objects.filter(
                    shop=shop,
                    status=BatchShipment.Status.SCHEDULED,
                    planned_dispatch_date=today,
                    picked_quantity__gt=0,
                )
            )
            for line in lines:
                line.quantity_shipped = line.picked_quantity
                line.status = BatchShipment.Status.READY_TO_SHIP
                line.save(update_fields=["quantity_shipped", "status"])
                total += 1

        return total

    def _apply_pick_pattern(self, lines: list, pattern: str) -> None:
        """Заполняет picked_quantity у строк по выбранному паттерну группы."""
        if not lines:
            return

        if pattern == "not_started":
            return

        if pattern == "picked":
            for line in lines:
                line.picked_quantity = line.quantity_shipped
                line.save(update_fields=["picked_quantity"])
            return

        if pattern == "partial":
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
