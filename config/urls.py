from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from core.views import *
from core import api

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),

    # CUSTOMER
    path("", home, name="home"),
    path("custom/", custom_meal, name="custom_meal"),
    path("ingredient/<int:ingredient_id>/", custom_add, name="ingredient_detail"),
    path("cart/", cart, name="cart"),
    path("last-order/", last_order, name="last_order"),

    # API
    path("api/get/products/", api.get_all_products),
    path("api/get/ingredients/", api.get_ingredients),
    path("api/get/ingredient/<int:pk>/", api.get_ingredient),
    path("api/get/order/last/", api.get_order_last),
    path("api/check/promo/<str:promo_code>/", api.check_promo),
    path("api/checkout/", api.checkout, name="checkout"),

    # CONTROL
    path("control/orders/", orders_control, name="orders_control"),
    path("control/orders/all/", orders_control_all, name="orders_control_all"),
    path("control/ingredients/", ingredient_control, name="ingredients_control"),
    path("control/products/", product_control, name="products_control"),
    path("control/promo/", promo_control, name="promo_control"),
    path("control/kitchen/orders/", kitchen_orders, name="kitchen"),
    path("control/kitchen/ingredients/", kitchen_ingredients, name="kitchen_ingredients"),

    # API
    path("api/control/get/products/", api.get_all_products_control),
    path("api/control/get/product/<int:pk>/", api.get_product_control),
    path("api/control/update/product/<int:pk>/", api.update_product_control),

    path("api/control/get/ingredients/", api.get_ingredients_control),
    path("api/control/get/ingredient/<int:pk>/", api.get_ingredient_control),
    path("api/control/update/ingredient/<int:pk>/", api.update_ingredient_control),
    path("api/control/create/ingredient/", api.create_ingredient_control),

    path("api/control/get/orders/", api.get_orders_control),
    path("api/control/get/order/<int:pk>/", api.get_order_control),
    path("api/control/update/order/<int:pk>/", api.update_order_control),

    path("api/control/get/promos/", api.get_promos),
    path("api/control/get/promo/<int:pk>/", api.get_promo),
    path("api/control/update/promo/<int:pk>/", api.update_promo),
    path("api/control/create/promo/", api.create_promo),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
