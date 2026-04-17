from django.contrib import admin

from .models import Category, Shop, Product, Batch, BatchShipment, Inventory, StockDeviation, InventorySnapshot, Sales


@admin.register(BatchShipment)
class BatchShipmentAdmin(admin.ModelAdmin):
    list_display = (
        "batch",
        "shop",
        "quantity_shipped",
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


admin.site.register(Category)
admin.site.register(Shop)
admin.site.register(Product)
admin.site.register(Batch)
admin.site.register(Inventory)
admin.site.register(StockDeviation)
admin.site.register(InventorySnapshot)
admin.site.register(Sales)