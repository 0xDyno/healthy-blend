// custom_add.js

import storage from './storage.js';
import { recalculateCustomMealSummary } from './utils.js';

let ingredientData;

document.addEventListener('DOMContentLoaded', function () {
    storage.updateCartInfo();

    fetch(`/api/ingredients/${ingredientId}/get_ingredient/`)
        .then(response => response.json())
        .then(data => {
            ingredientData = data;
            updateIngredientInfo();
            initializeForm();
            updateCustomMealSummary();
        })
        .catch(error => console.error('Error:', error));
});

function updateIngredientInfo() {
    document.getElementById('ingredientName').textContent = ingredientData.name;
    document.getElementById('ingredientDescription').textContent = ingredientData.description;
    document.getElementById('ingredientPrice').textContent = ingredientData.price;
}

function initializeForm() {
    const amountSlider = document.getElementById('ingredientAmount');
    const amountOutput = document.getElementById('amountOutput');

    amountSlider.min = ingredientData.min_order;
    amountSlider.max = ingredientData.max_order;
    amountSlider.value = ingredientData.min_order;
    amountOutput.textContent = ingredientData.min_order;

    amountSlider.addEventListener('input', function () {
        amountOutput.textContent = this.value;
        updateDynamicData(parseInt(this.value));
    });

    document.getElementById('addIngredientForm').addEventListener('submit', function (e) {
        e.preventDefault();
        const amount = parseInt(amountSlider.value);
        addIngredientToCustomMeal(amount);
        window.location.href = '/custom-meal/';
    });

    updateDynamicData(amountSlider.value);
}

function updateDynamicData(amount) {
    const factor = amount / 100;
    const dynamicElements = {
        total: document.getElementById('dynamicTotal'),
        calories: document.getElementById('dynamicCalories'),
        fats: document.getElementById('dynamicFats'),
        saturated_fats: document.getElementById('dynamicSaturated_fats'),
        carbohydrates: document.getElementById('dynamicCarbohydrates'),
        sugars: document.getElementById('dynamicSugars'),
        fiber: document.getElementById('dynamicFiber'),
        proteins: document.getElementById('dynamicProteins')
    };

    dynamicElements.total.textContent = (ingredientData.price * amount).toFixed(2);

    for (let key in dynamicElements) {
        if (key !== 'total' && ingredientData.nutritional_value[key] !== undefined) {
            dynamicElements[key].textContent = (ingredientData.nutritional_value[key] * factor).toFixed(1);
        }
    }
}

function updateCustomMealSummary() {
    const customMealDraft = storage.getCustomMealDraft();

    if (customMealDraft && customMealDraft.product && customMealDraft.product.nutritional_value) {
        const summaryElements = {
            totalPrice: document.getElementById('totalPrice'),
            calories: document.getElementById('totalKcal'),
            fats: document.getElementById('totalFat'),
            saturated_fats: document.getElementById('totalSaturatedFat'),
            carbohydrates: document.getElementById('totalCarbs'),
            sugars: document.getElementById('totalSugar'),
            fiber: document.getElementById('totalFiber'),
            proteins: document.getElementById('totalProtein')
        };

        const nutritional_value = customMealDraft.product.nutritional_value;

        for (let key in summaryElements) {
            if (key === 'totalPrice') {
                summaryElements[key].textContent = customMealDraft.product.price.toFixed(2);
            } else if (nutritional_value[key] !== undefined && summaryElements[key]) {
                summaryElements[key].textContent = nutritional_value[key].toFixed(2);
            }
        }

        const selectedIngredientsList = document.getElementById('selectedIngredients');
        if (selectedIngredientsList) {
            selectedIngredientsList.innerHTML = '';
            customMealDraft.product.ingredients.forEach(ingredient => {
                const li = document.createElement('li');
                li.textContent = `${ingredient.name}: ${ingredient.weight_grams}g`;
                selectedIngredientsList.appendChild(li);
            });
        }
    } else {
        console.warn("No custom meal draft or invalid structure");
    }
}

function addIngredientToCustomMeal(amount) {
    let customMealDraft = storage.getCustomMealDraft();

    if (!customMealDraft) {
        customMealDraft = {
            product: {
                id: Date.now(),
                name: "Custom Meal",
                description: "Custom created meal",
                image: "",
                product_type: "custom",
                selectedCalories: 0,
                nutritional_value: {},
                price: 0,
                ingredients: []
            },
            quantity: 1
        };
    }

    const existingIngredient = customMealDraft.product.ingredients.find(ing => ing.id === ingredientData.id);

    if (existingIngredient) {
        existingIngredient.weight_grams += amount;
    } else {
        const newIngredient = {
            id: ingredientData.id,
            name: ingredientData.name,
            weight_grams: amount,
            nutritional_value: {...ingredientData.nutritional_value},
            price: ingredientData.price
        };
        customMealDraft.product.ingredients.push(newIngredient);
    }

    recalculateCustomMealSummary(customMealDraft);
    storage.setCustomMealDraft(customMealDraft);
    storage.updateCartInfo();
}