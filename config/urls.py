from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from core.views import (
    api_get_orders, api_get_all_products, api_get_ingredient, api_get_all_ingredients, api_get_order, api_update_order,
    home, user_login, user_logout, custom_meal, custom_add, cart, checkout, last_order,
    kitchen, order_management, product_management, ingredient_management)

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", home, name="home"),
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),

    path("custom-meal/", custom_meal, name="custom_meal"),
    path("ingredient/<int:ingredient_id>/", custom_add, name="ingredient_detail"),
    path("cart/", cart, name="cart"),
    path("checkout/", checkout, name="checkout"),
    path("last-order/", last_order, name="last_order"),

    path("kitchen/", kitchen, name="kitchen"),
    path("order-management/", order_management, name="order_management"),
    path("ingredient-management/", ingredient_management, name="ingredient_management"),
    path("product-management/", product_management, name="product_management"),

    # API URLs
    path("api/get/products/", api_get_all_products),
    path("api/get/ingredient/<int:pk>/", api_get_ingredient),
    path("api/get/ingredients/", api_get_all_ingredients),
    path("api/get/order/<int:pk>/", api_get_order),
    path("api/get/orders/", api_get_orders),
    path("api/update/order/<int:pk>/", api_update_order),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
