from django.contrib import admin

from .models import Category, Coupon, Customer, Order, OrderItem, Product, Store


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "plan", "is_live", "trial_ends_at", "created_at")
    list_filter = ("plan", "is_live", "theme")
    search_fields = ("name", "slug", "owner__email")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "store", "price", "stock", "is_active", "ai_generated")
    list_filter = ("is_active", "ai_generated", "store")
    search_fields = ("title", "sku", "tags")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "store", "shipping_name", "total", "status", "payment_method", "risk_score", "created_at")
    list_filter = ("status", "payment_method", "courier", "source")
    search_fields = ("number", "shipping_name", "shipping_phone")
    inlines = [OrderItemInline]


admin.site.register(Category)
admin.site.register(Customer)
admin.site.register(Coupon)
