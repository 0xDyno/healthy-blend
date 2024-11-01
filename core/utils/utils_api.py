from datetime import timedelta, datetime

from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from core.models import Ingredient, Order, DaySetting, PromoUsage


def get_all_products(products: list):
    """ Uses to make orders by Customers"""
    data = []
    for product in products:
        product_info = {"id": product.id,
                        "product_type": product.product_type,
                        "name": product.name,
                        "description": product.description,
                        "image": product.image.url if product.image else "/static/icons/manage/no_image.png",
                        "weight": product.weight,
                        "price": product.get_selling_price(),
                        "ingredients": [],
                        "nutritional_value": product.nutritional_value.to_dict()}
        for pi in product.productingredient_set.all():
            ingredient_info = {"id": pi.ingredient.id,
                               "name": pi.ingredient.name,
                               "weight_grams": pi.weight_grams,
                               "nutritional_value": pi.ingredient.nutritional_value.to_dict(),
                               "price": pi.ingredient.get_selling_price()}
            product_info.get("ingredients").append(ingredient_info)
        data.append(product_info)
    return data


def get_products_data(product, is_full=False, is_admin=False):
    """ Uses in Control Panel"""
    data = {
        "id": product.id,
        "name": product.name,
        "image": product.image.url if product.image else "/static/icons/manage/no_image.png",
        "product_type": product.product_type,
        "is_menu": product.is_menu,
        "is_official": product.is_official,
        "is_available": product.is_available,
        "is_enabled": product.is_enabled,
        "selling_price": product.selling_price,
    }

    if is_full:
        data["description"] = product.description
        data["is_official"] = product.is_official
        data["nutritional_value"] = product.nutritional_value.to_dict()
        data["lack_of_ingredients"] = []
        data["ingredients"] = []
        for pi in product.productingredient_set.all():
            ingredient_info = {"id": pi.ingredient.id,
                               "name": pi.ingredient.name,
                               "weight_grams": pi.weight_grams}
            data.get("ingredients").append(ingredient_info)

        if product.lack_of_ingredients.exists():
            for ingredient in product.lack_of_ingredients.all():
                ingredient_data = {"name": ingredient.name}
                data["lack_of_ingredients"].append(ingredient_data)

    if is_admin:
        if not product.price:
            product.save()
        data["ingredients_price"] = product.price
    return data


def get_ingredient_data(ingredient: Ingredient):
    """ Uses to make orders by Customers"""
    return {
        "id": ingredient.id,
        "name": ingredient.name,
        "description": ingredient.description,
        "image": ingredient.image.url,
        "ingredient_type": ingredient.ingredient_type,
        "step": ingredient.step,
        "min_order": ingredient.min_order,
        "max_order": ingredient.max_order,
        "is_available": ingredient.is_available,
        "price": ingredient.selling_price if ingredient.selling_price else ingredient.purchase_price * ingredient.price_multiplier,
        "is_dish_ingredient": ingredient.is_dish_ingredient,
        "nutritional_value": ingredient.nutritional_value.to_dict() if ingredient.nutritional_value else None,
    }


def get_ingredient_data_lite(ingredient: Ingredient, admin=False):
    """ Uses to show base info on Control Panel"""
    data = {
        "id": ingredient.id,
        "name": ingredient.name,
        "image": ingredient.image.url if ingredient.image else "/static/icons/manage/no_image.png",
        "ingredient_type": ingredient.ingredient_type,
        "is_available": ingredient.is_available,
    }
    if admin:
        data["is_menu"] = ingredient.is_menu
        data["selling_price"] = ingredient.selling_price
    return data


def get_ingredient_data_full(ingredient: Ingredient):
    """ Uses to show Full info on Control Panel"""
    return {
        "id": ingredient.id,
        "name": ingredient.name,
        "description": ingredient.description,
        "image": ingredient.image.url,
        "ingredient_type": ingredient.ingredient_type,
        "step": ingredient.step,
        "min_order": ingredient.min_order,
        "max_order": ingredient.max_order,
        "is_available": ingredient.is_available,
        "is_dish_ingredient": ingredient.is_dish_ingredient,
        "is_menu": ingredient.is_menu,
        "purchase_price": ingredient.purchase_price,
        "selling_price": ingredient.selling_price,
        "nutritional_value": ingredient.nutritional_value.to_dict() if ingredient.nutritional_value else None,
    }


def get_order_general(order: Order):
    data_to_send = {
        "id": order.id,
        "user_nickname": order.user.nickname if order.user.nickname else f"id {order.user.id}",
        "user_role": order.user.role.capitalize(),
        "order_status": order.order_status,
        "order_type": order.order_type,
        "payment_type": order.payment_type,
        "tax": order.tax,
        "service": order.service,
        "base_price": order.base_price,
        "total_price": order.total_price,
        "payment_id": order.payment_id,
        "is_paid": order.is_paid,
        "is_refunded": order.is_refunded,
        "created_at": order.created_at,
        "paid_at": order.paid_at,
        "ready_at": order.ready_at,
        "refunded_at": order.refunded_at,
        "public_note": order.public_note,
    }
    return data_to_send


def get_orders_general(orders):
    return [get_order_general(order) for order in orders]


def get_order_full(order):
    data_to_send = {
        "id": order.id,
        "user_role": order.user.role,
        "user_nickname": order.user.nickname if order.user.nickname else f"id {order.user.id}",
        "order_status": order.order_status,
        "order_type": order.order_type,
        "payment_type": order.payment_type,
        "tax": order.tax,
        "service": order.service,
        "base_price": order.base_price,
        "total_price": order.total_price,
        "payment_id": order.payment_id,
        "is_paid": order.is_paid,
        "is_refunded": order.is_refunded,
        "created_at": order.created_at,
        "paid_at": order.paid_at,
        "ready_at": order.ready_at,
        "refunded_at": order.refunded_at,
        "public_note": order.public_note,
        "private_note": order.private_note,
        "nutritional_value": order.nutritional_value.to_dict(),
        "products": [],
    }

    if order.promo_usage:
        data_to_send["promo"] = {
            "promo_code": order.promo_usage.promo.promo_code,
            "discount": order.promo_usage.promo.discount,
            "discounted": order.promo_usage.discounted,
        }

    # product -> Product
    # order_product -> OrderProduct
    for order_product in order.products.all():
        product = order_product.product
        product_data = {
            "id": product.id,
            "name": product.name,
            "weight": product.weight,
            "price": order_product.price,
            "amount": order_product.amount,
            "is_official": product.is_official,
            "do_blend": order_product.do_blend,
            "nutritional_value": product.nutritional_value.to_dict() if product.nutritional_value else None,
            "ingredients": [],
        }

        for product_ingredient in product.productingredient_set.all():
            ingredient = product_ingredient.ingredient
            ingredient_data = {
                "name": ingredient.name,
                "weight_grams": product_ingredient.weight_grams,
            }
            product_data["ingredients"].append(ingredient_data)

        data_to_send["products"].append(product_data)
    return data_to_send


def get_order_last(order: Order):
    data_to_send = {
        "id": order.id,
        "order_status": order.get_order_status_display(),
        "payment_type": order.payment_type,
        "tax": order.tax,
        "service": order.service,
        "base_price": order.base_price,
        "total_price": order.total_price,
        "created_at": order.created_at,
        "is_paid": order.is_paid,
        "public_note": order.public_note,
        "paid_at": order.paid_at if order.paid_at else None,
        "nutritional_value": order.nutritional_value.to_dict(),
        "products": [],
    }
    for order_product in order.products.all():
        product_data = {
            "product_id": order_product.id,
            "product_name": order_product.product.name,
            "price": order_product.price,
            "amount": order_product.amount,
            "do_blend": order_product.do_blend,
            "is_official": order_product.product.is_official,
        }
        data_to_send["products"].append(product_data)
    return data_to_send


def get_order_for_kitchen(order: Order):
    data_to_send = {
        "id": order.id,
        "order_type": order.order_type,
        "paid_at": order.paid_at,
        "public_note": order.public_note,
        "private_note": order.private_note,
        "products": [],
    }

    for order_product in order.products.all():
        product = order_product.product
        product_data = {
            "product_name": product.name,
            "amount": order_product.amount,
            "is_official": product.is_official,
            "do_blend": order_product.do_blend,
            "ingredients": [],
        }

        for product_ingredient in product.productingredient_set.all():
            ingredient = product_ingredient.ingredient
            ingredient_data = {
                "id": ingredient.id,
                "name": ingredient.name,
                "weight_grams": product_ingredient.weight_grams,
                "ingredient_type": ingredient.ingredient_type,
            }
            product_data["ingredients"].append(ingredient_data)

        data_to_send["products"].append(product_data)
    return data_to_send


def get_orders_for_kitchen(orders: list):
    return [get_order_for_kitchen(order) for order in orders]


def can_edit_order(order):
    current_time = timezone.now()
    current_day = current_time.weekday()

    # 1. Check Now - working day & working hours
    today_settings = DaySetting.objects.get(day=current_day)

    if not today_settings.is_open:
        return False

    today_open_time = timezone.make_aware(datetime.combine(current_time.date(), today_settings.open_hours))
    today_close_time = timezone.make_aware(datetime.combine(current_time.date(), today_settings.close_hours))

    if not today_open_time <= current_time <= today_close_time:
        return False

    # 2. Check Order time
    if order.created_at.date() != current_time.date():
        return False

    return True


def can_edit_order_second_option(order):
    """
    Currently. Returns True If:
    - Today is working Day and Time
    - Order was created in the last 2 days
    :param order:
    :param user:
    :return:
    """
    # Get today time
    current_time = timezone.now()

    # Get Day when the Order was created
    order_day_settings = DaySetting.objects.get(day=order.created_at.weekday())

    # If it's - working day -> go next
    if order_day_settings.is_open:
        # Get working open TIME for that day
        order_day_open_time = timezone.make_aware(datetime.combine(order.created_at.date(), order_day_settings.open_hours))
        # Get working close TIME for that day
        order_day_close_time = timezone.make_aware(datetime.combine(order.created_at.date(), order_day_settings.close_hours))

        # If current time (when they want to edit) in (open - HERE - close) -> OKay
        if order_day_open_time <= current_time <= order_day_close_time:
            return True

    # Same check for next day. If current time in time_range for next day (from the order creation) -Ok
    next_day_settings = DaySetting.objects.get(day=(order.created_at.weekday() + 1) % 7)

    if next_day_settings.is_open:
        next_day_open_time = timezone.make_aware(
            datetime.combine((order.created_at + timedelta(days=1)).date(), next_day_settings.open_hours))
        next_day_close_time = timezone.make_aware(
            datetime.combine((order.created_at + timedelta(days=1)).date(), next_day_settings.close_hours))

        return next_day_open_time <= current_time <= next_day_close_time

    return False


def filter_orders(request, orders):
    search = request.GET.get("search", "")
    table_id = request.GET.get("table_id", "")

    order_status = request.GET.get("status", "")
    order_type = request.GET.get("order_type", "")

    payment_type = request.GET.get("payment_type", "")
    payment_id = request.GET.get("payment_id", "")

    is_paid = request.GET.get("is_paid", "")
    is_refunded = request.GET.get("is_refunded", "")

    orders_date = request.GET.get("date", "")

    sort_by = request.GET.get("sort_by", "-created_at")

    if search:
        orders = orders.filter(id__icontains=search)
    if table_id:
        orders = orders.filter(id__icontains=table_id)
    if order_status:
        orders = orders.filter(order_status=order_status)
    if order_type:
        orders = orders.filter(order_type=order_type)
    if payment_id:
        orders = orders.filter(payment_id__icontains=payment_id)
    if payment_type:
        orders = orders.filter(payment_type=payment_type)
    if is_paid == "true":
        orders = orders.filter(is_paid=True)
    if is_refunded == "true":
        orders = orders.filter(is_refunded=True)
    if orders_date:
        date_obj = parse_date(orders_date)
        orders = orders.filter(created_at__date=date_obj)

    # Apply sorting
    if sort_by == "created_at_asc":
        orders = orders.order_by("created_at")
    else:
        orders = orders.order_by("-created_at")
    return orders


def filter_products(request, products):
    # Get filter parameters from request.GET
    search = request.GET.get('search', '').lower()
    product_type = request.GET.get('type', '').lower()

    # Get boolean filters
    is_available = request.GET.get('available') == 'true'
    is_enabled = request.GET.get('enabled') == 'true'
    is_official = request.GET.get('official') == 'true'
    is_menu = request.GET.get('menu') == 'true'

    # Search filter
    if search:
        products = products.filter(Q(name__icontains=search) | Q(id__icontains=search))

    # Type filter
    if product_type:
        products = products.filter(product_type__iexact=product_type)

    # Status filters
    if is_available:
        products = products.filter(is_available=True)
    if is_enabled:
        products = products.filter(is_enabled=True)
    if is_official:
        products = products.filter(is_official=True)
    if is_menu:
        products = products.filter(is_menu=True)

    return products


def get_promo_data(promo, full=False):
    creator_name = f"{promo.creator.nickname} ({promo.creator.role})" if promo.creator.nickname \
        else f"{promo.creator.role.capitalize()} #{promo.creator.id}"
    data = {
        "id": promo.id,
        "promo_code": promo.promo_code,
        "discount": promo.discount,
        "is_enabled": promo.is_enabled,
        "is_active": promo.is_active(),
        "is_finished": promo.is_finished,
        "active_from": promo.active_from,
        "active_until": promo.active_until,
        "usage_limit": promo.usage_limit,
        "used_count": promo.used_count,
        "creator": creator_name,
    }
    if full:
        usage_data = PromoUsage.objects.filter(promo=promo).select_related('user', 'order')
        total_discounted = 0
        usage_list = []

        for usage in usage_data:
            usage_info = {
                'user_role': usage.user.role if usage.user else None,
                'user_nickname': usage.user.nickname if usage.user else None,
                'order_id': usage.order.id if usage.order else None,
                'order_base_price': usage.order.base_price if usage.order else None,
                'discounted': usage.discounted,
                'used_at': usage.used_at
            }
            total_discounted += usage.discounted
            usage_list.append(usage_info)

        data["discounted_total"] = total_discounted
        data['usage_history'] = usage_list
    return data


def update_promo(promo, request):
    promo.promo_code = request.data.get("promo_code")
    promo.discount = request.data.get("discount")
    promo.usage_limit = request.data.get("usage_limit")
    promo.is_enabled = request.data.get("is_enabled")
    promo.is_finished = request.data.get("is_finished")
    promo.active_from = parse_datetime(request.data.get('active_from'))
    promo.active_until = parse_datetime(request.data.get('active_until'))

    return promo
