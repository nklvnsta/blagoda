from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User

from .models import (
    Category,
    Shop,
    Product,
    Batch,
    BatchShipment,
    Inventory,
    StockDeviation,
    InventorySnapshot,
    Sales,
    UserProfile,
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0


class UserAdmin(DjangoUserAdmin):
    inlines = (UserProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(BatchShipment)
class BatchShipmentAdmin(admin.ModelAdmin):
    list_display = (
        "batch",
        "shop",
        "quantity_shipped",
        "picked_quantity",
        "pick_status_display",
        "status",
        "planned_dispatch_date",
        "planned_delivery_date",
        "shipped_at",
        "delivered_at",
    )
    list_filter = ("status", "shop", "planned_dispatch_date")
    search_fields = ("shop__name", "batch__product__name", "note")
    date_hierarchy = "planned_dispatch_date"
    ordering = ("-planned_dispatch_date", "-shipped_at")

    @admin.display(description="Сборка")
    def pick_status_display(self, obj: BatchShipment) -> str:
        return BatchShipment.PickStatus(obj.pick_status).label


admin.site.register(Category)
admin.site.register(Shop)
admin.site.register(Product)
admin.site.register(Batch)
admin.site.register(Inventory)
admin.site.register(StockDeviation)
admin.site.register(InventorySnapshot)
admin.site.register(Sales)
