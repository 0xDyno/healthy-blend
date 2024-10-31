from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, NutritionalValue, Ingredient, Product, ProductIngredient, Order, OrderProduct, OrderHistory, Setting, \
    DaySetting, Promo, PromoUsage


class CustomUserAdmin(UserAdmin):
    list_display = ("id", "username", "nickname", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("Custom Fields", {"fields": ("role", "nickname")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (_("Custom Fields"), {"fields": ("role",)}),
    )


class NutritionalValueAdmin(admin.ModelAdmin):
    list_display = ("id", "calories", "proteins", "fats", "carbohydrates")
    search_fields = ["id"]


class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_menu", "is_available", "is_dish_ingredient", "purchase_price", "selling_price", "min_order", "max_order")
    list_filter = ("is_available",)
    search_fields = ["name"]


class ProductIngredientInline(admin.TabularInline):
    model = ProductIngredient
    extra = 1


class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "is_menu", "is_official", "product_type")
    list_filter = ("is_menu", "is_official", "product_type")
    search_fields = ["name"]
    inlines = [ProductIngredientInline]


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 1


class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "order_status", "is_paid", "is_refunded", "order_type", "payment_type", "total_price", "created_at")
    list_filter = ("order_status", "order_type", "payment_type", "is_paid")
    search_fields = ["id", "user__username"]
    inlines = [OrderProductInline]


class HistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "order", "created_at")
    list_filter = ("created_at",)
    search_fields = ["user__username", "order__id"]


class OrderProductAdmin(admin.ModelAdmin):
    list_display = [field.name for field in OrderProduct._meta.fields]


class SettingAdmin(admin.ModelAdmin):
    list_display = ("id", "service", "tax", "minimum_order_amount")


class DaySettingAdmin(admin.ModelAdmin):
    list_display = ("day", "is_open", "open_hours", "close_hours")


class PromoAdmin(admin.ModelAdmin):
    list_display = ("id", "promo_code", "discount", "used_count", "usage_limit", "active_from", "active_until", "creator")
    list_filter = ("creator",)
    search_fields = ["id", "promo_code", "creator"]


class PromoUsageAdmin(admin.ModelAdmin):
    list_display = ("id", "promo", "order", "user", "used_at")


admin.site.register(User, CustomUserAdmin)
admin.site.register(NutritionalValue, NutritionalValueAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderHistory, HistoryAdmin)
admin.site.register(OrderProduct, OrderProductAdmin)
admin.site.register(Setting, SettingAdmin)
admin.site.register(DaySetting, DaySettingAdmin)
admin.site.register(Promo, PromoAdmin)
admin.site.register(PromoUsage, PromoUsageAdmin)
