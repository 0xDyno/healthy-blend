# utils.py

import json
from datetime import datetime, timedelta
from functools import wraps

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django_ratelimit.exceptions import Ratelimited

from core.models import Product, Ingredient, Order, ProductIngredient, OrderProduct, NutritionalValue, DaySetting, Setting, Promo, \
    PromoUsage

NUTRITIONAL_VALUE_FIELDS = None


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


def handle_errors(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Ratelimited:
            return JsonResponse({"messages": [
                {"level": "error", "message": "Too many requests. Please try again in a minute."}]}, status=429)
        except ValidationError as e:
            return JsonResponse({"messages": [{"level": "warning", "message": e.messages}]}, status=400)
        except Exception as e:
            print(e)  # logging in the future
            return JsonResponse({"messages": [{"level": "warning", "message": f"Error occurred. Please try again."}]}, status=500)
    return wrapped_view


def order_validator(data: json, settings: dict):
    """ We return, save & use frontend price - if it's less than 0.1% different of official. Customer oriented
    :return: price
    """
    # Check ordering is On and it's working time
    if not settings.get("can_order"):
        raise ValidationError(message="Currently, ordering is not available. We apologize for the inconveniences.")
    validate_working_time(settings.get("close_kitchen_before"))

    # Get basic info
    official_meals = data.get("official_meals", [])
    custom_meals = data.get("custom_meals", [])
    front_price_base = data.get("base_price")
    front_price_final = data.get("final_price")
    payment_type = data.get("payment_type")
    order_type = data.get("order_type")
    promo_code = data.get("promo_code")

    # Check cart is not empty
    if not official_meals and not custom_meals:
        raise ValidationError(message="The cart is empty")

    # Check data format
    if not isinstance(front_price_base, (int, float)) and not isinstance(front_price_final, (int, float)):
        raise ValidationError(message="Wrong price format")
    if payment_type not in ["cash", "card", "qr"]:
        raise ValidationError(message="Wrong payment type")
    # if order_type not in ["offline", "takeaway", "delivery"]:
    #     raise ValidationError(message="Wrong order type")
    if not isinstance(promo_code, str):
        promo_code = str(promo_code)

    front_price_base = front_price_base
    front_price_final = front_price_final

    # Check the price is Okay before checks that require DataBase
    max_order = settings.get("maximum_order_amount")
    min_order = settings.get("minimum_order_amount")
    if front_price_base < 0 or front_price_final < 0:
        raise ValidationError("The price cannot be negative. Please review your order details.")
    if front_price_final > max_order:
        raise ValidationError(f"Total price ({front_price_final}) exceeds the maximum allowed of {max_order}.")
    if not promo_code and front_price_final < min_order:
        raise ValidationError(f"Total price ({front_price_final}) is less than the minimum allowed of {min_order}.")

    # Check promo code
    if promo_code:
        promo = check_promo(promo_code)
        if not promo:
            raise ValidationError(message="It appears the promo code entered is not valid.")
        discount = front_price_base * promo.discount
        discount = discount if discount < promo.max_discount else promo.max_discount
    else:
        promo = None

    # Check nutrition values
    validate_nutritional_summary(data.get("nutritional_value"))

    # Check ordered positions
    validation_result_official = validate_official_meal(official_meals, settings.get("minimum_blend_weight"))
    validation_result_custom = validate_custom_meal(custom_meals, settings.get("minimum_blend_weight"))

    # Check weight
    total_weight = validation_result_official.get("weight") + validation_result_custom.get("weight")
    if total_weight > settings.get("maximum_order_weight"):
        raise ValidationError(message=f"The order weight ({round(total_weight)}) exceeds the maximum allowed of "
                                      f"{settings.get('maximum_order_weight')}. Please remove items to meet the limit.")

    # Check all ingredients available
    all_ingredients = validation_result_official.get("ingredients").union(validation_result_custom.get("ingredients"))
    validate_ingredient_availability(all_ingredients)

    # Get and check base & finale price calculated on backend
    back_price_base = validation_result_official.get("total_price") + validation_result_custom.get("total_price")

    discounted_price = back_price_base - discount if promo else back_price_base
    back_price_final = get_price_with_tax(price=discounted_price, service=settings.get("service"), tax=settings.get("tax"))

    print(f"Front Price Base: {front_price_base}, Front Price Final: {front_price_final}")
    print(f"Back Price Base: {back_price_base}, Back Price Final: {back_price_final}")
    if not validate_price_difference(back_price_base, front_price_base) or not validate_price_difference(back_price_final, front_price_final):
        raise ValidationError(message=f"Wrong calculated Price. Please review your order details.")

    # Check promo
    if promo:
        return PromoUsage.objects.create(promo=promo, discounted=round(discount), user=None, order=None)
    return None


def validate_working_time(close_kitchen_before: int = 30):
    current_time = timezone.now()
    current_day = current_time.weekday()

    day_setting = DaySetting.objects.get(day=current_day)

    if not day_setting.is_open:
        raise ValidationError("Orders are unavailable on non-working days.")

    open_time = timezone.make_aware(datetime.combine(current_time.date(), day_setting.open_hours))
    close_time = timezone.make_aware(datetime.combine(current_time.date(), day_setting.close_hours))

    if current_time < open_time or current_time > close_time:
        raise ValidationError(f"Orders are only available during working hours: from {day_setting.open_hours} to {day_setting.close_hours}.")

    if current_time >= close_time - timedelta(minutes=close_kitchen_before):
        raise ValidationError("Orders close 20 minutes before the end of working hours.")

    return True


def validate_official_meal(official_meals, min_blend=0):
    if not official_meals:
        return {"total_price": 0, "ingredients": set(), "weight": 0}

    meal_ids = {meal["id"] for meal in official_meals}
    products = {product.id: product for product in Product.objects.filter(id__in=meal_ids).prefetch_related('ingredients')}

    total_price = 0
    total_weight = 0
    ingredients_set = set()

    for meal in official_meals:
        meal_id = meal.get("id")
        amount = meal.get("amount")
        calories = meal.get("calories")
        price = meal.get("price")
        do_blend = meal.get("do_blend")

        if not isinstance(meal_id, int):
            raise ValidationError(message="Official Meal - wrong type for id.")
        if not isinstance(amount, int) or amount < 1 or amount > 10:
            raise ValidationError(message="Official Meal - max allowed 10 for one type.")
        if not isinstance(calories, int):
            raise ValidationError(message="Official Meal - wrong type for calories.")
        if not isinstance(price, (int, float)):
            raise ValidationError(message="Official Meal - wrong type for price.")
        if not isinstance(do_blend, bool):
            raise ValidationError(message="Official Meal - wrong type for do_blend.")

        product = products.get(meal_id)

        if product is None:
            raise ValidationError(message="Official Meal - wrong product id.")

        if not product.is_available:
            raise ValidationError(message="Official Meal - product is not available.")

        official_price = product.get_price_for_calories(calories)
        if not validate_price_difference(official_price, price):
            raise ValidationError(message="Official Meal - wrong calculated price on web-site.")

        weight = product.weight * (calories / product.nutritional_value.calories)

        if do_blend and weight < min_blend:
            raise ValidationError(message=f"Official Meal - weight is less than minimum allowed for blend, min is {min_blend}g.")

        ingredients_set.update(product.ingredients.all())
        total_price += official_price * amount
        total_weight += weight * amount

    return {"total_price": total_price, "ingredients": ingredients_set, "weight": total_weight}


def validate_custom_meal(custom_meals, min_blend=0):
    if not custom_meals:
        return {"total_price": 0, "ingredients": set(), "weight": 0}

    ingredient_ids = set()
    for meal in custom_meals:
        ingredient_ids.update(ing["id"] for ing in meal.get("ingredients", []))

    all_ingredients_map = {ingredient.id: ingredient for ingredient in Ingredient.objects.filter(id__in=ingredient_ids)}

    total_price = 0
    total_weight = 0
    ingredients_set = set()

    for meal in custom_meals:
        product_price = 0
        meal_weight = 0
        ingredients = meal.get("ingredients", [])
        amount = meal.get("amount")
        price = meal.get("price")
        do_blend = meal.get("do_blend")

        if not isinstance(ingredients, list):
            raise ValidationError(message="Custom Meal - wrong type for ingredients.")
        if not isinstance(amount, int) or amount < 1 or amount > 10:
            raise ValidationError(message="Custom Meal - max allowed 10 for one type.")
        if not isinstance(price, (int, float)):
            raise ValidationError(message="Custom Meal - wrong type for price.")

        for ingredient in ingredients:
            ingredient_id = ingredient.get("id")
            weight = ingredient.get("weight")

            if not isinstance(ingredient_id, int):
                raise ValidationError(message=f"Custom Meal - wrong type for ingredient id. Received ({type(ingredient_id)})")
            if not isinstance(weight, (int, float)):
                raise ValidationError(message=f"Custom Meal - wrong type for ingredient id. Received ({type(weight)})")

            ingredient_obj = all_ingredients_map.get(ingredient_id)
            if not ingredient_obj:
                raise ValidationError(message="Custom Meal - wrong ingredient id.")

            if weight > ingredient_obj.max_order or weight < ingredient_obj.min_order:
                raise ValidationError(message=f"Custom Meal - wrong weight for ingredient, received {weight}, "
                                              f"allowed {ingredient_obj.min_order} - {ingredient_obj.max_order}.")

            product_price += ingredient_obj.get_selling_price_for_weight(weight)
            meal_weight += weight
            ingredients_set.add(ingredient_obj)

        if do_blend and meal_weight < min_blend:
            raise ValidationError(message=f"Custom Meal - weight is less than minimum allowed for blend, min is {min_blend}g.")

        if not validate_price_difference(price, product_price):
            raise ValidationError(message="Custom Meal - wrong calculated price on web-site.")

        total_price += product_price * amount
        total_weight += meal_weight * amount

    return {"total_price": total_price, "ingredients": ingredients_set, "weight": total_weight}


def validate_ingredient_availability(ingredients: set):
    unavailable = Ingredient.objects.filter(id__in=[ing.id for ing in ingredients], is_available=False).values_list('name', flat=True)
    if unavailable:
        raise ValidationError(f"We're sorry to tell you that following ingredients are not available: {', '.join(unavailable)}.")
    not_menu = Ingredient.objects.filter(id__in=[ing.id for ing in ingredients], is_menu=False).values_list('name', flat=True)
    if not_menu:
        raise ValidationError(f"Following ingredients are not allowed to be ordered: {', '.join(not_menu)}.")


def validate_price_difference(p1, p2, allowed_difference=0.1):
    """it doesn't matter divide difference to p1 or p2
    :param allowed_difference: in %, default 0.1%
    :return: True if everything Okay. False if difference too big
    """
    difference = abs(p1 - p2)
    percentage_difference = (difference / p1) * 100
    return percentage_difference < allowed_difference


def validate_nutritional_summary(nutritional_summary):
    if not nutritional_summary:
        raise ValidationError(f"Missing nutritions")
    # Get all fields
    model_fields = get_nutritional_value_fields()

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
        if not isinstance(value, (int, float)):
            raise ValidationError(f"Value for '{key}' must be a number")

        # Check if value is non-negative
        if value < 0:
            raise ValidationError(f"Value for '{key}' must be non-negative")

        # Check if value is within allowed range
        if value > 100000:
            raise ValidationError(f"Value for '{key}' exceeds maximum limit of 100,000 (current value: {value})")


def get_nutritional_value_fields():
    global NUTRITIONAL_VALUE_FIELDS
    if NUTRITIONAL_VALUE_FIELDS is None:
        NUTRITIONAL_VALUE_FIELDS = set(
            field.name for field in NutritionalValue._meta.get_fields()
            if not field.auto_created
        )
    return NUTRITIONAL_VALUE_FIELDS


@transaction.atomic
def process_official_meal(official_meals, order: Order):
    # Get all official products we need
    meal_ids = [meal.get("id") for meal in official_meals]
    official_products = {prod.id: prod for prod in Product.objects.filter(id__in=meal_ids).select_related('nutritional_value')}

    # list with correct names for official_products with N kcal
    potential_names = [f"{official_products[meal.get('id')].name} {meal.get('calories')} kCal"for meal in official_meals
                       if official_products[meal.get('id')].is_dish()]

    # get all products with such names
    existing_products = {prod.name: prod for prod in Product.objects.filter(name__in=potential_names, is_official=True)}

    for meal in official_meals:
        meal_id = meal.get("id")
        price = round(meal.get("price"))
        official_product = official_products[meal_id]
        amount = meal.get("amount")
        calories = meal.get("calories")
        do_blend = meal.get("do_blend")

        if not official_product.is_dish():
            # If drink - just save
            OrderProduct.objects.create(order=order, product=official_product, amount=amount, price=price, do_blend=True)
        else:
            name = f"{official_product.name} {calories} kCal"
            product = existing_products.get(name)

            if not product:
                weight_product = round(meal.get("weight"))
                coefficient = calories / official_product.nutritional_value.calories

                product = Product.objects.create(name=name, description=official_product.description, image=official_product.image,
                                                 is_menu=False, is_official=True, product_type=official_product.product_type,
                                                 weight=weight_product)

                # Collect required ingredients
                for original_ingredient in official_product.productingredient_set.all():
                    weight = round(original_ingredient.weight_grams * coefficient, 1)
                    ProductIngredient.objects.create(product=product, ingredient=original_ingredient.ingredient, weight_grams=weight)
                product.save()

            # Add OrderProduct to the list
            OrderProduct.objects.create(order=order, product=product, amount=amount, price=price, do_blend=do_blend)


@transaction.atomic
def process_custom_meal(custom_meals, order: Order):
    # get IDs of ingredients in Custom Meal and get all Ingredients
    all_ingredient_ids = {ingredient["id"]
                          for meal in custom_meals
                          for ingredient in meal.get("ingredients", [])}
    ingredients_dict = {ing.id: ing for ing in Ingredient.objects.filter(id__in=all_ingredient_ids)}

    for meal in custom_meals:
        name = "Custom Meal"
        description = f"{name} - {get_date_today()}"
        price = round(meal.get("price"))
        amount = meal.get("amount")
        do_blend = meal.get("do_blend")

        product = Product.objects.create(name=name, description=description, is_official=False, product_type="dish", selling_price=price)

        total_weight = 0
        for ingredient in meal.get("ingredients", []):
            official_ingredient = ingredients_dict.get(ingredient.get("id"))
            weight_grams = round(ingredient.get("weight"), 1)
            total_weight += weight_grams

            ProductIngredient.objects.create(product=product, ingredient=official_ingredient, weight_grams=weight_grams)

        product.weight = round(total_weight)
        product.save()      # important to update price & nutrition values
        OrderProduct.objects.create(order=order, product=product, amount=amount, price=price, do_blend=do_blend)


def get_date_today():
    current_date = datetime.today()
    return current_date.strftime("%d-%m-%Y %H:%M:%S")


def get_price_with_tax(price, service, tax):
    """
    Tax should be in whole numbers, 10% = 10
    """
    price_service = price * (service / 100)
    price_tax = (price + price_service) * (tax / 100)
    return price + price_service + price_tax


def get_ingredient_type_choices():
    return [ingredient[0] for ingredient in Ingredient.INGREDIENT_TYPES]


def check_promo(promo_code):
    """
    Check if promo code exists and available for use.
    Returns Promo object if available, None otherwise.
    """
    if not promo_code and len(promo_code) > 20:
        return None

    now = timezone.now()
    try:
        return Promo.objects.get(promo_code=promo_code, active_from__lte=now, active_until__gte=now,
                                 used_count__lt=F('usage_limit'), is_enabled=True)
    except Promo.DoesNotExist:
        return None
