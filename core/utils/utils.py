# utils.py

import json
from datetime import datetime, timedelta
from functools import wraps

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone

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


def handle_rate_limit(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if getattr(request, 'limited', False):

            user_key = f"ratelimit-{request.user.id}"
            ttl = cache.ttl(user_key)

            return JsonResponse({"messages": [
                {"level": "error", "message": f"Rate limit exceeded. Please try again in {ttl // 60} minutes."}]}, status=429)
        return view_func(request, *args, **kwargs)

    return wrapped


def big_validator(data: json):
    """ We return, save & use frontend price - if it's less than 0.5% different of official. Customer oriented
    :return: price
    """
    # Get basic info
    official_meals = data.get("official_meals", [])
    custom_meals = data.get("custom_meals", [])
    raw_price_front = data.get("raw_price")
    total_price_front = data.get("total_price")
    payment_type = data.get("payment_type")
    promo_code = data.get("promo_code")

    # Check cart is not empty
    if not official_meals and not custom_meals:
        raise ValidationError(message="The cart is empty")

    settings = Setting.objects.values("service", "tax", "can_order",
                                      "minimum_order_amount", "maximum_order_amount", "maximum_order_weight").first()

    # Check ordering is On
    if not settings.get("can_order"):
        raise ValidationError(message="Currently, ordering is not available. We apologize for the inconvenience.")

    service = settings.get("service")
    tax = settings.get("tax")
    max_order = settings.get("maximum_order_amount")
    min_order = settings.get("minimum_order_amount")
    max_order_weight = settings.get("maximum_order_weight")

    # Check it's working time
    validate_working_time()

    # Check max price (min price later)
    if not max_order > total_price_front:
        raise ValidationError(message=f"The order amount exceeds the maximum allowed of {max_order}. Please remove items to meet the limit.")

    # Check promo
    if promo_code:
        promo = check_promo(promo_code)
        if not promo:
            raise ValidationError(message="It appears the promo code entered is not valid.")
    else:
        promo = False

    # Check nutrition values
    validate_nutritional_summary(data.get("nutritional_value"))

    # Check price format and payment types
    if not isinstance(raw_price_front, (int, float)) and not isinstance(total_price_front, (int, float)):
        raise ValidationError(message="Wrong price format")
    if payment_type not in ["cash", "card", "qr"]:
        raise ValidationError(message="Wrong payment type")

    # Check the price is Okay before checks that require DataBase
    if raw_price_front < 0 or total_price_front < 0:
        raise ValidationError("The calculated price cannot be negative. Please review your order details.")

    # Check ordered positions
    validation_result_official = validate_official_meal(official_meals)
    validation_result_custom = validate_custom_meal(custom_meals)

    # Check weight
    total_weight = validation_result_official.get("weight") + validation_result_custom.get("weight")
    if total_weight > max_order_weight:
        raise ValidationError(message=f"The order weight ({round(total_weight)}) exceeds the maximum allowed of {max_order_weight}. "
                                      f"Please remove items to meet the limit.")

    # Check all ingredients available
    all_ingredients = validation_result_official.get("ingredients").union(validation_result_custom.get("ingredients"))
    validate_ingredient_availability(all_ingredients)

    # Get price calculated on backend and check it
    raw_price_back = validation_result_official.get("total_price") + validation_result_custom.get("total_price")
    return validate_price(service=service, tax=tax, min_order=min_order, promo=promo,
                          back_price=raw_price_back, front_price=raw_price_front, total_front_price=total_price_front)


def validate_working_time():
    current_time = timezone.now()
    current_day = current_time.weekday()

    day_setting = DaySetting.objects.get(day=current_day)

    if not day_setting.is_open:
        raise ValidationError("Orders are unavailable on non-working days.")

    open_time = timezone.make_aware(datetime.combine(current_time.date(), day_setting.open_hours))
    close_time = timezone.make_aware(datetime.combine(current_time.date(), day_setting.close_hours))

    if current_time < open_time or current_time > close_time:
        raise ValidationError(f"Orders are only available during working hours: from {day_setting.open_hours} to {day_setting.close_hours}.")

    if current_time >= close_time - timedelta(minutes=20):
        raise ValidationError("Orders close 20 minutes before the end of working hours.")

    return True


def validate_official_meal(official_meals):
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

        if not isinstance(meal_id, int):
            raise ValidationError(message="Official Meal - wrong type for id.")
        if not isinstance(amount, int) or amount < 1 or amount > 10:
            raise ValidationError(message="Official Meal - max allowed 10 for one type.")
        if not isinstance(calories, int):
            raise ValidationError(message="Official Meal - wrong type for calories.")
        if not isinstance(price, (int, float)):
            raise ValidationError(message="Official Meal - wrong type for price.")

        product = products.get(meal_id)

        if product is None:
            raise ValidationError(message="Official Meal - wrong product id.")

        official_price = product.get_price_for_calories(calories)
        if not validate_price_difference(official_price, price):
            raise ValidationError(message="Official Meal - wrong calculated price on web-site.")

        weight = product.weight * (calories / product.nutritional_value.calories)

        ingredients_set.update(product.ingredients.all())
        total_price += official_price * amount
        total_weight += weight * amount

    return {"total_price": total_price, "ingredients": ingredients_set, "weight": total_weight}


def validate_custom_meal(custom_meals):
    if not custom_meals:
        return {"total_price": 0, "ingredients": set(), "weight": 0}

    ingredient_ids = set()
    for meal in custom_meals:
        ingredient_ids.update(ing["id"] for ing in meal.get("ingredients", []))

    all_ingredients_map = {ingredient.id: ingredient for ingredient in Ingredient.objects.filter(id__in=ingredient_ids)}

    total_price = 0
    total_weight = 0
    ingredients_set = set()

    for custom_meal in custom_meals:
        product_price = 0
        meal_weight = 0
        ingredients = custom_meal.get("ingredients", [])
        amount = custom_meal.get("amount")
        price = custom_meal.get("price")

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

        if not validate_price_difference(price, product_price):
            raise ValidationError(message="Custom Meal - wrong calculated price on web-site.")

        total_price += product_price * amount
        total_weight += meal_weight * amount

    return {"total_price": total_price, "ingredients": ingredients_set, "weight": total_weight}


def validate_ingredient_availability(ingredients: set):
    unavailable = Ingredient.objects.filter(id__in=[ing.id for ing in ingredients], is_available=False).values_list('name', flat=True)

    if unavailable:
        raise ValidationError(f"We're sorry to tell you that following ingredients are not available: {', '.join(unavailable)}.")


def validate_price(service, tax, min_order, promo, back_price, front_price, total_front_price):
    if promo:
        discount = back_price * promo.discount
        back_price = back_price - discount

    # Get price with tax & service
    total_back_price = get_price_with_tax(service, tax, back_price)

    if not validate_price_difference(back_price, front_price) or not validate_price_difference(total_back_price, total_front_price):
        raise ValidationError(message=f"Wrong calculated total Price. Web price: {total_front_price}, off price {total_back_price}")

    # Check price is > than minimum
    if front_price < min_order and not promo:
        raise ValidationError(message=f"The order amount is below the minimum required. "
                                      f"Please add more items to reach the minimum order amount of {min_order}.")

    if promo:
        return PromoUsage(promo=promo, discounted=discount)
    return None


def validate_price_difference(p1, p2, allowed_difference=0.5):
    """it doesn't matter divide difference to p1 or p2
    :param allowed_difference: in %, default 0.5%
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
    order_products_to_create = []
    products_to_create = []
    product_ingredients_to_create = []

    # Get all official_products with needed ID
    meal_ids = [meal.get("id") for meal in official_meals]
    official_products = {prod.id: prod for prod in Product.objects.filter(id__in=meal_ids).select_related('nutritional_value')}

    # list with correct names for official_products with N kcal
    potential_names = [f"{official_products[meal.get('id')].name} {meal.get('calories')}"for meal in official_meals
                       if official_products[meal.get('id')].is_dish()]

    # get all products with such names
    existing_products = {prod.name: prod for prod in Product.objects.filter(name__in=potential_names, is_official=True)}

    for meal in official_meals:
        meal_id = meal.get("id")
        price = round(meal.get("price"))
        official_product = official_products[meal_id]
        amount = meal.get("amount")
        calories = meal.get("calories")

        if not official_product.is_dish():
            # If drink - just save
            order_products_to_create.append(OrderProduct(order=order, product=official_product, amount=amount, price=price))
        else:
            new_name = f"{official_product.name} {calories}"
            product = existing_products.get(new_name)

            if not product:
                # Create new product
                weight_product = round(meal.get("weight"))
                coefficient = calories / official_product.nutritional_value.calories

                product = Product(name=new_name, description=official_product.description, image=official_product.image, is_menu=False,
                                  is_official=True, product_type=official_product.product_type, weight=weight_product)
                products_to_create.append(product)

                # Collect required ingredients
                for original_ingredient in official_product.productingredient_set.all():
                    weight = original_ingredient.weight_grams * coefficient
                    product_ingredient = ProductIngredient(product=product, ingredient=original_ingredient.ingredient, weight_grams=weight)
                    product_ingredients_to_create.append(product_ingredient)

            # Add OrderProduct to the list
            order_products_to_create.append(OrderProduct(order=order, product=product, amount=amount, price=price))

    # Bulk creation
    if products_to_create:
        Product.objects.bulk_create(products_to_create)
    if product_ingredients_to_create:
        ProductIngredient.objects.bulk_create(product_ingredients_to_create)
    if order_products_to_create:
        OrderProduct.objects.bulk_create(order_products_to_create)


@transaction.atomic
def process_custom_meal(custom_meals, order: Order):
    products_to_create = []
    product_ingredients_to_create = []
    order_products_to_create = []

    # get IDs of ingredients in Custom Meal and get all Ingredients
    all_ingredient_ids = {ingredient["id"] for meal in custom_meals for ingredient in meal.get("ingredients", [])}
    ingredients_dict = {ing.id: ing for ing in Ingredient.objects.filter(id__in=all_ingredient_ids)}

    for meal in custom_meals:
        name = "Custom Meal"
        description = f"{name} - {get_date_today()}"
        price = round(meal.get("price"))
        amount = meal.get("amount")

        product = Product(name=name, description=description, is_official=False, product_type="dish", price=price)

        # count weight for each product
        total_weight = sum(ingredient.get("weight", 0) for ingredient in meal.get("ingredients", []))
        product.weight = round(total_weight)

        # add product to creation list
        products_to_create.append(product)

        # prepare ProductIngredient for the product
        for ingredient_data in meal.get("ingredients", []):
            ingredient_id = ingredient_data.get("id")
            weight_grams = ingredient_data.get("weight")

            official_ingredient = ingredients_dict.get(ingredient_id)
            if official_ingredient:
                product_ingredient = ProductIngredient(product=product, ingredient=official_ingredient, weight_grams=weight_grams)
                product_ingredients_to_create.append(product_ingredient)

        # prepare OrderProduct для этого продукта
        order_products_to_create.append(OrderProduct(order=order, product=product, amount=amount, price=price))

    # Bulk create Products
    Product.objects.bulk_create(products_to_create)

    # Update Product in ProductIngredient
    for i, product in enumerate(products_to_create):
        for pi in product_ingredients_to_create:
            if pi.product == product:
                pi.product_id = product.id

        # Update Product in OrderProduct
        order_products_to_create[i].product_id = product.id

    # Bulk create ProductIngredient & OrderProduct
    ProductIngredient.objects.bulk_create(product_ingredients_to_create)
    OrderProduct.objects.bulk_create(order_products_to_create)


def get_date_today():
    current_date = datetime.today()
    return current_date.strftime("%d-%m-%Y %H:%M:%S")


def get_price_with_tax(service, tax, price):
    price_service = price + (price * service)
    return round(price_service + (price_service * tax))


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
        return Promo.objects.get(promo_code=promo_code, active_from__lte=now, active_until__gte=now, used_count__lt=F('usage_limit'))
    except Promo.DoesNotExist:
        return None
