// custom_add.js

import storage from './storage.js';

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
        updateDynamicData(this.value);
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
        kcal: document.getElementById('dynamicKcal'),
        fat: document.getElementById('dynamicFat'),
        saturatedFat: document.getElementById('dynamicSaturatedFat'),
        carbs: document.getElementById('dynamicCarbs'),
        sugar: document.getElementById('dynamicSugar'),
        fiber: document.getElementById('dynamicFiber'),
        protein: document.getElementById('dynamicProtein')
    };

    dynamicElements.total.textContent = (ingredientData.price * amount).toFixed(2);
    dynamicElements.kcal.textContent = (ingredientData.nutritional_value.calories * factor).toFixed(0);
    dynamicElements.fat.textContent = (ingredientData.nutritional_value.fats * factor).toFixed(1);
    dynamicElements.saturatedFat.textContent = (ingredientData.nutritional_value.saturated_fats * factor).toFixed(1);
    dynamicElements.carbs.textContent = (ingredientData.nutritional_value.carbohydrates * factor).toFixed(1);
    dynamicElements.sugar.textContent = (ingredientData.nutritional_value.sugars * factor).toFixed(1);
    dynamicElements.fiber.textContent = (ingredientData.nutritional_value.fiber * factor).toFixed(1);
    dynamicElements.protein.textContent = (ingredientData.nutritional_value.proteins * factor).toFixed(1);
}

function updateCustomMealSummary() {
    const customMealDraft = storage.getCustomMealDraft();

    if (customMealDraft && customMealDraft.product && customMealDraft.product.nutritional_value) {
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

        const nutritional_value = customMealDraft.product.nutritional_value;

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
            const value = nutritional_value[nutritionalKey];
            if (value !== undefined && summaryElements[key]) {
                summaryElements[key].textContent = value.toFixed(2);
            } else {
                console.warn(`Missing or invalid value for ${key}`);
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
    // Изменяем эту функцию для работы с customMealDraft
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
                nutritional_value: {
                    calories: 0,
                    grams: 0,
                    fats: 0,
                    saturated_fats: 0,
                    carbohydrates: 0,
                    sugars: 0,
                    fiber: 0,
                    proteins: 0,
                    price: 0
                },
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

function recalculateCustomMealSummary(customMeal) {
    customMeal.product.nutritional_value = customMeal.product.ingredients.reduce((sum, ingredient) => {
        const factor = ingredient.weight_grams / 100;

        sum.calories += ingredient.nutritional_value.calories * factor;
        sum.grams += ingredient.weight_grams;
        sum.fats += ingredient.nutritional_value.fats * factor;
        sum.saturated_fats += ingredient.nutritional_value.saturated_fats * factor;
        sum.carbohydrates += ingredient.nutritional_value.carbohydrates * factor;
        sum.sugars += ingredient.nutritional_value.sugars * factor;
        sum.fiber += ingredient.nutritional_value.fiber * factor;
        sum.proteins += ingredient.nutritional_value.proteins * factor;
        sum.price += ingredient.price * ingredient.weight_grams;
        return sum;
    }, {
        calories: 0,
        grams: 0,
        fats: 0,
        saturated_fats: 0,
        carbohydrates: 0,
        sugars: 0,
        fiber: 0,
        proteins: 0,
        price: 0
    });
}