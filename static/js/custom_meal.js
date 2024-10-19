// custom_meal.js

import storage from './storage.js';

document.addEventListener('DOMContentLoaded', function () {
    // Загружаем информацию о корзине и ингредиентах при загрузке страницы
    storage.updateCartInfo();
    loadIngredients();
    updateCustomMealSummary();

    // Отслеживаем изменения в селекторе сортировки
    document.getElementById('sortIngredients').addEventListener('change', function () {
        loadIngredients(this.value);  // Передаем выбранный параметр сортировки
    });

    // Добавляем обработчик для кнопки добавления заказа
    document.getElementById('addToOrderBtn').addEventListener('click', addToOrder);
});

function loadIngredients(sortBy = 'protein') {

    const validSortOptions = {
        protein: 'proteins',
        fat: 'fats',
        carbs: 'carbohydrates',
        sugar: 'sugars',
        fiber: 'fiber'
    };

    const nutrientKey = validSortOptions[sortBy] || 'proteins';

    // Выполняем запрос к серверу для получения всех ингредиентов
    fetch(`/api/ingredients/all_ingredients/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка сети при запросе ингредиентов');
            }
            return response.json();
        })
        .then(data => {
            console.log('Данные ингредиентов получены: ', data); // Отладочная информация

            // Сортируем ингредиенты по выбранному показателю
            data.sort((a, b) => {
                const aValue = a.nutritional_value[nutrientKey] || 0;
                const bValue = b.nutritional_value[nutrientKey] || 0;
                return bValue - aValue;
            });

            const ingredientList = document.getElementById('ingredientList');
            ingredientList.innerHTML = '';

            // Добавляем ингредиенты на страницу
            data.forEach(ingredient => {
                const card = document.createElement('div');
                card.className = 'col-md-4 mb-4';
                card.innerHTML = `
                    <div class="card h-100 ingredient-card" data-ingredient-id="${ingredient.id}">
                        <div class="card-body">
                            <h5 class="card-title">${ingredient.name}</h5>
                            <p class="card-text">${ingredient.description}</p>
                            <p class="card-text">Цена: ${ingredient.price} IDR / g</p>
                        </div>
                    </div>
                `;
                ingredientList.appendChild(card);
            });

            // Добавляем обработчик нажатия на карточки ингредиентов
            document.querySelectorAll('.ingredient-card').forEach(card => {
                card.addEventListener('click', function () {
                    const ingredientId = this.dataset.ingredientId;
                    window.location.href = `/ingredient/${ingredientId}`;
                });
            });
            updateCustomMealSummary();
        })
        .catch(error => {
            console.error('Ошибка загрузки ингредиентов: ', error); // Отладочная информация
        });
}

function updateCustomMealSummary() {
    const customMeals = storage.getCustomMeals();
    const lastCustomMeal = customMeals[customMeals.length - 1];

    if (lastCustomMeal && lastCustomMeal.product && lastCustomMeal.product.nutritional_value) {
        const summaryElements = {
            totalPrice: document.getElementById('totalPrice'),
            totalKcal: document.getElementById('totalKcal'),
            totalFat: document.getElementById('totalFat'),
            totalSaturatedFat: document.getElementById('totalSaturatedFat'),
            totalCarbs: document.getElementById('totalCarbs'),
            totalSugar: document.getElementById('totalSugar'),
            totalFiber: document.getElementById('totalFiber'),
            totalProtein: document.getElementById('totalProtein')
        };

        const nutritionalInfo = lastCustomMeal.product.nutritional_value;

        // Обновляем соответствие ключей
        const keyMapping = {
            totalPrice: 'price',
            totalKcal: 'calories',
            totalFat: 'fats',
            totalSaturatedFat: 'saturated_fats',
            totalCarbs: 'carbohydrates',
            totalSugar: 'sugars',
            totalFiber: 'fiber',
            totalProtein: 'proteins'
        };

        for (let key in summaryElements) {
            const nutritionalKey = keyMapping[key];
            const value = nutritionalInfo[nutritionalKey];
            if (value !== undefined && summaryElements[key]) {
                summaryElements[key].textContent = value.toFixed(2);
            } else {
                console.warn(`Missing or invalid value for ${key}`);
            }
        }

        const selectedIngredientsList = document.getElementById('selectedIngredients');
        if (selectedIngredientsList) {
            // Очищаем текущее содержимое
            selectedIngredientsList.innerHTML = '';

            // Создаем таблицу
            const table = document.createElement('table');
            table.className = 'table table-striped';

            // Создаем заголовок таблицы
            const thead = document.createElement('thead');
            thead.innerHTML = `
                <tr>
                    <th></th>
                    <th></th>
                    <th></th>
                </tr>
            `;
            table.appendChild(thead);

            // Создаем тело таблицы
            const tbody = document.createElement('tbody');
            lastCustomMeal.product.ingredients.forEach(ingredient => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${ingredient.name}</td>
                    <td>${ingredient.weight_grams}g</td>
                    <td>
                        <button class="btn btn-sm btn-outline-danger remove-ingredient" data-id="${ingredient.id}">Remove</button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
            table.appendChild(tbody);

            // Добавляем таблицу в DOM
            selectedIngredientsList.appendChild(table);

            // Добавляем обработчики событий для кнопок удаления
            document.querySelectorAll('.remove-ingredient').forEach(button => {
                button.addEventListener('click', function () {
                    removeIngredient(this.dataset.id);
                });
            });
        }
    } else {
        console.warn("No custom meal or invalid structure");
    }
}

function removeIngredient(ingredientId) {
    const customMeals = storage.getCustomMeals();
    const lastCustomMeal = customMeals[customMeals.length - 1];

    if (lastCustomMeal && lastCustomMeal.product && lastCustomMeal.product.ingredients) {
        const removedIngredientIndex = lastCustomMeal.product.ingredients.findIndex(i => i.id === parseInt(ingredientId));

        if (removedIngredientIndex !== -1) {
            const removedIngredient = lastCustomMeal.product.ingredients.splice(removedIngredientIndex, 1)[0];

            recalculateNutritionalValue(lastCustomMeal.product);
            storage.saveToLocalStorage();
            updateCustomMealSummary();

            console.log('Removed ingredient:', removedIngredient);
        }
    }
}

function recalculateNutritionalValue(product) {
    // Сбрасываем текущие значения
    product.nutritional_value = {
        calories: 0,
        proteins: 0,
        fats: 0,
        saturated_fats: 0,
        carbohydrates: 0,
        sugars: 0,
        fiber: 0,
        price: 0
    };

    // Пересчитываем на основе оставшихся ингредиентов
    product.ingredients.forEach(ingredient => {
        const factor = ingredient.weight_grams / 100; // так как nutritional_value на 100г

        product.nutritional_value.calories += ingredient.nutritional_value.calories * factor;
        product.nutritional_value.proteins += ingredient.nutritional_value.proteins * factor;
        product.nutritional_value.fats += ingredient.nutritional_value.fats * factor;
        product.nutritional_value.saturated_fats += ingredient.nutritional_value.saturated_fats * factor;
        product.nutritional_value.carbohydrates += ingredient.nutritional_value.carbohydrates * factor;
        product.nutritional_value.sugars += ingredient.nutritional_value.sugars * factor;
        product.nutritional_value.fiber += ingredient.nutritional_value.fiber * factor;
        product.nutritional_value.price += ingredient.price * ingredient.weight_grams;
    });

    // Округляем значения для удобства отображения
    for (let key in product.nutritional_value) {
        product.nutritional_value[key] = Math.round(product.nutritional_value[key] * 100) / 100;
    }
}

function addToOrder() {
    const customMeals = storage.getCustomMeals();
    const lastCustomMeal = customMeals[customMeals.length - 1];

    if (lastCustomMeal) {
        storage.addItem(lastCustomMeal.product, 1);
        storage.clearCustomMeals();
        updateCustomMealSummary();
        storage.updateCartInfo();
        alert('Custom meal added to order!');
    }
}