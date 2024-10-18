from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    # login/pass, optional - first_name, last_names, email, is_staff, is_active, email
    ROLES = (
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('table', 'Table'),
        ('other', 'Other'),
    )
    role = models.CharField(max_length=10, choices=ROLES, default='other')


class NutritionalValue(models.Model):
    # Per 100 gram

    # Основные нутриенты
    calories = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    proteins = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    fats = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    saturated_fats = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    carbohydrates = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    sugars = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    fiber = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])

    # Витамины (значения по умолчанию 0)
    vitamin_a = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    vitamin_c = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    vitamin_d = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    vitamin_e = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    vitamin_k = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    thiamin = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    riboflavin = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    niacin = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    vitamin_b6 = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    folate = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    vitamin_b12 = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)

    # Минералы и микроэлементы (значения по умолчанию 0)
    calcium = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    iron = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    magnesium = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    phosphorus = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    potassium = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    sodium = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    zinc = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    copper = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    manganese = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    selenium = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)], default=0)

    def __str__(self):
        return f"Nutritional Value (ID: {self.id})"


class Ingredient(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    min_order = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    max_order = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(300)])
    available = models.BooleanField(default=True)
    price_per_gram = models.DecimalField(max_digits=6, decimal_places=2)
    nutritional_value = models.OneToOneField(NutritionalValue, on_delete=models.CASCADE, related_name='ingredient')

    private_note = models.TextField(blank=True)

    def clean(self):
        if self.max_order < self.min_order:
            raise ValidationError("Max order must be greater than or equal to Min order.")

    def save(self, *args, **kwargs):
        if not self.nutritional_value:
            self.nutritional_value = NutritionalValue.objects.create()
        super().save(*args, **kwargs)


class Product(models.Model):
    PRODUCT_TYPES = (
        ('dish', 'Dish'),
        ('drink', 'Drink'),
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_official = models.BooleanField(default=False)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPES)
    ingredients = models.ManyToManyField('Ingredient', through='ProductIngredient')

    private_note = models.TextField(blank=True)

    total_calories = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_proteins = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_fats = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_saturated_fats = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_carbohydrates = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_sugars = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_fiber = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_vitamins = models.JSONField(default=dict)
    total_microelements = models.JSONField(default=dict)

    def calculate_nutritional_value(self):
        nutritional_values = {
            'calories': 0, 'proteins': 0, 'fats': 0, 'saturated_fats': 0,
            'carbohydrates': 0, 'sugars': 0, 'fiber': 0
        }
        vitamins = {}
        minerals = {}

        for dish_ingredient in self.ingredients.all():
            weight_ratio = dish_ingredient.weight_grams / 100
            nv = dish_ingredient.ingredient.nutritional_value

            for field in nutritional_values.keys():
                nutritional_values[field] += getattr(nv, field) * weight_ratio

            for vitamin in ['vitamin_a', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k',
                            'thiamin', 'riboflavin', 'niacin', 'vitamin_b6', 'folate', 'vitamin_b12']:
                vitamins[vitamin] = vitamins.get(vitamin, 0) + getattr(nv, vitamin) * weight_ratio

            for mineral in ['calcium', 'iron', 'magnesium', 'phosphorus', 'potassium',
                            'sodium', 'zinc', 'copper', 'manganese', 'selenium']:
                minerals[mineral] = minerals.get(mineral, 0) + getattr(nv, mineral) * weight_ratio

        for field, value in nutritional_values.items():
            setattr(self, f'total_{field}', round(value, 2))

        self.total_vitamins = {k: round(v, 2) for k, v in vitamins.items()}
        self.total_microelements = {k: round(v, 2) for k, v in minerals.items()}

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Сначала сохраняем, чтобы получить id если это новый объект
        self.calculate_nutritional_value()
        super().save(*args, **kwargs)  # Сохраняем еще раз с обновленными значениями


class ProductIngredient(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE)
    weight_grams = models.IntegerField(validators=[MinValueValidator(0)])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.product.calculate_nutritional_value()
        self.product.save()

    def delete(self, *args, **kwargs):
        product = self.product
        super().delete(*args, **kwargs)
        product.calculate_nutritional_value()
        product.save()


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('cancelled', 'Cancelled'),
    )
    ORDER_TYPES = (
        ('offline', 'Offline'),
        ('online', "Online"),
    )
    PAYMENT_TYPES = (
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('qr', 'QR'),
    )
    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES, default='offline')
    payment_type = models.CharField(max_length=20, choices=ORDER_TYPES, default='card')

    table = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'table'})
    price = models.IntegerField()
    total_price = models.IntegerField()
    payment_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='dishes')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])


class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
