// custom_meal.js

import storage from './storage.js';

document.addEventListener('DOMContentLoaded', function () {
    storage.updateCartInfo();
    loadIngredients();
    updateCustomMealSummary();
    updateAddToOrderButton();

    document.getElementById('sortIngredients').addEventListener('change', function () {
        loadIngredients(this.value);
    });

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

    fetch(`/api/ingredients/all_ingredients/`)
        .then(response => {
            return response.json();
        })
        .then(data => {

            data.sort((a, b) => {
                const aValue = a.nutritional_value[nutrientKey] || 0;
                const bValue = b.nutritional_value[nutrientKey] || 0;
                return bValue - aValue;
            });

            const ingredientList = document.getElementById('ingredientList');
            ingredientList.innerHTML = '';

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
    const customMealDraft = storage.getCustomMealDraft();

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

    const selectedIngredientsList = document.getElementById('selectedIngredients');

    if (customMealDraft && customMealDraft.product && customMealDraft.product.nutritional_value) {
        const nutritionalInfo = customMealDraft.product.nutritional_value;

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

        if (selectedIngredientsList) {
            selectedIngredientsList.innerHTML = '';

            const table = document.createElement('table');
            table.className = 'table table-striped';

            const thead = document.createElement('thead');
            thead.innerHTML = `
                <tr>
                    <th>Ingredient</th>
                    <th>Weight</th>
                    <th>Action</th>
                </tr>
            `;
            table.appendChild(thead);

            const tbody = document.createElement('tbody');
            customMealDraft.product.ingredients.forEach(ingredient => {
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

            selectedIngredientsList.appendChild(table);

            document.querySelectorAll('.remove-ingredient').forEach(button => {
                button.addEventListener('click', function () {
                    removeIngredient(this.dataset.id);
                });
            });
        }
    } else {
        for (let key in summaryElements) {
            if (summaryElements[key]) {
                summaryElements[key].textContent = '0';
            }
        }
        if (selectedIngredientsList) {
            selectedIngredientsList.innerHTML = '';
        }
    }
    updateAddToOrderButton();
}

function updateAddToOrderButton() {
    const addToOrderBtn = document.getElementById('addToOrderBtn');
    const customMealDraft = storage.getCustomMealDraft();

    addToOrderBtn.disabled = !(customMealDraft && customMealDraft.product && customMealDraft.product.ingredients.length > 0);
}


function removeIngredient(ingredientId) {
    const customMealDraft = storage.getCustomMealDraft();

    if (customMealDraft && customMealDraft.product && customMealDraft.product.ingredients) {
        const removedIngredientIndex = customMealDraft.product.ingredients.findIndex(i => i.id === parseInt(ingredientId));

        if (removedIngredientIndex !== -1) {
            const removedIngredient = customMealDraft.product.ingredients.splice(removedIngredientIndex, 1)[0];

            recalculateNutritionalValue(customMealDraft.product);
            storage.setCustomMealDraft(customMealDraft);
            updateCustomMealSummary();
        }
    }
}

function recalculateNutritionalValue(product) {
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

    product.ingredients.forEach(ingredient => {
        const factor = ingredient.weight_grams / 100;

        product.nutritional_value.calories += ingredient.nutritional_value.calories * factor;
        product.nutritional_value.proteins += ingredient.nutritional_value.proteins * factor;
        product.nutritional_value.fats += ingredient.nutritional_value.fats * factor;
        product.nutritional_value.saturated_fats += ingredient.nutritional_value.saturated_fats * factor;
        product.nutritional_value.carbohydrates += ingredient.nutritional_value.carbohydrates * factor;
        product.nutritional_value.sugars += ingredient.nutritional_value.sugars * factor;
        product.nutritional_value.fiber += ingredient.nutritional_value.fiber * factor;
        product.nutritional_value.price += ingredient.price * ingredient.weight_grams;
    });

    for (let key in product.nutritional_value) {
        product.nutritional_value[key] = Math.round(product.nutritional_value[key] * 100) / 100;
    }
}

function addToOrder() {
    const customMealDraft = storage.getCustomMealDraft();

    if (customMealDraft) {

        const newCustomMeal = {
            product: {...customMealDraft.product},
            quantity: customMealDraft.quantity // Устанавливаем начальное количество
        };

        const customMeals = storage.getCustomMeals();
        customMeals.push(newCustomMeal);
        storage.setCustomMeals(customMeals);

        storage.clearCustomMealDraft();
        updateCustomMealSummary();
        storage.updateCartInfo();

        window.location.href = '/';
    } else {
        alert('No custom meal to add to order!');
    }
}