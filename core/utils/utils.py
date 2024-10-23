# utils.py

import json
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from rest_framework import status

from core.models import Product, Ingredient, Order, ProductIngredient, OrderProduct, NutritionalValue


def verify_if_manager(user):
    if user.role != "admin" and user.role != "manager":
        return JsonResponse({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)


def big_validator(data: json):
    """ We return, save & use frontend price - if it's less than 0.1% different of official. Customer oriented
    :return: price
    """
    official_meals = data.get("official_meals", [])
    custom_meals = data.get("custom_meals", [])
    raw_price_front = data.get("raw_price")
    total_price_front = data.get("total_price")
    payment_type = data.get("payment_type")

    validate_nutritional_summary(data.get("nutritional_value"))

    if not official_meals and not custom_meals:
        raise ValidationError(message="The cart is empty")

    if not isinstance(raw_price_front, (int, float)) and not isinstance(total_price_front, (int, float)):
        raise ValidationError(message="Wrong price format")
    if payment_type not in ["cash", "card", "qr"]:
        raise ValidationError(message="Wrong payment type")

    price_for_official_meal = validate_official_meal(official_meals)
    price_for_custom_meal = validate_custom_meal(custom_meals)

    raw_price_back = float(price_for_official_meal + price_for_custom_meal)
    total_price_back = get_price_with_tax(raw_price_back)

    if not validate_price(raw_price_back, raw_price_front) or not validate_price(total_price_back, total_price_front):
        raise ValidationError(message=f"Wrong calculated total Price. Web price: {total_price_front}, off price {total_price_back}")


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
            if not isinstance(weight, (int, float)):
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


def validate_price(p1, p2, allowed_difference=0.5):
    """ it doesn't matter divide difference to p1 or p2
    :return: True if everything Okay. False if difference too big
    """
    difference = abs(float(p1) - float(p2))
    percentage_difference = (difference / float(p1)) * 100
    return percentage_difference < allowed_difference


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
            new_desc = official_product.description

            # Check if we have SAME product
            product = Product.objects.filter(name=new_name, is_official=True, product_type=official_product.product_type).first()

            # If we don't have - let's create
            if not product:
                product = Product.objects.create(name=new_name, description=official_product.description, image=official_product.image,
                                                 is_menu=False, is_official=True, product_type=official_product.product_type)
                # Add ingredients & weight
                for original_ingredient in official_product.productingredient_set.all():
                    weight = round(original_ingredient.weight_grams * coefficient)
                    ProductIngredient.objects.create(product=product, ingredient=original_ingredient.ingredient, weight_grams=weight)

            # Connect with order
            OrderProduct.objects.create(order=order, product=product, amount=amount, price=price)


def process_custom_meal(custom_meals, order: Order):
    for custom_meal in custom_meals:
        name = "Custom Meal"
        description = f"{name} - {get_date_today()}"
        price = round(custom_meal.get("price"))

        product = Product.objects.create(name=name, description=description, is_official=False, product_type="dish", price=price)
        amount = custom_meal.get("amount")

        # get IDs of ingredients in Custom Meal
        received_ingredients = custom_meal.get("ingredients")
        received_ingredient_ids = [ingredient_id.get("id") for ingredient_id in received_ingredients]

        # get Ingredients we need by ID from DB, then make it dict k:V - id:obj
        official_ingredients = Ingredient.objects.filter(id__in=received_ingredient_ids)
        official_ingredient_dict = {ingredient.id: ingredient for ingredient in official_ingredients}

        # creat ProductIngredient
        total_weight = 0
        for ingredient in received_ingredients:
            official_ingredient = official_ingredient_dict.get(ingredient.get("id"))
            weight = ingredient.get("weight")
            total_weight += weight
            ProductIngredient.objects.create(product=product, ingredient=official_ingredient, weight_grams=weight)

        product.weight = total_weight
        product.save()
        OrderProduct.objects.create(order=order, product=product, amount=amount, price=price)


def get_date_today():
    from datetime import datetime
    current_date = datetime.today()
    return current_date.strftime("%d-%m-%Y %H:%M:%S")


def get_price_with_tax(price):
    price_tax = price + (price * 0.07)
    return round(price_tax + (price_tax * 0.01))
