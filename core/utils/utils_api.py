from django.utils.dateparse import parse_date

from core.models import Ingredient, Order


def get_all_products(products: list):
    data = []
    for product in products:
        product_info = {"id": product.id,
                        "product_type": product.product_type,
                        "name": product.name,
                        "description": product.description,
                        "image": product.image.url if product.image else None,
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


def get_ingredient_data(ingredient: Ingredient):
    data = {
        "id": ingredient.id,
        "name": ingredient.name,
        "description": ingredient.description,
        "image": ingredient.image.url,
        "ingredient_type": ingredient.ingredient_type,
        "step": ingredient.step,
        "min_order": ingredient.min_order,
        "max_order": ingredient.max_order,
        "available": ingredient.is_available,
        "price": ingredient.custom_price if ingredient.custom_price else ingredient.price_per_gram * ingredient.price_multiplier,
        "nutritional_value": ingredient.nutritional_value.to_dict() if ingredient.nutritional_value else None,
    }
    return data


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
            "nutritional_value": product.nutritional_value.to_dict() if product.nutritional_value else None,
            "ingredients": [],
        }

        for product_ingredient in product.productingredient_set.all():
            ingredient = product_ingredient.ingredient
            ingredient_data = {
                "name": ingredient.name,
                "weight_grams": float(product_ingredient.weight_grams),
            }
            product_data["ingredients"].append(ingredient_data)

        data_to_send["products"].append(product_data)
    return data_to_send


def get_order_for_table(order: Order):
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
            "ingredients": [],
        }

        for product_ingredient in product.productingredient_set.all():
            ingredient = product_ingredient.ingredient
            ingredient_data = {
                "id": ingredient.id,
                "name": ingredient.name,
                "weight_grams": float(product_ingredient.weight_grams),
                "ingredient_type": ingredient.ingredient_type,
            }
            product_data["ingredients"].append(ingredient_data)

        data_to_send["products"].append(product_data)
    return data_to_send


def get_orders_for_kitchen(orders: list):
    return [get_order_for_kitchen(order) for order in orders]


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
