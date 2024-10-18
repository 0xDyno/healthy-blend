from django.core.management.base import BaseCommand
from core.models import NutritionalValue, Ingredient, Product, ProductIngredient


class Command(BaseCommand):
    help = 'Populates the database with ingredients and products'

    def handle(self, *args, **options):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from decimal import Decimal

        # Create ingredients
        ingredients = [
            {
                'name': 'Chicken fillet',
                'description': 'Tender chicken fillet',
                'min_order': 50,
                'max_order': 200,
                'price_per_gram': 83,
                'nutritional_value': {
                    'calories': 165,
                    'proteins': 31,
                    'fats': 3.6,
                    'carbohydrates': 0,
                    'saturated_fats': 1.0,
                    'sugars': 0,
                    'fiber': 0,
                }
            },
            {
                'name': 'Rice',
                'description': 'White long-grain rice',
                'min_order': 50,
                'max_order': 200,
                'price_per_gram': 5,
                'nutritional_value': {
                    'calories': 130,
                    'proteins': 2.7,
                    'fats': 0.3,
                    'carbohydrates': 28,
                    'saturated_fats': 0.1,
                    'sugars': 0.1,
                    'fiber': 0.4,
                }
            },
            {
                'name': 'Carrot',
                'description': 'Fresh carrot',
                'min_order': 20,
                'max_order': 100,
                'price_per_gram': 20,
                'nutritional_value': {
                    'calories': 41,
                    'proteins': 0.9,
                    'fats': 0.2,
                    'carbohydrates': 9.6,
                    'saturated_fats': 0,
                    'sugars': 4.7,
                    'fiber': 2.8,
                }
            },
            {
                'name': 'Onion',
                'description': 'Yellow onion',
                'min_order': 20,
                'max_order': 100,
                'price_per_gram': 22,
                'nutritional_value': {
                    'calories': 40,
                    'proteins': 1.1,
                    'fats': 0.1,
                    'carbohydrates': 9.3,
                    'saturated_fats': 0,
                    'sugars': 4.2,
                    'fiber': 1.7,
                }
            },
            {
                'name': 'Soy sauce',
                'description': 'Classic soy sauce',
                'min_order': 5,
                'max_order': 50,
                'price_per_gram': 73,
                'nutritional_value': {
                    'calories': 53,
                    'proteins': 5.6,
                    'fats': 0.1,
                    'carbohydrates': 4.9,
                    'saturated_fats': 0,
                    'sugars': 0.4,
                    'fiber': 0.8,
                }
            },
            {
                'name': 'Garlic',
                'description': 'Fresh garlic',
                'min_order': 5,
                'max_order': 30,
                'price_per_gram': 66,
                'nutritional_value': {
                    'calories': 149,
                    'proteins': 6.4,
                    'fats': 0.5,
                    'carbohydrates': 33,
                    'saturated_fats': 0.1,
                    'sugars': 1.0,
                    'fiber': 2.1,
                }
            },
            {
                'name': 'Ginger',
                'description': 'Fresh ginger root',
                'min_order': 5,
                'max_order': 30,
                'price_per_gram': 57,
                'nutritional_value': {
                    'calories': 80,
                    'proteins': 1.8,
                    'fats': 0.8,
                    'carbohydrates': 17.8,
                    'saturated_fats': 0.2,
                    'sugars': 1.7,
                    'fiber': 2.0,
                }
            },
            {
                'name': 'Sesame oil',
                'description': 'Unrefined sesame oil',
                'min_order': 5,
                'max_order': 30,
                'price_per_gram': 68,
                'nutritional_value': {
                    'calories': 884,
                    'proteins': 0,
                    'fats': 100,
                    'carbohydrates': 0,
                    'saturated_fats': 14.2,
                    'sugars': 0,
                    'fiber': 0,
                }
            },
            {
                'name': 'Sesame seeds',
                'description': 'Sesame seeds',
                'min_order': 5,
                'max_order': 30,
                'price_per_gram': 71,
                'nutritional_value': {
                    'calories': 573,
                    'proteins': 17.7,
                    'fats': 49.7,
                    'carbohydrates': 23.5,
                    'saturated_fats': 7.0,
                    'sugars': 0.3,
                    'fiber': 11.8,
                }
            },
            {
                'name': 'Green onion',
                'description': 'Fresh green onion',
                'min_order': 10,
                'max_order': 50,
                'price_per_gram': 30,
                'nutritional_value': {
                    'calories': 32,
                    'proteins': 1.8,
                    'fats': 0.2,
                    'carbohydrates': 7.3,
                    'saturated_fats': 0,
                    'sugars': 2.3,
                    'fiber': 2.6,
                }
            },
            {
                'name': 'Egg',
                'description': 'Chicken egg',
                'min_order': 1,
                'max_order': 10,
                'price_per_gram': 28,
                'nutritional_value': {
                    'calories': 155,
                    'proteins': 12.6,
                    'fats': 11.5,
                    'carbohydrates': 0.7,
                    'saturated_fats': 3.3,
                    'sugars': 0.4,
                    'fiber': 0,
                }
            },
            {
                'name': 'Salt',
                'description': 'Table salt',
                'min_order': 1,
                'max_order': 10,
                'price_per_gram': 100,
                'nutritional_value': {
                    'calories': 0,
                    'proteins': 0,
                    'fats': 0,
                    'carbohydrates': 0,
                    'saturated_fats': 0,
                    'sugars': 0,
                    'fiber': 0,
                }
            },
            {
                'name': 'Pepper',
                'description': 'Ground black pepper',
                'min_order': 1,
                'max_order': 10,
                'price_per_gram': 110,
                'nutritional_value': {
                    'calories': 251,
                    'proteins': 10.4,
                    'fats': 3.3,
                    'carbohydrates': 63.9,
                    'saturated_fats': 1.4,
                    'sugars': 0.6,
                    'fiber': 25.3,
                }
            },
            {
                'name': 'Sunflower oil',
                'description': 'Sunflower oil',
                'min_order': 5,
                'max_order': 50,
                'price_per_gram': 49,
                'nutritional_value': {
                    'calories': 884,
                    'proteins': 0,
                    'fats': 100,
                    'carbohydrates': 0,
                    'saturated_fats': 10.3,
                    'sugars': 0,
                    'fiber': 0,
                }
            },
            {
                'name': 'Corn',
                'description': 'Canned corn',
                'min_order': 20,
                'max_order': 100,
                'price_per_gram': 21,
                'nutritional_value': {
                    'calories': 96,
                    'proteins': 3.2,
                    'fats': 1.2,
                    'carbohydrates': 21,
                    'saturated_fats': 0.2,
                    'sugars': 3.2,
                    'fiber': 2.4,
                }
            },
        ]

        # Create ingredients in the database
        created_ingredients = []
        for ingredient_data in ingredients:
            nutritional_value_data = ingredient_data.pop('nutritional_value')
            nutritional_value = NutritionalValue.objects.create(**nutritional_value_data)
            ingredient = Ingredient.objects.create(nutritional_value=nutritional_value, **ingredient_data)
            created_ingredients.append(ingredient)

        # Create dishes
        products = [
            {
                'name': 'Chicken with rice',
                'description': 'Tender chicken with rice and vegetables',
                'price': 10,
                'is_official': True,
                'product_type': 'dish',
                'image': SimpleUploadedFile(name='kwc.png', content=open('/Users/dyno/Desktop/kwc.png', 'rb').read(),
                                            content_type='image/png'),
                'ingredients': [
                    {'ingredient': 'Chicken fillet', 'weight_grams': 150},
                    {'ingredient': 'Rice', 'weight_grams': 100},
                    {'ingredient': 'Carrot', 'weight_grams': 50},
                    {'ingredient': 'Onion', 'weight_grams': 30},
                    {'ingredient': 'Soy sauce', 'weight_grams': 10},
                    {'ingredient': 'Sunflower oil', 'weight_grams': 10},
                    {'ingredient': 'Salt', 'weight_grams': 2},
                    {'ingredient': 'Pepper', 'weight_grams': 1},
                ]
            },
            {
                'name': 'Fried rice with egg',
                'description': 'Classic fried rice with egg and vegetables',
                'price': 10,
                'is_official': False,
                'product_type': 'dish',
                'ingredients': [
                    {'ingredient': 'Rice', 'weight_grams': 200},
                    {'ingredient': 'Egg', 'weight_grams': 50},
                    {'ingredient': 'Carrot', 'weight_grams': 30},
                    {'ingredient': 'Green onion', 'weight_grams': 20},
                    {'ingredient': 'Corn', 'weight_grams': 30},
                    {'ingredient': 'Soy sauce', 'weight_grams': 15},
                    {'ingredient': 'Sunflower oil', 'weight_grams': 15},
                    {'ingredient': 'Salt', 'weight_grams': 2},
                    {'ingredient': 'Pepper', 'weight_grams': 1},
                ]
            },
            {
                'name': 'Sesame chicken',
                'description': 'Crispy chicken in sesame coating',
                'price': 10,
                'is_official': True,
                'product_type': 'dish',
                'image': SimpleUploadedFile(name='kwk.png', content=open('/Users/dyno/Desktop/kwk.png', 'rb').read(),
                                            content_type='image/png'),
                'ingredients': [
                    {'ingredient': 'Chicken fillet', 'weight_grams': 200},
                    {'ingredient': 'Sesame seeds', 'weight_grams': 20},
                    {'ingredient': 'Soy sauce', 'weight_grams': 20},
                    {'ingredient': 'Sesame oil', 'weight_grams': 10},
                    {'ingredient': 'Garlic', 'weight_grams': 5},
                    {'ingredient': 'Ginger', 'weight_grams': 5},
                    {'ingredient': 'Sunflower oil', 'weight_grams': 20},
                    {'ingredient': 'Salt', 'weight_grams': 2},
                    {'ingredient': 'Pepper', 'weight_grams': 1},
                ]
            },
        ]

        # Create dishes in the database
        for product_data in products:
            ingredients_data = product_data.pop('ingredients')
            product = Product.objects.create(**product_data)

            for ingredient_data in ingredients_data:
                ingredient_name = ingredient_data['ingredient']
                ingredient = next(i for i in created_ingredients if i.name == ingredient_name)
                ProductIngredient.objects.create(
                    product=product,
                    ingredient=ingredient,
                    weight_grams=ingredient_data['weight_grams']
                )

        print("Ingredients and dishes successfully created!")