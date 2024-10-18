from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, NutritionalValue, Ingredient, Product, ProductIngredient, Order, OrderProduct, History


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('role',)}),
    )


class NutritionalValueAdmin(admin.ModelAdmin):
    list_display = ('id', 'calories', 'proteins', 'fats', 'carbohydrates')
    search_fields = ['id']


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_order', 'max_order', 'available', 'price_per_gram')
    list_filter = ('available',)
    search_fields = ['name']


class ProductIngredientInline(admin.TabularInline):
    model = ProductIngredient
    extra = 1


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_official', 'product_type')
    list_filter = ('is_official', 'product_type')
    search_fields = ['name']
    inlines = [ProductIngredientInline]


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 1


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'table', 'order_status', 'order_type', 'payment_type', 'total_price', 'created_at')
    list_filter = ('order_status', 'order_type', 'payment_type')
    search_fields = ['id', 'table__username']
    inlines = [OrderProductInline]


class HistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'order', 'created_at')
    list_filter = ('created_at',)
    search_fields = ['user__username', 'order__id']


admin.site.register(User, CustomUserAdmin)
admin.site.register(NutritionalValue, NutritionalValueAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(History, HistoryAdmin)
