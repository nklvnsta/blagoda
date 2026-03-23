from django.contrib import admin

# Register your models here.
from .models import Category, Shop, Product, Batch, BatchShipment, Inventory, StockDeviation, InventorySnapshot, Sales

admin.site.register(Category)
admin.site.register(Shop)
admin.site.register(Product)
admin.site.register(Batch)
admin.site.register(BatchShipment)
admin.site.register(Inventory)
admin.site.register(StockDeviation)
admin.site.register(InventorySnapshot)
admin.site.register(Sales)