# models.py

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Sum, F


class User(AbstractUser):
    # login/pass, optional - first_name, last_names, email, is_staff, is_active, email
    ROLES = (
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('table', 'Table'),
        ('kitchen', 'Kitchen'),
        ('other', 'Other'),
    )
    nickname = models.CharField(max_length=50, blank=True, default="")
    role = models.CharField(max_length=10, choices=ROLES, default='other')


class NutritionalValue(models.Model):
    # Per 100 gram

    # Основные нутриенты
    calories = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    proteins = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    fats = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    saturated_fats = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    carbohydrates = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    sugars = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    fiber = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)], default=0)

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

    def to_dict(self, exclude_fields=None):
        if exclude_fields is None:
            exclude_fields = ['id']
        return {
            field.name: float(getattr(self, field.name)) if isinstance(getattr(self, field.name), Decimal) else getattr(self, field.name)
            for field in self._meta.fields
            if field.name not in exclude_fields
        }

    def __str__(self):
        return f"Nutritional Value (ID: {self.id})"


class Ingredient(models.Model):
    INGREDIENT_TYPES = (
        ('base', 'Base'),
        ('protein', 'Protein'),
        ('vegetable', 'Vegetable'),
        ('dairy', 'Dairy'),
        ('fruit', 'Fruit'),
        ('topping', 'Topping'),
        ('other', 'Other'),
    )
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='ingredients/')
    ingredient_type = models.CharField(max_length=10, choices=INGREDIENT_TYPES, default='other')
    step = models.DecimalField(max_digits=2, decimal_places=1, default=1)
    min_order = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(50)])
    max_order = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(500)])
    available = models.BooleanField(default=True)

    price_per_gram = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(999)])
    price_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=3.00, validators=[MinValueValidator(0)])
    custom_price = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])

    # for 100g
    nutritional_value = models.OneToOneField(NutritionalValue, on_delete=models.CASCADE, related_name='ingredient')

    private_note = models.TextField(blank=True)

    def clean(self):
        if self.max_order < self.min_order:
            raise ValidationError("Max order must be greater than or equal to Min order.")

    def save(self, *args, **kwargs):
        if not self.nutritional_value:
            self.nutritional_value = NutritionalValue.objects.create()
        super().save(*args, **kwargs)

    def get_selling_price_for_weight(self, weight):
        price = self.get_selling_price() * weight
        return round(price)

    def get_selling_price(self):
        if self.custom_price is not None and self.custom_price > 0:
            return self.custom_price
        return round(self.price_per_gram * self.price_multiplier)

    def __str__(self):
        return f"Ingredient ({self.id}): {self.name}"


class Product(models.Model):
    PRODUCT_TYPES = (
        ('dish', 'Dish'),
        ('drink', 'Drink'),
    )
    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPES, default="dish")

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    is_official = models.BooleanField(default=False)

    weight = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0)])
    private_note = models.TextField(blank=True)

    price = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    price_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=3.00, validators=[MinValueValidator(0)])
    custom_price = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])

    ingredients = models.ManyToManyField('Ingredient', through='ProductIngredient')
    nutritional_value = models.OneToOneField(NutritionalValue, on_delete=models.CASCADE, related_name='product', null=True, blank=True)

    def clean(self):
        super().clean()
        if self.is_official and not self.image:
            raise ValidationError("Official products must have an image.")

    def calculate_base_price(self):
        total_price = self.productingredient_set.aggregate(
            total=Sum(F('ingredient__price_per_gram') * F('weight_grams'))
        )['total'] or 0
        return round(total_price)

    def get_selling_price(self):
        if self.custom_price is not None and self.custom_price > 0:
            return self.custom_price
        return self.price * self.price_multiplier

    def get_price_for_calories(self, calories):
        base_calories = self.nutritional_value.calories
        price_factor = calories / base_calories
        return self.get_selling_price() * price_factor

    def calculate_nutritional_value(self):
        nutritional_value = NutritionalValue()
        product_ingredients = self.productingredient_set.all()
        total_weight = Decimal(product_ingredients.aggregate(total=Sum('weight_grams'))['total'] or 0)

        for product_ingredient in product_ingredients:
            ingredient = product_ingredient.ingredient
            weight_ratio = Decimal(product_ingredient.weight_grams) / Decimal('100')

            for field in NutritionalValue._meta.fields:
                if field.name != 'id':
                    current_value = getattr(nutritional_value, field.name) or Decimal('0')
                    ingredient_value = getattr(ingredient.nutritional_value, field.name) or Decimal('0')
                    new_value = current_value + (ingredient_value * weight_ratio)
                    setattr(nutritional_value, field.name, round(new_value, 2))

        return nutritional_value, total_weight

    def is_dish(self):
        return self.product_type == 'dish'

    @transaction.atomic
    def save(self, *args, **kwargs):
        self.full_clean()
        is_new = self.pk is None

        if is_new and not hasattr(self, 'nutritional_value'):
            self.nutritional_value = NutritionalValue.objects.create()

        super().save(*args, **kwargs)

        if self.pk:
            new_nutritional_value, total_weight = self.calculate_nutritional_value()

            if total_weight is not None and total_weight > 0:
                self.weight = int(total_weight)
            else:
                self.weight = None

            if self.nutritional_value:
                for field in NutritionalValue._meta.fields:
                    if field.name != 'id':
                        setattr(self.nutritional_value, field.name, getattr(new_nutritional_value, field.name))
                self.nutritional_value.save()
            else:
                new_nutritional_value.save()
                self.nutritional_value = new_nutritional_value

            self.price = self.calculate_base_price()

            Product.objects.filter(pk=self.pk).update(
                weight=self.weight,
                nutritional_value=self.nutritional_value,
                price=self.price
            )

    def __str__(self):
        return self.name


class ProductIngredient(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE)
    weight_grams = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])

    def clean(self):
        if self.weight_grams > self.ingredient.max_order:
            raise ValidationError(
                f"Weight is too big for ingredient \"{self.ingredient.name}\", "
                f"allowed {self.ingredient.max_order}g max, you have {self.weight_grams}")
        if self.weight_grams < self.ingredient.min_order:
            raise ValidationError(
                f"Weight is too small for ingredient \"{self.ingredient.name}\", "
                f"allowed {self.ingredient.min_order}g min, you have {self.weight_grams}")


class Order(models.Model):
    STATUS_CHOICES = (
        ('waiting', 'Waiting'),
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
    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES, default='offline')
    payment_type = models.CharField(max_length=20, choices=ORDER_TYPES, default='card')

    table = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'table'})
    price = models.IntegerField(default=0)
    total_price = models.IntegerField(default=0)
    payment_id = models.CharField(max_length=100, blank=True)
    is_refunded = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])


class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
