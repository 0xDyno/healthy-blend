# utils.py

import json
from collections import defaultdict
from decimal import Decimal

from django.core.exceptions import ValidationError

from .models import Product, Ingredient, Order, ProductIngredient, OrderProduct, NutritionalValue


def big_validator(data: json):
    """ We return, save & use frontend price - if it's less than 0.1% different of official. Customer oriented
    :return: price
    """
    official_meals = data.get("official_meals", [])
    custom_meals = data.get("custom_meals", [])
    price = data.get("price")
    payment_type = data.get("payment_type")

    validate_nutritional_summary(data.get("nutritional_value"))

    if not official_meals and not custom_meals:
        raise ValidationError(message="The cart is empty")

    if not isinstance(price, (int, float)):
        raise ValidationError(message="Wrong price format")
    if payment_type not in ["cash", "card", "qr"]:
        raise ValidationError(message="Wrong payment type")

    price_for_official_meal = validate_official_meal(official_meals)
    price_for_custom_meal = validate_custom_meal(custom_meals)

    total_off_price = price_for_official_meal + price_for_custom_meal
    if not validate_price(total_off_price, price):
        raise ValidationError(message=f"Wrong calculated total Price. Web price: {price}, off price {total_off_price}")
    return price


def validate_official_meal(official_meals):
    total_price = 0
    for official_meal in official_meals:
        meal_id = official_meal.get("id")
        amount = official_meal.get("amount")
        calories = official_meal.get("calories")
        price = official_meal.get("price")

        if not isinstance(meal_id, int):
            raise ValidationError(message="Official Meal - wrong type for id.")
        if not isinstance(amount, int) or amount < 1 or amount > 10:
            raise ValidationError(message="Official Meal - max allowed 10 for one type.")
        if not isinstance(calories, int):
            raise ValidationError(message="Official Meal - wrong type for calories.")
        if not isinstance(price, (int, float)):
            raise ValidationError(message="Official Meal - wrong type for price.")

        product = Product.objects.filter(id=meal_id).first()
        if product is None:
            raise ValidationError(message="Official Meal - wrong product id.")
        if product.product_type == "dish" and calories not in [400, 600, 800]:
            raise ValidationError(message="Official Meal - wrong calories number.")

        official_price = product.get_price_for_calories(calories)
        if not validate_price(official_price, price):
            raise ValidationError(message="Official Meal - wrong calculated price on web-site.")

        total_price += official_price * amount
    return total_price


def validate_custom_meal(custom_meals):
    total_price = 0
    for custom_meal in custom_meals:
        product_price = 0

        ingredients = custom_meal.get("ingredients")
        amount = custom_meal.get("amount")
        price = custom_meal.get("price")

        if not isinstance(ingredients, list):
            raise ValidationError(message="Custom Meal - wrong type for ingredients.")
        if not isinstance(amount, int) or amount < 1 or amount > 10:
            raise ValidationError(message="Custom Meal - max allowed 10 for one type.")
        if not isinstance(price, (int, float)):
            raise ValidationError(message="Custom Meal - wrong type for price.")

        # Get all ingredients and save them to map as k:V -> id:object
        all_ingredients_map = {ingredient.id: ingredient for ingredient in Ingredient.objects.all()}

        for ingredient in ingredients:
            ingredient_id = ingredient.get("id")
            weight = ingredient.get("weight")

            if not isinstance(ingredient_id, int):
                raise ValidationError(message=f"Custom Meal - wrong type for ingredient id. Received ({type(ingredient_id)})")
            if not isinstance(weight, float):
                raise ValidationError(message=f"Custom Meal - wrong type for ingredient id. Received ({type(weight)})")

            if ingredient_id not in all_ingredients_map:
                raise ValidationError(message="Custom Meal - wrong ingredient id.")

            ingredient_object = all_ingredients_map.get(ingredient_id)
            if weight > ingredient_object.max_order or weight < ingredient_object.min_order:
                raise ValidationError(message=f"Custom Meal - wrong weight for ingredient, received {weight}, "
                                              f"allowed {ingredient_object.min_order} - {ingredient_object.max_order}.")

            product_price += ingredient_object.get_selling_price_for_weight(weight)
        if not validate_price(price, product_price):
            raise ValidationError(message="Custom Meal - wrong calculated price on web-site.")

        total_price += product_price
    return total_price


def validate_nutritional_summary(nutritional_summary):
    if not nutritional_summary:
        raise ValidationError(f"Missing nutritions")
    # Get all fields
    model_fields = [field.name for field in NutritionalValue._meta.get_fields() if not field.auto_created]

    # check we have all keys in nutritional_summary
    for key, value in nutritional_summary.items():
        if key not in model_fields:
            raise ValidationError(f"Wrong format. Field '{key}' doesn't exist in nutritions.")

        # Проверка, что значение является числом и больше 0
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError(f"Wrong format. Value for '{key}' should be a number")
        if value < 0:
            raise ValidationError(f"Wrong format. Value for '{key}' should be bigger than 0")

    # check we have all fields we need
    missing_fields = set(model_fields) - set(nutritional_summary.keys())
    if missing_fields:
        raise ValidationError(f"Wrong format, not all fields provided for nutritions. Missing for: {', '.join(missing_fields)}")


def process_official_meal(official_meals, order: Order):
    for official_meal in official_meals:
        meal_id = official_meal.get("id")
        price = round(official_meal.get("price"))
        official_product = Product.objects.filter(id=meal_id).first()

        amount = official_meal.get("amount")
        calories = official_meal.get("calories")
        coefficient = calories / official_product.nutritional_value.calories

        if not official_product.is_dish():
            # if it's drink - just connect with Order
            OrderProduct.objects.create(order=order, product=official_product, amount=amount, price=price)
        else:
            new_name = f"{official_product.name} {calories}"
            new_desc = f"Copy for {calories} kCal for meal \"{official_product.description}\""

            # Check if we have SAME product
            product = Product.objects.filter(name=new_name, description=new_desc, image=official_product.image, is_official=False,
                                             product_type=official_product.product_type).first()

            # If we don't have - let's create
            if not product:
                product = Product.objects.create(name=new_name, description=new_desc, image=official_product.image, is_official=False,
                                                 product_type=official_product.product_type)
                # Add ingredients & weight
                for original_ingredient in official_product.productingredient_set.all():
                    weight = round(original_ingredient.weight_grams * coefficient)
                    ProductIngredient.objects.create(product=product, ingredient=original_ingredient.ingredient, weight_grams=weight)
                product.save()

            # Connect with order
            OrderProduct.objects.create(order=order, product=product, amount=amount, price=price)


def process_custom_meal(custom_meals, order: Order):
    for custom_meal in custom_meals:
        name = "Custom Meal"
        description = f"{name} - {get_date_today()}"

        product = Product.objects.create(name=name, description=description, is_official=False, product_type="dish")
        amount = custom_meal.get("amount")

        # get IDs of ingredients in Custom Meal
        received_ingredients = custom_meal.get("ingredients")
        received_ingredient_ids = [ingredient_id.get("id") for ingredient_id in received_ingredients]

        # get Ingredients we need by ID from DB, then make it dict k:V - id:obj
        official_ingredients = Ingredient.objects.filter(id__in=received_ingredient_ids)
        official_ingredient_dict = {ingredient.id: ingredient for ingredient in official_ingredients}

        # creat ProductIngredient
        for ingredient in received_ingredients:
            official_ingredient = official_ingredient_dict.get(ingredient.get("id"))
            weight = ingredient.get("weight")
            ProductIngredient.objects.create(product=product, ingredient=official_ingredient, weight_grams=weight)

        product.save()
        OrderProduct.objects.create(order=order, product=product, amount=amount, price=round(custom_meal.get("price")))


def get_date_today():
    from datetime import date
    current_date = date.today()
    return current_date.strftime("%d-%m-%Y %H:%M:%S")


def validate_price(p1, p2, allowed_difference=0.1):
    """ it doesn't matter divide difference to p1 or p2
    :return: True if everything Okay. False if difference too big
    """
    difference = abs(float(p1) - float(p2))
    percentage_difference = (difference / float(p1)) * 100
    return percentage_difference < allowed_difference


def summarize_nutritions(nutritions: list):
    """ Not is use now, can be deleted later
    :param nutritions: list with NutritionalValue objects
    :return: dict with sum of all nutritions
    """
    total_nutrients = defaultdict(lambda: 0)

    # Проходим по каждому объекту в списке
    for nutrient in nutritions:
        nutrient_data = vars(nutrient)  # Получаем все атрибуты объекта в виде словаря
        for key, value in nutrient_data.items():
            if isinstance(value, (int, float, Decimal)):  # Проверяем, что значение числовое
                total_nutrients[key] += value

    return dict(total_nutrients)


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
        "available": ingredient.available,
        "price": ingredient.custom_price if ingredient.custom_price else ingredient.price_per_gram * ingredient.price_multiplier,
        "nutritional_value": ingredient.nutritional_value.to_dict() if ingredient.nutritional_value else None,
    }
    return data


def get_orders_full_info(orders):
    result = []

    for order in orders:
        data_to_send = {
            "id": order.id,
            "table_id": order.user.id,
            "order_status": order.order_status,
            "order_type": order.order_type,
            "payment_type": order.payment_type,
            "raw_price": order.raw_price,
            "fee": order.fee,
            "service": order.service,
            "total_price": order.total_price,
            "payment_id": order.payment_id,
            "is_refunded": order.is_refunded,
            "created_at": order.created_at,
            "paid_at": order.paid_at,
            "ready_at": order.ready_at,
            "refunded_at": order.refunded_at,
            "nutrition_value": order.nutritional_value.to_dict(),
            "products": [],
        }

        for order_product in order.products.all():
            product = order_product.product
            product_data = {
                "id": product.id,
                "name": product.name,
                "weight": product.weight,
                "price": order_product.price,
                "amount": order_product.amount,
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

        result.append(data_to_send)

    return result


def get_order_data(order):
    data_to_send = {
        "id": order.id,
        "order_status": order.order_status,
        "payment_type": order.payment_type,
        "total_price": order.total_price,
        "created_at": order.created_at,
        "paid_at": order.paid_at if order.paid_at else None,
        "products": [],
    }
    for product in order.products.all():
        product_data = {
            "product_name": product.product.name,
            "price": product.price,
            "amount": product.amount,
        }
        data_to_send["products"].append(product_data)
    return data_to_send


def get_orders_for_table(orders):
    result = []
    for order in orders:
        result.append(get_order_data(order))
    return result


def get_orders_for_kitchen(orders):
    result = []
    for order in orders:
        data_to_send = {
            "id": order.id,
            "table_id": order.user.id,
            "order_status": order.order_status,
            "paid_at": order.paid_at,
            "products": [],
        }

        for order_product in order.products.all():
            product = order_product.product
            product_data = {
                "product_name": product.name,
                "amount": order_product.amount,
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

        result.append(data_to_send)

    return result
