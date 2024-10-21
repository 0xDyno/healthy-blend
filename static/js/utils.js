// utils.js

import storage from './storage.js';

export function formatNumber(number) {
    return Number.isInteger(number) ? number.toString() : number.toFixed(1);
}

export function updateNutritionSummary(summary) {
    document.getElementById('nutritionSummaryCalories').textContent = formatNumber(summary.calories);
    document.getElementById('nutritionSummaryFats').textContent = formatNumber(summary.fats);
    document.getElementById('nutritionSummarySaturatedFats').textContent = formatNumber(summary.saturated_fats);
    document.getElementById('nutritionSummaryCarbohydrates').textContent = formatNumber(summary.carbohydrates);
    document.getElementById('nutritionSummarySugars').textContent = formatNumber(summary.sugars);
    document.getElementById('nutritionSummaryFiber').textContent = formatNumber(summary.fiber);
    document.getElementById('nutritionSummaryProteins').textContent = formatNumber(summary.proteins);
}

export function calculateNutritionSummary(items) {
    return items.reduce((acc, item) => {
        const nutritionalInfo = item.product.nutritional_value;
        const quantity = item.quantity;
        acc.total += item.product.price * quantity;
        acc.calories += nutritionalInfo.calories * quantity;
        acc.fats += nutritionalInfo.fats * quantity;
        acc.saturated_fats += nutritionalInfo.saturated_fats * quantity;
        acc.carbohydrates += nutritionalInfo.carbohydrates * quantity;
        acc.sugars += nutritionalInfo.sugars * quantity;
        acc.fiber += nutritionalInfo.fiber * quantity;
        acc.proteins += nutritionalInfo.proteins * quantity;
        return acc;
    }, {total: 0, calories: 0, fats: 0, saturated_fats: 0, carbohydrates: 0, sugars: 0, fiber: 0, proteins: 0});
}

export function updateOrderSummary() {
    const {officialMeals, customMeals} = storage.getCartItemsSet();
    const allItems = [...officialMeals, ...customMeals];
    const summary = calculateNutritionSummary(allItems);
    updateNutritionSummary(summary);

    // Update cart info in navbar
    const cartItemCountElement = document.getElementById('cartItemCount');
    const cartTotalElement = document.getElementById('cartTotal');
    if (cartItemCountElement && cartTotalElement) {
        cartItemCountElement.textContent = allItems.reduce((total, item) => total + item.quantity, 0);
        cartTotalElement.textContent = `${summary.total.toFixed(0)} IDR`;
    }
}

///////////////////////////
// custom_meal & custom_add
///////////////////////////

export function getCustomMealDraft(give_new = false) {
    let customMealDraft = storage.getCustomMealDraft();

    if (!customMealDraft || give_new) {
        customMealDraft = {
            product: {
                id: Date.now(),
                name: "Custom Meal",
                description: "Custom created meal",
                image: "",
                product_type: "custom",
                selectedCalories: 0,
                nutritional_value: init_nutritional_value(),
                price: 0,
                ingredients: []
            },
            quantity: 1
        };
    }
    return customMealDraft;
}

export function recalculateCustomMealSummary(customMeal) {
    customMeal.product.nutritional_value = {};
    customMeal.product.price = 0;

    customMeal.product.ingredients.forEach(ingredient => {
        const factor = ingredient.weight_grams / 100;

        for (let key in ingredient.nutritional_value) {
            if (customMeal.product.nutritional_value[key] === undefined) {
                customMeal.product.nutritional_value[key] = 0;
            }
            customMeal.product.nutritional_value[key] += ingredient.nutritional_value[key] * factor;
        }

        customMeal.product.price += ingredient.price * ingredient.weight_grams;
    });

    for (let key in customMeal.product.nutritional_value) {
        customMeal.product.nutritional_value[key] = parseFloat(customMeal.product.nutritional_value[key].toFixed(2));
    }

    customMeal.product.price = parseFloat(customMeal.product.price.toFixed(2));
    storage.setCustomMealDraft(customMeal);
}

export function updateCustomMealSummary() {
    const customMealDraft = getCustomMealDraft();
    if (customMealDraft && customMealDraft.product.ingredients.length > 0) {
        const summary = calculateNutritionSummary([customMealDraft]);
        updateNutritionSummary(summary);
    } else {
        updateNutritionSummary({calories: 0, fats: 0, saturated_fats: 0, carbohydrates: 0, sugars: 0, fiber: 0, proteins: 0});
    }
}

export function removeIngredient(mealStorage, ingredientId) {
    if (mealStorage && mealStorage.product && mealStorage.product.ingredients) {
        const removedIngredientIndex = mealStorage.product.ingredients.findIndex(i => i.id === parseInt(ingredientId));

        if (removedIngredientIndex !== -1) {
            mealStorage.product.ingredients.splice(removedIngredientIndex, 1);
            return true;
        }
    }
    return false;
}

function init_nutritional_value() {
    return {
        "calories": 0,
        "proteins": 0,
        "fats": 0,
        "saturated_fats": 0,
        "carbohydrates": 0,
        "sugars": 0,
        "fiber": 0,
        "vitamin_a": 0,
        "vitamin_c": 0,
        "vitamin_d": 0,
        "vitamin_e": 0,
        "vitamin_k": 0,
        "thiamin": 0,
        "riboflavin": 0,
        "niacin": 0,
        "vitamin_b6": 0,
        "folate": 0,
        "vitamin_b12": 0,
        "calcium": 0,
        "iron": 0,
        "magnesium": 0,
        "phosphorus": 0,
        "potassium": 0,
        "sodium": 0,
        "zinc": 0,
        "copper": 0,
        "manganese": 0,
        "selenium": 0,
    }
}