# models.py

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator, MaxLengthValidator
from django.db.models import Sum, F
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone


class User(AbstractUser):
    # login/pass, optional - first_name, last_names, email, is_staff, is_active, email
    ROLES = (
        ("owner", "Owner"),
        ("administrator", "Administrator"),
        ("manager", "Manager"),
        ("table", "Table"),
        ("kitchen", "Kitchen"),
        ("user", "User"),
    )
    nickname = models.CharField(max_length=50, blank=True, default="")
    role = models.CharField(max_length=15, choices=ROLES, default="user")


class NutritionalValue(models.Model):
    # Per 100 gram

    calories = models.FloatField(validators=[MinValueValidator(0)], default=0)
    proteins = models.FloatField(validators=[MinValueValidator(0)], default=0)
    fats = models.FloatField(validators=[MinValueValidator(0)], default=0)
    saturated_fats = models.FloatField(validators=[MinValueValidator(0)], default=0)
    carbohydrates = models.FloatField(validators=[MinValueValidator(0)], default=0)
    sugars = models.FloatField(validators=[MinValueValidator(0)], default=0)
    fiber = models.FloatField(validators=[MinValueValidator(0)], default=0)

    vitamin_a = models.FloatField(validators=[MinValueValidator(0)], default=0)
    vitamin_c = models.FloatField(validators=[MinValueValidator(0)], default=0)
    vitamin_d = models.FloatField(validators=[MinValueValidator(0)], default=0)
    vitamin_e = models.FloatField(validators=[MinValueValidator(0)], default=0)
    vitamin_k = models.FloatField(validators=[MinValueValidator(0)], default=0)
    thiamin = models.FloatField(validators=[MinValueValidator(0)], default=0)
    riboflavin = models.FloatField(validators=[MinValueValidator(0)], default=0)
    niacin = models.FloatField(validators=[MinValueValidator(0)], default=0)
    vitamin_b6 = models.FloatField(validators=[MinValueValidator(0)], default=0)
    folate = models.FloatField(validators=[MinValueValidator(0)], default=0)
    vitamin_b12 = models.FloatField(validators=[MinValueValidator(0)], default=0)

    calcium = models.FloatField(validators=[MinValueValidator(0)], default=0)
    iron = models.FloatField(validators=[MinValueValidator(0)], default=0)
    magnesium = models.FloatField(validators=[MinValueValidator(0)], default=0)
    phosphorus = models.FloatField(validators=[MinValueValidator(0)], default=0)
    potassium = models.FloatField(validators=[MinValueValidator(0)], default=0)
    sodium = models.FloatField(validators=[MinValueValidator(0)], default=0)
    zinc = models.FloatField(validators=[MinValueValidator(0)], default=0)
    copper = models.FloatField(validators=[MinValueValidator(0)], default=0)
    manganese = models.FloatField(validators=[MinValueValidator(0)], default=0)
    selenium = models.FloatField(validators=[MinValueValidator(0)], default=0)

    def to_dict(self, exclude_fields=None):
        if exclude_fields is None:
            exclude_fields = ["id"]
        return {
            field.name: getattr(self, field.name)
            for field in self._meta.fields
            if field.name not in exclude_fields
        }

    def __str__(self):
        return f"Nutritional Value (ID: {self.id})"


class Ingredient(models.Model):
    INGREDIENT_TYPES = (  # if update - update kitchen & manage/ingredients
        ("base", "Base"),
        ("protein", "Protein"),
        ("vegetable", "Vegetable"),
        ("dairy", "Dairy"),
        ("fruit", "Fruit"),
        ("topping", "Topping"),
        ("other", "Other"),
    )
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to="ingredients/")
    ingredient_type = models.CharField(max_length=10, choices=INGREDIENT_TYPES, default="other")
    step = models.FloatField(default=1, validators=[MinValueValidator(0.05), MaxValueValidator(5)])
    min_order = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(50)])
    max_order = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(500)])
    is_available = models.BooleanField(default=True)

    price_per_gram = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(999)])
    price_multiplier = models.FloatField(default=3.00, validators=[MinValueValidator(0)])
    custom_price = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])

    # for 100g
    nutritional_value = models.OneToOneField(NutritionalValue, on_delete=models.PROTECT, related_name="ingredient")

    def clean(self):
        if self.max_order < self.min_order:
            raise ValidationError("Max order must be greater than or equal to Min order.")

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.nutritional_value:
            self.nutritional_value = NutritionalValue.objects.create()
        self.clean()
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
        ("dish", "Dish"),
        ("drink", "Drink"),
    )
    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPES, default="dish")

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="products/", null=True, blank=True)
    is_menu = models.BooleanField(default=False)  # for Menu
    is_official = models.BooleanField()  # True - copy of Menu w/ different kCal, False - custom meal
    is_available = models.BooleanField(default=False)  # for Menu if there's no Ingredients

    price = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    price_multiplier = models.FloatField(default=3.0, validators=[MinValueValidator(0)])
    custom_price = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    weight = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0)])

    ingredients = models.ManyToManyField("Ingredient", through="ProductIngredient")
    nutritional_value = models.OneToOneField(NutritionalValue, on_delete=models.PROTECT, related_name="product")

    def clean(self):
        super().clean()
        if self.is_menu and (not self.image or not self.name or not self.description or not self.ingredients):
            raise ValidationError("Menu products must have an image and other data.")

    @transaction.atomic
    def save(self, *args, **kwargs):
        try:
            self.nutritional_value
        except AttributeError:
            self.nutritional_value = NutritionalValue.objects.create()
        self.full_clean()
        super().save(*args, **kwargs)

        if self.productingredient_set.exists():
            new_nutritional_value, total_weight = self.calculate_nutritional_value()
            NutritionalValue.objects.filter(id=self.nutritional_value.id).update(**new_nutritional_value.to_dict())

            self.weight = round(total_weight) if total_weight > 0 else None
            self.price = self.calculate_base_price()
            Product.objects.filter(pk=self.pk).update(weight=self.weight, price=self.price)

    def calculate_nutritional_value(self):
        nutritional_value = NutritionalValue()
        product_ingredients = self.productingredient_set.select_related('ingredient__nutritional_value').all()

        if not product_ingredients.exists():
            return nutritional_value, 0

        total_weight = product_ingredients.aggregate(total=Sum("weight_grams"))["total"] or 0

        for product_ingredient in product_ingredients:
            ingredient = product_ingredient.ingredient
            weight_ratio = product_ingredient.weight_grams / 100

            for field in NutritionalValue._meta.fields:
                if field.name != "id":
                    current_value = getattr(nutritional_value, field.name) or 0
                    ingredient_value = getattr(ingredient.nutritional_value, field.name) or 0
                    new_value = current_value + (ingredient_value * weight_ratio)
                    setattr(nutritional_value, field.name, round(new_value, 2))

        return nutritional_value, total_weight

    def calculate_base_price(self):
        total_price = self.productingredient_set.aggregate(total=Sum(F("ingredient__price_per_gram") * F("weight_grams")))["total"] or 0
        return round(total_price)

    def get_selling_price(self):
        if self.custom_price is not None and self.custom_price > 0:
            return self.custom_price
        return self.price * self.price_multiplier

    def get_price_for_calories(self, calories):
        base_calories = self.nutritional_value.calories
        price_factor = calories / base_calories
        return self.get_selling_price() * price_factor

    def is_dish(self):
        return self.product_type == "dish"

    def __str__(self):
        return self.name


class ProductIngredient(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    ingredient = models.ForeignKey("Ingredient", on_delete=models.PROTECT)
    weight_grams = models.FloatField(validators=[MinValueValidator(0)])

    def clean(self):
        super().clean()
        if self.weight_grams > self.ingredient.max_order:
            raise ValidationError(
                f"Weight is too big for ingredient \"{self.ingredient.name}\", "
                f"allowed {self.ingredient.max_order}g max, you have {self.weight_grams}")
        if self.weight_grams < self.ingredient.min_order:
            raise ValidationError(
                f"Weight is too small for ingredient \"{self.ingredient.name}\", "
                f"allowed {self.ingredient.min_order}g min, you have {self.weight_grams}")
        if not self.ingredient.is_available:
            raise ValidationError(f"Ingredient {self.ingredient.name} is not available")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Order(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['order_status']),
            models.Index(fields=['order_type']),
            models.Index(fields=['payment_type']),
            models.Index(fields=['is_paid']),
            models.Index(fields=['is_refunded']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user_id']),
        ]

    PENDING = "pending"
    COOKING = "cooking"
    READY = "ready"
    FINISHED = "finished"
    CANCELLED = "cancelled"
    PROBLEM = "problem"

    STATUS_CHOICES = (
        (PENDING, "Pending"),  # waiting for payment
        (COOKING, "Cooking"),  # paid - ready for Kitchen to cook
        (READY, "Ready"),  # is ready for Manager to deliver
        (FINISHED, "Finished"),  # Done!
        (CANCELLED, "Cancelled"),  # cancelled
        (PROBLEM, "Problem"),  # cancelled
    )
    ORDER_TYPES = (
        ("offline", "Offline"),
        ("takeaway", "Take Away"),
        ("online", "Online"),
    )
    PAYMENT_TYPES = (
        ("cash", "Cash"),
        ("card", "Card"),
        ("qr", "QR"),
    )
    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES, default="offline")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default="card")

    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="first_order")
    user_last_update = models.ForeignKey(User, on_delete=models.PROTECT, related_name="last_update")
    nutritional_value = models.OneToOneField(NutritionalValue, on_delete=models.PROTECT, related_name="order")

    tax = models.IntegerField(default=7, validators=[MinValueValidator(0), MaxValueValidator(15)])
    service = models.IntegerField(default=1, validators=[MinValueValidator(0), MaxValueValidator(10)])
    base_price = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    total_price = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    payment_id = models.CharField(max_length=100, blank=True)
    is_paid = models.BooleanField(default=False)
    is_refunded = models.BooleanField(default=False)
    public_note = models.TextField(null=True, blank=True, max_length=500, validators=[MaxLengthValidator(1000)])
    private_note = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)

    show_public = models.BooleanField(default=True)

    def clean(self):
        super().clean()

        if not self.is_paid and self.is_refunded:
            raise ValidationError("The order can not be refunded if it is not paid.")

        if not self.is_paid and self.order_status in [Order.COOKING, Order.READY, Order.FINISHED]:
            raise ValidationError("The order is not paid. It should be paid before continuing.")

        if self.is_paid and not self.payment_id:
            if self.payment_type != "cash":  # TEMPORARY, until I know how works payment system
                raise ValidationError("Please provide the Payment ID for the order.")

        if self.is_paid and self.order_status == Order.PENDING:
            raise ValidationError("The order has been paid and cannot be marked as \"Pending\". "
                                  "If something went wrong, please change the status to \"Problem\".")

        if self.is_refunded and not self.private_note:
            raise ValidationError("Please add an ID for the refund and describe what happened. Thank you.")

        if self.order_status == Order.PROBLEM and not self.private_note:
            raise ValidationError("Please add a brief note about the problem to the private notes. Thank you.")

        if self.payment_type == "cash" and self.order_type == "online":
            raise ValidationError(f"It’s not possible to pay with cash for online orders.")

        if not self.user_last_update:
            raise ValidationError("Please specify the user making the update.")

    def save(self, *args, **kwargs):
        super().full_clean()
        if self.is_refunded and self.refunded_at is None:
            self.refunded_at = timezone.now()

        if self.is_paid and not self.paid_at:
            self.paid_at = timezone.now()

        if self.order_status == self.READY and not self.ready_at:
            self.ready_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id}"


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="products")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    amount = models.IntegerField(validators=[MinValueValidator(1)])
    price = models.IntegerField(validators=[MinValueValidator(0)])
    do_blend = models.BooleanField(default=True)


class OrderHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, related_name="history")
    order_deleted_id = models.IntegerField(null=True, blank=True)

    order_status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    order_type = models.CharField(max_length=20, choices=Order.ORDER_TYPES)
    payment_type = models.CharField(max_length=20, choices=Order.PAYMENT_TYPES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="order_history_user")
    user_last_update = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="order_history_last_update")
    tax = models.IntegerField()
    service = models.IntegerField()
    base_price = models.IntegerField()
    total_price = models.IntegerField()
    payment_id = models.CharField(max_length=100, blank=True)
    is_paid = models.BooleanField(default=False)
    is_refunded = models.BooleanField(default=False)
    public_note = models.TextField(null=True, blank=True, max_length=500)
    private_note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_deleted(self):
        return bool(self.order_deleted_id)

    def __str__(self):
        order = f"Order #{self.order.id}" if self.order else f"deleted Order #{self.order_deleted_id}"
        return f"OrderHistory for {order}."


# Creates signal to create OrderHistory when Order saves
@receiver(post_save, sender=Order)
def create_order_history(sender, instance, **kwargs):
    OrderHistory.objects.create(
        order=instance,
        order_status=instance.order_status,
        order_type=instance.order_type,
        payment_type=instance.payment_type,
        user=instance.user,
        user_last_update=instance.user_last_update,
        tax=instance.tax,
        service=instance.service,
        base_price=instance.base_price,
        total_price=instance.total_price,
        payment_id=instance.payment_id,
        is_paid=instance.is_paid,
        is_refunded=instance.is_refunded,
        public_note=instance.public_note,
        private_note=instance.private_note,
    )


@receiver(pre_delete, sender=Order)
def save_order_id_before_delete(sender, instance, **kwargs):
    with transaction.atomic():
        for history in instance.history.all():
            history.order_deleted_id = instance.id
            history.save()


class Setting(models.Model):
    service = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    tax = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(1)])
    can_order = models.BooleanField(default=True)
    close_kitchen_before = models.IntegerField(default=20, validators=[MinValueValidator(0), MaxValueValidator(120)])

    minimum_order_amount = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    maximum_order_amount = models.IntegerField(default=3000000, validators=[MinValueValidator(0)])
    # weight in grams
    maximum_order_weight = models.IntegerField(default=5000, validators=[MinValueValidator(0)])
    minimum_blend_weight = models.IntegerField(default=100, validators=[MinValueValidator(0)])

    def save(self, *args, **kwargs):
        self.pk = 1
        super(Setting, self).save(*args, **kwargs)


class DaySetting(models.Model):
    """
    Time handling conventions:
    - All times are stored in UTC
    - Frontend is responsible for local time conversion
    - API accepts and returns UTC timestamps
    - Database queries should use UTC for comparisons
    """
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday')
    ]

    day = models.IntegerField(choices=DAY_CHOICES, unique=True)
    is_open = models.BooleanField(default=True)
    open_hours = models.TimeField(null=True, blank=True)
    close_hours = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_day_display()}: {'Open' if self.is_open else 'Closed'}"


class Promo(models.Model):
    discount = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(0.5)])
    promo_code = models.CharField(max_length=20, unique=True)
    active_from = models.DateTimeField()
    active_until = models.DateTimeField()
    usage_limit = models.IntegerField(validators=[MinValueValidator(0)])
    used_count = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    creator = models.ForeignKey(User, on_delete=models.PROTECT, related_name="creator")

    def clean(self):
        super().clean()
        if self.used_count > self.usage_limit:
            raise ValidationError("The used count cannot exceed the usage limit.")

        if self.active_until <= self.active_from:
            raise ValidationError("The end date cannot be earlier than the start date.")

        if timezone.now() > self.active_until:
            raise ValidationError("The promo has already expired. Please set a future end date.")

        if not (0 <= self.discount <= 1):
            raise ValidationError("Discount must be a value between 0 and 1.")

    def save(self, *args, **kwargs):
        self.full_clean()

    def is_available(self):
        now = timezone.now()
        return self.active_from <= now <= self.active_until and self.used_count < self.usage_limit

    @staticmethod
    def get_active_promos():
        now = timezone.now()
        return Promo.objects.filter(active_from__lte=now, active_until__gte=now)


class PromoUsage(models.Model):
    promo = models.ForeignKey(Promo, on_delete=models.CASCADE, null=True, related_name="used_promo")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="used_user")
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, related_name="user_for_order")
    discounted = models.IntegerField(validators=[MinValueValidator(0)])
    used_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.full_clean()
        with transaction.atomic():
            if not self.pk:
                promo = Promo.objects.select_for_update().get(pk=self.promo.pk)
                if not promo.promo.is_available():
                    raise ValidationError("This promo code is no longer available.")

                promo.used_count = promo.used_count + 1
                promo.save(update_fields=["used_count"])
            super().save(*args, **kwargs)
