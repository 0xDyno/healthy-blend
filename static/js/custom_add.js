// custom_add.js

import storage from './storage.js';
import * as utils from './utils.js';

let ingredientData;

document.addEventListener('DOMContentLoaded', function () {
    storage.updateCartInfo();

    fetch(`/api/ingredients/${ingredientId}/get_ingredient/`)
        .then(response => response.json())
        .then(data => {
            ingredientData = data;
            updateIngredientInfo();
            initializeForm();
            utils.updateCustomMealSummary();
        })
        .catch(error => console.error('Error:', error));
});

function updateIngredientInfo() {
    document.getElementById('ingredientName').textContent = ingredientData.name;
    document.getElementById('ingredientDescription').textContent = ingredientData.description;
    document.getElementById('ingredientPrice').textContent = ingredientData.price;
    document.getElementById('ingredientImage').src = ingredientData.image;
}

function initializeForm() {
    const amountSlider = document.getElementById('ingredientAmount');
    const amountOutput = document.getElementById('amountOutput');

    amountSlider.min = ingredientData.min_order;
    amountSlider.max = ingredientData.max_order;

    const existingWeight = checkIngredientInDraft(ingredientData.id);
    if (existingWeight) {
        amountSlider.value = existingWeight;
        amountOutput.textContent = existingWeight;
    } else {
        amountSlider.value = ingredientData.min_order;
        amountOutput.textContent = ingredientData.min_order;
    }

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
    updateTotalNutrition(amount);
}

function updateTotalNutrition(amount) {
    const factor = amount / 100;
    const totalNutrition = {...utils.getCustomMealDraft().product.nutritional_value};

    for (let key in totalNutrition) {
        if (ingredientData.nutritional_value[key] !== undefined) {
            totalNutrition[key] += ingredientData.nutritional_value[key] * factor;
        }
    }
    utils.updateNutritionSummary(totalNutrition);
}


function addIngredientToCustomMeal(amount) {
    let customMealDraft = utils.getCustomMealDraft()

    if (amount > ingredientData.max_order) {
        alert(`Amount can't be bigger than ${ingredientData.max_order} grams.`);
        return;
    }

    if (amount <= 0) {
        utils.removeIngredient(customMealDraft, ingredientId)
    } else {
        const existingIngredient = customMealDraft.product.ingredients.find(ing => ing.id === ingredientData.id);

        if (existingIngredient) {
            existingIngredient.weight_grams = amount;
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
    }
    utils.recalculateCustomMealSummary(customMealDraft);
    storage.updateCartInfo();
}

function checkIngredientInDraft(ingredientId) {
    let customMealDraft = utils.getCustomMealDraft();

    if (!customMealDraft.product.ingredients || customMealDraft.product.ingredients.length === 0) {
        return false;
    }

    const existingIngredient = customMealDraft.product.ingredients.find(ing => ing.id === ingredientId);

    return existingIngredient ? existingIngredient.weight_grams : false;
}