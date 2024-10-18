from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Sum


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
    price = models.IntegerField()
    is_official = models.BooleanField(default=False)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPES, default="dish")
    ingredients = models.ManyToManyField('Ingredient', through='ProductIngredient')
    nutritional_value = models.OneToOneField(NutritionalValue, on_delete=models.CASCADE, related_name='product', null=True, blank=True)

    private_note = models.TextField(blank=True)

    def clean(self):
        super().clean()
        if self.is_official and not self.image:
            raise ValidationError("Official products must have an image.")

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
                    setattr(nutritional_value, field.name, new_value)

        # Округляем значения до двух знаков после запятой
        for field in NutritionalValue._meta.fields:
            if field.name != 'id':
                current_value = getattr(nutritional_value, field.name) or Decimal('0')
                setattr(nutritional_value, field.name, round(current_value, 2))

        return nutritional_value, total_weight

    def save(self, *args, **kwargs):
        self.full_clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            self.nutritional_value = NutritionalValue.objects.create()
            super().save(update_fields=['nutritional_value'])
        else:
            new_nutritional_value, total_weight = self.calculate_nutritional_value()

            if self.nutritional_value:
                for field in NutritionalValue._meta.fields:
                    if field.name != 'id':
                        setattr(self.nutritional_value, field.name, getattr(new_nutritional_value, field.name))
                self.nutritional_value.save()
            else:
                new_nutritional_value.save()
                self.nutritional_value = new_nutritional_value
                super().save(update_fields=['nutritional_value'])

    def __str__(self):
        return self.name


class ProductIngredient(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    ingredient = models.ForeignKey('Ingredient', on_delete=models.CASCADE)
    weight_grams = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.product.save()  # Это вызовет пересчет пищевой ценности

    def delete(self, *args, **kwargs):
        product = self.product
        super().delete(*args, **kwargs)
        product.save()  # Это вызовет пересчет пищевой ценности


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
