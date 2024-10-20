// utils.js

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
        customMeal.product.nutritional_value[key] = Math.round(customMeal.product.nutritional_value[key] * 100) / 100;
    }

    customMeal.product.price = Math.round(customMeal.product.price);
}
