from django.contrib import admin
from .orders.models.order import Order
from .transactions.models.transaction import Transaction
from .products.models.product import Product
from .titles.models.title import Title


class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "address", "full_name", "telephone", "comment"]
    search_fields = ["user__username", "full_name", "address", "id", "telephone"]
    list_filter = ["user", "address", "full_name"]
    ordering = ("id", "user__id")
    list_per_page = 50


class TransactionAdmin(admin.ModelAdmin):
    list_display = ["user", "id", "timestamp", "action", "points", "reason"]
    search_fields = ["user__username", "action", "reason", "id"]
    list_filter = ["user", "action", "reason"]
    date_hierarchy = "timestamp"
    ordering = ("id", "user__id", "-timestamp")
    list_per_page = 50


class TitleAdmin(admin.ModelAdmin):
    list_display = ["name", "points", "color", "id"]
    search_fields = ["name", "id", "color"]
    list_filter = ["name"]
    ordering = ("id", "-points")
    list_per_page = 50


class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "points", "quantity", "details", "id"]
    search_fields = ["id", "name", "details"]
    list_filter = ["name", "points"]
    ordering = ("id", "-points", "-quantity")
    list_per_page = 55


admin.site.register(Order, OrderAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Title, TitleAdmin)
admin.site.register(Product, ProductAdmin)
