# serializers.py

# from rest_framework import serializers
# from .models import User, NutritionalValue, Ingredient, Product, ProductIngredient, Order, OrderProduct, History
#
#
# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ["id", "username", "role", "first_name", "last_name", "email", "is_staff", "is_active"]
#         extra_kwargs = {"password": {"write_only": True}}
#
#     def create(self, validated_data):
#         user = User.objects.create_user(**validated_data)
#         return user
#
#
# class NutritionalValueSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = NutritionalValue
#         fields = "__all__"
#
#
# class IngredientSerializer(serializers.ModelSerializer):
#     nutritional_value = NutritionalValueSerializer()
#
#     class Meta:
#         model = Ingredient
#         fields = "__all__"
#
#     def create(self, validated_data):
#         nutritional_value_data = validated_data.pop("nutritional_value")
#         nutritional_value = NutritionalValue.objects.create(**nutritional_value_data)
#         ingredient = Ingredient.objects.create(nutritional_value=nutritional_value, **validated_data)
#         return ingredient
#
#     def update(self, instance, validated_data):
#         nutritional_value_data = validated_data.pop("nutritional_value", None)
#         if nutritional_value_data:
#             nutritional_value_serializer = NutritionalValueSerializer(instance.nutritional_value, data=nutritional_value_data)
#             if nutritional_value_serializer.is_valid():
#                 nutritional_value_serializer.save()
#         return super().update(instance, validated_data)
#
#
# class ProductIngredientSerializer(serializers.ModelSerializer):
#     ingredient = IngredientSerializer(read_only=True)
#     ingredient_id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(), write_only=True)
#
#     class Meta:
#         model = ProductIngredient
#         fields = ["id", "ingredient", "ingredient_id", "weight_grams"]
#
#     def create(self, validated_data):
#         ingredient = validated_data.pop("ingredient_id")
#         return ProductIngredient.objects.create(ingredient=ingredient, **validated_data)
#
#
# class ProductSerializer(serializers.ModelSerializer):
#     ingredients = ProductIngredientSerializer(many=True, source="productingredient_set")
#
#     class Meta:
#         model = Product
#         fields = "__all__"
#
#     def create(self, validated_data):
#         ingredients_data = validated_data.pop("productingredient_set")
#         product = Product.objects.create(**validated_data)
#         for ingredient_data in ingredients_data:
#             ProductIngredient.objects.create(product=product, **ingredient_data)
#         return product
#
#     def update(self, instance, validated_data):
#         ingredients_data = validated_data.pop("productingredient_set", None)
#         instance = super().update(instance, validated_data)
#         if ingredients_data is not None:
#             instance.productingredient_set.all().delete()
#             for ingredient_data in ingredients_data:
#                 ProductIngredient.objects.create(product=instance, **ingredient_data)
#         return instance
#
#
# class OrderProductSerializer(serializers.ModelSerializer):
#     product = ProductSerializer(read_only=True)
#     product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), write_only=True)
#
#     class Meta:
#         model = OrderProduct
#         fields = ["id", "product", "product_id", "quantity"]
#
#     def create(self, validated_data):
#         product = validated_data.pop("product_id")
#         return OrderProduct.objects.create(product=product, **validated_data)
#
#
# class OrderSerializer(serializers.ModelSerializer):
#     products = OrderProductSerializer(many=True, source="orderproduct_set")
#     table = UserSerializer(read_only=True)
#     table_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role="table"), write_only=True)
#
#     class Meta:
#         model = Order
#         fields = "__all__"
#
#     def create(self, validated_data):
#         products_data = validated_data.pop("orderproduct_set")
#         table = validated_data.pop("table_id")
#         order = Order.objects.create(table=table, **validated_data)
#         for product_data in products_data:
#             OrderProduct.objects.create(order=order, **product_data)
#         return order
#
#     def update(self, instance, validated_data):
#         products_data = validated_data.pop("orderproduct_set", None)
#         instance = super().update(instance, validated_data)
#         if products_data is not None:
#             instance.orderproduct_set.all().delete()
#             for product_data in products_data:
#                 OrderProduct.objects.create(order=instance, **product_data)
#         return instance
#
#
# class HistorySerializer(serializers.ModelSerializer):
#     user = UserSerializer(read_only=True)
#     order = OrderSerializer(read_only=True)
#
#     class Meta:
#         model = History
#         fields = "__all__"
