from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from core.views import *

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

    path("manage/kitchen/", kitchen, name="kitchen"),
    path("manage/orders/control/", orders_control, name="orders_manage_control"),
    path("manage/orders/all/", orders_all, name="orders_manage_all"),
    path("manage/ingredients/", ingredient_management, name="ingredient_management"),
    path("manage/products/", product_management, name="product_management"),

    # API URLs
    path("api/get/products/", api_get_all_products),
    path("api/get/ingredient/<int:pk>/", api_get_ingredient),
    path("api/get/ingredients/", api_get_all_ingredients),
    path("api/get/order/table/", api_get_order_table),
    path("api/get/order/<int:pk>/", api_get_order),
    path("api/get/orders/", api_get_orders),
    path("api/get/orders/kitchen/", api_get_orders_kitchen),
    path("api/update/order/<int:pk>/", api_update_order),
    path("api/update/ingredient/<int:pk>/", api_update_ingredient),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
