// custom_meal.js

import storage from '../storage.js';
import * as utils from '../utils.js';

document.addEventListener('DOMContentLoaded', function () {
    storage.updateCartInfo();           // update common CartItems & CartPrice
    utils.updateCustomMealSummary();    // update nutrition stat
    showChosenIngredients();            // show ingredients we chose
    updateAddToOrderButton();           // turn off button if no ingredients
    loadIngredients();                  // load all ingredients

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

    fetch(`/api/get/ingredients/`)
        .then(response => response.json())
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
                            <div class="row">
                                <div class="col-8">
                                    <h5 class="card-title">${ingredient.name}</h5>
                                    <p class="card-text">${ingredient.description}</p>
                                    <p class="card-text">${ingredient.price} IDR / g</p>
                                </div>
                                <div class="col-4 d-flex align-items-center justify-content-center">
                                    <img src="${ingredient.image}" alt="${ingredient.name}" class="img-fluid" style="max-height: 100px; object-fit: cover;">
                                </div>
                            </div>
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
            utils.updateCustomMealSummary();
        })
        .catch(error => {
            console.error('Ошибка загрузки ингредиентов: ', error);
        });
}

function updateAddToOrderButton() {
    const addToOrderBtn = document.getElementById('addToOrderBtn');
    const customMealDraft = utils.getCustomMealDraft()

    addToOrderBtn.disabled = !(customMealDraft && customMealDraft.product && customMealDraft.product.ingredients.length > 0);
}

function addToOrder() {
    let customMealDraft = utils.getCustomMealDraft();

    const newCustomMeal = {
        product: {...customMealDraft.product},
        amount: customMealDraft.amount
    };

    const customMeals = storage.getCustomMeals();
    customMeals.push(newCustomMeal);
    storage.setCustomMeals(customMeals);

    storage.clearCustomMealDraft();
    utils.updateCustomMealSummary();
    storage.updateCartInfo();

    window.location.href = '/';
}

export function showChosenIngredients() {
    const customMealDraft = utils.getCustomMealDraft();
    const selectedIngredientsBody = document.getElementById('selectedIngredientsBody');
    const selectedIngredientsContainer = document.getElementById('selectedIngredientsContainer');

    if (customMealDraft && customMealDraft.product && customMealDraft.product.ingredients && customMealDraft.product.ingredients.length > 0) {
        selectedIngredientsBody.innerHTML = '';

        customMealDraft.product.ingredients.forEach(ingredient => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${ingredient.name}</td>
                <td>${ingredient.price}</td>
                <td>${utils.formatNumber(ingredient.weight_grams)}g</td>
                <td>${(ingredient.price * ingredient.weight_grams).toFixed(0)}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary edit-ingredient me-2" data-id="${ingredient.id}">Edit</button>
                    <button class="btn btn-sm btn-outline-danger remove-ingredient" data-id="${ingredient.id}">Remove</button>
                </td>
            `;
            selectedIngredientsBody.appendChild(tr);
        });

        // Add total price row
        const totalRow = document.createElement('tr');
        totalRow.innerHTML = `
            <td colspan="5" class="text-center"><strong>${customMealDraft.product.price.toFixed(0)} IDR</strong></td>
        `;
        selectedIngredientsBody.appendChild(totalRow);

        selectedIngredientsContainer.style.display = 'block';

        // Add event listeners to edit buttons
        document.querySelectorAll('.edit-ingredient').forEach(button => {
            button.addEventListener('click', function () {
                const ingredientId = this.dataset.id;
                window.location.href = `/ingredient/${ingredientId}`;
            });
        });

        // Add event listeners to remove buttons
        document.querySelectorAll('.remove-ingredient').forEach(button => {
            button.addEventListener('click', function () {
                removeIngredient(this.dataset.id);
            });
        });
    } else {
        selectedIngredientsContainer.style.display = 'none';
    }
}

function removeIngredient(ingredientId) {
    let customMealDraft = utils.getCustomMealDraft()
    utils.removeIngredient(customMealDraft, ingredientId)

    utils.recalculateCustomMealSummary(customMealDraft) // 1 - calculate new nutritions
    updateAddToOrderButton();                           // 2 - Check & Update Button
    showChosenIngredients();                            // 3 - update UI for Ingredients
    utils.updateCustomMealSummary();                    // 5 - update UI for Summary
}