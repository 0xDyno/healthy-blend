import json

from django.core.exceptions import ValidationError

from .models import Product, Ingredient, Order


def big_validator(data: json):
    official_meals = data.get('officialMeals', [])
    custom_meals = data.get('customMeals', [])
    price = data.get('price')

    if not (official_meals and custom_meals):
        raise ValidationError(message="The cart is empty")

    if not isinstance(price, (int, float)):
        raise ValidationError(message="Wrong price format")
    if data.get("payment_type") not in ["cash", "card", "qr"]:
        raise ValidationError(message="Wrong payment type")

    price_for_official_meal = validate_official_meal(official_meals)
    price_for_custom_meal = validate_custom_meal(custom_meals)

    total_off_price = price_for_official_meal + price_for_custom_meal
    if round(total_off_price) != round(price):
        raise ValidationError(message=f"Wrong calculated total Price. Web price: {price}, off price {total_off_price}")
    return total_off_price


def validate_official_meal(official_meals):
    total_price = 0
    for official_meal in official_meals:
        meal_id = official_meal.get("id")
        amount = official_meal.get("quantity")
        calories = official_meal.get("calories")
        price = official_meal.get("price")

        if not isinstance(meal_id, int):
            raise ValidationError(message="Official Meal - wrong type for id.")
        if not isinstance(amount, int) or amount < 1 or amount > 5:
            raise ValidationError(message="Official Meal - wrong type for quantity.")
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
        if round(official_price) != round(price):
            raise ValidationError(message="Official Meal - wrong calculated price on web-site.")

        total_price += official_price * amount
    return total_price


def validate_custom_meal(custom_meals):
    total_price = 0
    for custom_meal in custom_meals:
        product_price = 0

        ingredients = custom_meal.get("ingredients")
        amount = custom_meal.get("quantity")
        price = custom_meal.get("price")

        if not isinstance(ingredients, list):
            raise ValidationError(message="Custom Meal - wrong type for ingredients.")
        if not isinstance(amount, int) or amount < 1 or amount > 5:
            raise ValidationError(message="Custom Meal - wrong type for quantity.")
        if not isinstance(price, (int, float)):
            raise ValidationError(message="Custom Meal - wrong type for price.")

        for ingredient in ingredients:
            ingredient_id = ingredient.get("id")
            weight = ingredient.get("weight")

            if not isinstance(ingredient_id, int) or not isinstance(weight, int):
                raise ValidationError(message="Custom Meal - wrong type for ingredient id.")

            ingredient_object = Ingredient.objects.filter(id=ingredient_id).first()
            if ingredient_object is None:
                raise ValidationError(message="Custom Meal - wrong ingredient id.")
            if weight > ingredient_object.max_order or weight < ingredient_object.min_order:
                raise ValidationError(message=f"Custom Meal - wrong weight for ingredient, received {weight}, "
                                              f"allowed {ingredient_object.min_order} - {ingredient_object.max_order}.")

            product_price += ingredient_object.get_selling_price_for_weight(weight)
        if round(product_price) != round(price):
            raise ValidationError(message="Custom Meal - wrong calculated price on web-site.")

        total_price += product_price
    return total_price


def process_official_meal(official_meals, order: Order):
    all_products = {}
    for official_meal in official_meals:
        meal_id = official_meal.get("id")
        amount = official_meal.get("quantity")
        calories = official_meal.get("calories")
        price = round(official_meal.get("price"))

        product = Product.objects.filter(id=meal_id).first()
        if product.is_dish():
            pass
        else:
            pass


def process_custom_meal(custom_meals, order: Order):
    pass


