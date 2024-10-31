from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from core.views import *
from core import api

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", home, name="home"),
    path("login/", user_login, name="login"),
    path("logout/", user_logout, name="logout"),

    path("custom/", custom_meal, name="custom_meal"),
    path("ingredient/<int:ingredient_id>/", custom_add, name="ingredient_detail"),
    path("cart/", cart, name="cart"),
    path("checkout/", checkout, name="checkout"),
    path("last-order/", last_order, name="last_order"),

    path("manage/orders/control/", orders_control, name="orders_manage_control"),
    path("manage/orders/all/", orders_all, name="orders_manage_all"),
    path("manage/ingredients/", ingredient_management, name="ingredient_management"),
    path("manage/products/", product_management, name="product_management"),
    path("kitchen/", kitchen_orders, name="kitchen"),
    path("kitchen/ingredients/", kitchen_ingredients, name="kitchen_ingredients"),

    # API URLs - customer
    path("api/get/products/", api.get_all_products),
    path("api/get/ingredients/", api.get_ingredients),
    path("api/get/ingredient/<int:pk>/", api.get_ingredient),
    path("api/get/order/last/", api.get_order_last),

    # APU URLs - control
    path("api/control/get/products/", api.get_all_products_control),

    path("api/control/get/ingredients/", api.get_ingredients_control),
    path("api/control/get/ingredient/<int:pk>/", api.get_ingredient_control),
    path("api/control/update/ingredient/<int:pk>/", api.update_ingredient_control),
    path("api/control/create/ingredient/", api.create_ingredient_control),

    path("api/control/get/orders/", api.get_orders_control),
    path("api/control/get/order/<int:pk>/", api.get_order_control),
    path("api/control/update/order/<int:pk>/", api.update_order),

    path("api/control/check/promo/<str:promo_code>/", api.check_promo),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
