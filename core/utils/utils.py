# utils.py

import json
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps

from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone

from core.models import Product, Ingredient, Order, ProductIngredient, OrderProduct, NutritionalValue, DaySettings, Settings


def role_redirect(roles, redirect_url, do_redirect=True):
    """
    If do_redirect is True - redirect will be for ALL included roles.
    If do_redirect is False - redirect will be for ALL excluded roles.
    :param roles: list
    :param redirect_url: String, path name from urls.py
    :param do_redirect: bool
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_role = getattr(request.user, 'role', None)
            if (user_role in roles and do_redirect) or (user_role not in roles and not do_redirect):
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def big_validator(data: json):
    """ We return, save & use frontend price - if it's less than 0.1% different of official. Customer oriented
    :return: price
    """
    official_meals = data.get("official_meals", [])
    custom_meals = data.get("custom_meals", [])
    raw_price_front = data.get("raw_price")
    total_price_front = data.get("total_price")
    payment_type = data.get("payment_type")

    if not Settings.objects.get(pk=1).can_order:
        raise ValidationError(message="Currently, ordering is not available. We apologize for the inconvenience.")

    validate_working_time()
    validate_nutritional_summary(data.get("nutritional_value"))

    if not official_meals and not custom_meals:
        raise ValidationError(message="The cart is empty")

    if not isinstance(raw_price_front, (int, float)) and not isinstance(total_price_front, (int, float)):
        raise ValidationError(message="Wrong price format")
    if payment_type not in ["cash", "card", "qr"]:
        raise ValidationError(message="Wrong payment type")

    validation_result_official = validate_official_meal(official_meals)
    validation_result_custom = validate_custom_meal(custom_meals)

    ingredients_official = validation_result_official.get("ingredients")
    ingredients_custom = validation_result_custom.get("ingredients")
    all_ingredients = ingredients_official.union(ingredients_custom)
    validate_ingredient_availability(all_ingredients)

    price_for_official_meal = validation_result_official.get("total_price")
    price_for_custom_meal = validation_result_custom.get("total_price")

    raw_price_back = float(price_for_official_meal + price_for_custom_meal)
    total_price_back = get_price_with_tax(raw_price_back)

    if not validate_price(raw_price_back, raw_price_front) or not validate_price(total_price_back, total_price_front):
        raise ValidationError(message=f"Wrong calculated total Price. Web price: {total_price_front}, off price {total_price_back}")


def validate_working_time():
    current_time = timezone.localtime()
    current_day = current_time.weekday()
    print(current_time)
    print(current_day)

    day_settings = DaySettings.objects.get(day=current_day)

    if not day_settings.is_open:
        raise ValidationError("Orders are unavailable on non-working days.")

    open_time = timezone.make_aware(datetime.combine(current_time.date(), day_settings.open_hours))
    close_time = timezone.make_aware(datetime.combine(current_time.date(), day_settings.close_hours))
    print(open_time)
    print(close_time)

    if current_time < open_time or current_time > close_time:
        raise ValidationError(f"Orders are only available during working hours: from {day_settings.open_hours} to {day_settings.close_hours}.")

    if current_time >= close_time - timedelta(minutes=20):
        raise ValidationError("Orders close 20 minutes before the end of working hours.")

    return True


def validate_official_meal(official_meals):
    total_price = 0
    ingredients_set = set()
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
        # if 100 > calories > 1000:
        #     raise ValidationError(
        #         message=f"Official Meal - minimal is 100 kCal, maximum 1000 kCal, your choice: {calories}. Please change it.")
        if not isinstance(price, (int, float)):
            raise ValidationError(message="Official Meal - wrong type for price.")

        product = Product.objects.filter(id=meal_id).first()
        if product is None:
            raise ValidationError(message="Official Meal - wrong product id.")

        official_price = product.get_price_for_calories(calories)
        if not validate_price(official_price, price):
            raise ValidationError(message="Official Meal - wrong calculated price on web-site.")

        ingredients_set.update(product.ingredients.all())
        total_price += official_price * amount
    return {"total_price": total_price, "ingredients": ingredients_set}


def validate_custom_meal(custom_meals):
    total_price = 0
    ingredients_set = set()
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

            ingredient_obj = all_ingredients_map.get(ingredient_id)
            if weight > ingredient_obj.max_order or weight < ingredient_obj.min_order:
                raise ValidationError(message=f"Custom Meal - wrong weight for ingredient, received {weight}, "
                                              f"allowed {ingredient_obj.min_order} - {ingredient_obj.max_order}.")

            product_price += ingredient_obj.get_selling_price_for_weight(weight)

            ingredients_set.add(ingredient_obj)
        if not validate_price(price, product_price):
            raise ValidationError(message="Custom Meal - wrong calculated price on web-site.")

        total_price += product_price
    return {"total_price": total_price, "ingredients": ingredients_set}


def validate_ingredient_availability(ingredients: set):
    not_available = [ingredient.name for ingredient in ingredients if not ingredient.is_available]

    if not_available:
        unavailable_ingredients = ", ".join(not_available)  # Преобразуем в строку для сообщения об ошибке
        raise ValidationError(f"We're sorry to tell you that following ingredients are not available: {unavailable_ingredients}.")


def validate_price(p1, p2, allowed_difference=0.5):
    """it doesn't matter divide difference to p1 or p2
    :param allowed_difference: in %, default 0.5%
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

    # Check if all required fields are present
    missing_fields = set(model_fields) - set(nutritional_summary.keys())
    if missing_fields:
        raise ValidationError(f"Missing required nutritional values: {', '.join(missing_fields)}")

    # Validate each provided value
    for key, value in nutritional_summary.items():
        # Check if field exists in model
        if key not in model_fields:
            raise ValidationError(f"Invalid field '{key}' in nutritional values")

        # Check if value is a number
        if not isinstance(value, (int, float, Decimal)):
            raise ValidationError(f"Value for '{key}' must be a number")

        # Check if value is non-negative
        if value < 0:
            raise ValidationError(f"Value for '{key}' must be non-negative")

        # Check if value is within allowed range
        if value > 100000:
            raise ValidationError(f"Value for '{key}' exceeds maximum limit of 100,000 (current value: {value})")


@transaction.atomic
def process_official_meal(official_meals, order: Order):
    for meal in official_meals:
        meal_id = meal.get("id")
        price = round(meal.get("price"))
        official_product = Product.objects.filter(id=meal_id).first()

        amount = meal.get("amount")
        calories = meal.get("calories")
        coefficient = calories / official_product.nutritional_value.calories

        if not official_product.is_dish():
            # if it's drink - just connect with Order
            OrderProduct.objects.create(order=order, product=official_product, amount=amount, price=price)
        else:
            new_name = f"{official_product.name} {calories}"

            # Check if we have SAME product
            product = Product.objects.filter(name=new_name, is_official=True, product_type=official_product.product_type).first()

            # If we don't have - let's create
            if not product:
                weight_product = round(meal.get("weight"))
                product = Product.objects.create(name=new_name, description=official_product.description, image=official_product.image,
                                                 is_menu=False, is_official=True, product_type=official_product.product_type,
                                                 weight=weight_product)
                # Add ingredients & weight
                for original_ingredient in official_product.productingredient_set.all():
                    weight_grams = original_ingredient.weight_grams * coefficient
                    ProductIngredient.objects.create(product=product, ingredient=original_ingredient.ingredient, weight_grams=weight_grams)

            # Connect with order
            OrderProduct.objects.create(order=order, product=product, amount=amount, price=price)


@transaction.atomic
def process_custom_meal(custom_meals, order: Order):
    for meal in custom_meals:
        name = "Custom Meal"
        description = f"{name} - {get_date_today()}"
        price = round(meal.get("price"))

        product = Product.objects.create(name=name, description=description, is_official=False, product_type="dish", price=price)
        amount = meal.get("amount")

        # get IDs of ingredients in Custom Meal
        received_ingredients = meal.get("ingredients")
        received_ingredient_ids = [ingredient_id.get("id") for ingredient_id in received_ingredients]

        # get Ingredients we need by ID from DB, then make it dict k:V - id:obj
        official_ingredients = Ingredient.objects.filter(id__in=received_ingredient_ids)
        official_ingredient_dict = {ingredient.id: ingredient for ingredient in official_ingredients}

        # creat ProductIngredient
        total_weight = 0
        for ingredient in received_ingredients:
            official_ingredient = official_ingredient_dict.get(ingredient.get("id"))
            weight_grams = ingredient.get("weight")
            total_weight += weight_grams
            ProductIngredient.objects.create(product=product, ingredient=official_ingredient, weight_grams=weight_grams)

        product.weight = round(total_weight)
        product.save()
        OrderProduct.objects.create(order=order, product=product, amount=amount, price=price)


def get_date_today():
    current_date = datetime.today()
    return current_date.strftime("%d-%m-%Y %H:%M:%S")


def get_price_with_tax(price):
    settings = Settings.objects.get(pk=1)
    price_service = price + (price * settings.service)
    return round(price_service + (price_service * settings.tax))


def get_ingredient_type_choices():
    return [ingredient[0] for ingredient in Ingredient.INGREDIENT_TYPES]
