# Generated by Django 5.1.2 on 2024-10-29 07:45

import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='DaySetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.IntegerField(choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')], unique=True)),
                ('is_open', models.BooleanField(default=True)),
                ('open_hours', models.TimeField(blank=True, null=True)),
                ('close_hours', models.TimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='NutritionalValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('calories', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('proteins', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('fats', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('saturated_fats', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('carbohydrates', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('sugars', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('fiber', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('vitamin_a', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('vitamin_c', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('vitamin_d', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('vitamin_e', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('vitamin_k', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('thiamin', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('riboflavin', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('niacin', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('vitamin_b6', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('folate', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('vitamin_b12', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('calcium', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('iron', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('magnesium', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('phosphorus', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('potassium', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('sodium', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('zinc', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('copper', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('manganese', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('selenium', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
            ],
        ),
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service', models.FloatField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('tax', models.FloatField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('can_order', models.BooleanField(default=True)),
                ('close_kitchen_before', models.IntegerField(default=20, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(120)])),
                ('minimum_order_amount', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('maximum_order_amount', models.IntegerField(default=3000000, validators=[django.core.validators.MinValueValidator(0)])),
                ('maximum_order_weight', models.IntegerField(default=5000, validators=[django.core.validators.MinValueValidator(0)])),
                ('minimum_blend_weight', models.IntegerField(default=100, validators=[django.core.validators.MinValueValidator(0)])),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('nickname', models.CharField(blank=True, default='', max_length=50)),
                ('role', models.CharField(choices=[('owner', 'Owner'), ('administrator', 'Administrator'), ('manager', 'Manager'), ('table', 'Table'), ('kitchen', 'Kitchen'), ('user', 'User')], default='user', max_length=15)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('image', models.ImageField(upload_to='ingredients/')),
                ('ingredient_type', models.CharField(choices=[('base', 'Base'), ('protein', 'Protein'), ('vegetable', 'Vegetable'), ('dairy', 'Dairy'), ('fruit', 'Fruit'), ('topping', 'Topping'), ('other', 'Other')], default='other', max_length=10)),
                ('step', models.FloatField(default=1, validators=[django.core.validators.MinValueValidator(0.05), django.core.validators.MaxValueValidator(5)])),
                ('min_order', models.IntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(50)])),
                ('max_order', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(500)])),
                ('is_available', models.BooleanField(default=True)),
                ('price_per_gram', models.IntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(999)])),
                ('price_multiplier', models.FloatField(default=3.0, validators=[django.core.validators.MinValueValidator(0)])),
                ('custom_price', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('nutritional_value', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='ingredient', to='core.nutritionalvalue')),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_status', models.CharField(choices=[('pending', 'Pending'), ('cooking', 'Cooking'), ('ready', 'Ready'), ('finished', 'Finished'), ('cancelled', 'Cancelled'), ('problem', 'Problem')], default='pending', max_length=20)),
                ('order_type', models.CharField(choices=[('offline', 'Offline'), ('takeaway', 'Take Away'), ('online', 'Online')], default='offline', max_length=20)),
                ('payment_type', models.CharField(choices=[('cash', 'Cash'), ('card', 'Card'), ('qr', 'QR')], default='card', max_length=20)),
                ('tax', models.IntegerField(default=7, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(15)])),
                ('service', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)])),
                ('base_price', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('total_price', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('payment_id', models.CharField(blank=True, max_length=100)),
                ('is_paid', models.BooleanField(default=False)),
                ('is_refunded', models.BooleanField(default=False)),
                ('public_note', models.TextField(blank=True, max_length=500, null=True, validators=[django.core.validators.MaxLengthValidator(1000)])),
                ('private_note', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('ready_at', models.DateTimeField(blank=True, null=True)),
                ('refunded_at', models.DateTimeField(blank=True, null=True)),
                ('show_public', models.BooleanField(default=True)),
                ('nutritional_value', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='order', to='core.nutritionalvalue')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='first_order', to=settings.AUTH_USER_MODEL)),
                ('user_last_update', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='last_update', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OrderHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_deleted_id', models.IntegerField(blank=True, null=True)),
                ('order_status', models.CharField(choices=[('pending', 'Pending'), ('cooking', 'Cooking'), ('ready', 'Ready'), ('finished', 'Finished'), ('cancelled', 'Cancelled'), ('problem', 'Problem')], max_length=20)),
                ('order_type', models.CharField(choices=[('offline', 'Offline'), ('takeaway', 'Take Away'), ('online', 'Online')], max_length=20)),
                ('payment_type', models.CharField(choices=[('cash', 'Cash'), ('card', 'Card'), ('qr', 'QR')], max_length=20)),
                ('tax', models.IntegerField()),
                ('service', models.IntegerField()),
                ('base_price', models.IntegerField()),
                ('total_price', models.IntegerField()),
                ('payment_id', models.CharField(blank=True, max_length=100)),
                ('is_paid', models.BooleanField(default=False)),
                ('is_refunded', models.BooleanField(default=False)),
                ('public_note', models.TextField(blank=True, max_length=500, null=True)),
                ('private_note', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='history', to='core.order')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_history_user', to=settings.AUTH_USER_MODEL)),
                ('user_last_update', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_history_last_update', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_type', models.CharField(choices=[('dish', 'Dish'), ('drink', 'Drink')], default='dish', max_length=10)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='products/')),
                ('is_menu', models.BooleanField(default=False)),
                ('is_official', models.BooleanField()),
                ('is_available', models.BooleanField(default=False)),
                ('price', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('price_multiplier', models.FloatField(default=3.0, validators=[django.core.validators.MinValueValidator(0)])),
                ('custom_price', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('weight', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('nutritional_value', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='product', to='core.nutritionalvalue')),
            ],
        ),
        migrations.CreateModel(
            name='OrderProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ('price', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('do_blend', models.BooleanField(default=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='core.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.product')),
            ],
        ),
        migrations.CreateModel(
            name='ProductIngredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight_grams', models.FloatField(validators=[django.core.validators.MinValueValidator(0)])),
                ('ingredient', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.ingredient')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.product')),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='ingredients',
            field=models.ManyToManyField(through='core.ProductIngredient', to='core.ingredient'),
        ),
        migrations.CreateModel(
            name='Promo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('discount', models.FloatField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(0.5)])),
                ('promo_code', models.CharField(max_length=20, unique=True)),
                ('active_from', models.DateTimeField()),
                ('active_until', models.DateTimeField()),
                ('usage_limit', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('used_count', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='creator', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PromoUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('discounted', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('used_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_for_order', to='core.order')),
                ('promo', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='used_promo', to='core.promo')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='used_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['order_status'], name='core_order_order_s_945ce3_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['order_type'], name='core_order_order_t_34e487_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['payment_type'], name='core_order_payment_36ea40_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['is_paid'], name='core_order_is_paid_376863_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['is_refunded'], name='core_order_is_refu_a8c703_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['created_at'], name='core_order_created_912d27_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['user_id'], name='core_order_user_id_f84106_idx'),
        ),
    ]
