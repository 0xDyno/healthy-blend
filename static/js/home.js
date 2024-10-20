// home.js

import storage from './storage.js';

document.addEventListener('DOMContentLoaded', function () {
    const dishesList = document.getElementById('dishesList');
    const drinksList = document.getElementById('drinksList');

    // Загрузка продуктов с сервера
    fetch('/api/products/all_products/')
        .then(response => response.json())
        .then(products => {
            products.forEach(product => {
                const productElement = createProductElement(product);
                if (product.product_type === 'dish') {
                    dishesList.appendChild(productElement);
                } else if (product.product_type === 'drink') {
                    drinksList.appendChild(productElement);
                }
            });
        });

    updateOrderSummary();
});

function createProductElement(product) {
    const productDiv = document.createElement('div');
    productDiv.className = 'col-md-4 mb-4';
    productDiv.innerHTML = `
        <div class="card">
            <img src="${product.image}" class="card-img-top" alt="${product.name}">
            <div class="card-body">
                <h5 class="card-title">${product.name}</h5>
                <p class="card-text">${product.description}</p>
                <button class="btn btn-primary view-details" data-product-id="${product.id}">View Details</button>
            </div>
        </div>
    `;

    productDiv.querySelector('.view-details').addEventListener('click', () => showProductDetails(product));

    return productDiv;
}

function showProductDetails(product) {
    const modalElement = document.getElementById('productModal');
    const modal = new bootstrap.Modal(modalElement);
    const modalBody = modalElement.querySelector('.modal-body');

    if (product.product_type === 'dish') {
        showDishDetails(product, modalBody, modal);
    } else if (product.product_type === 'drink') {
        showDrinkDetails(product, modalBody, modal);
    }

    modal.show();
}

function editMeal(product) {
    // 1. Очистить текущий customMealDraft
    storage.clearCustomMealDraft();

    // 2. Создать новый customMealDraft на основе выбранного продукта
    const customMealDraft = {
        product: {
            id: Date.now(),
            name: `Custom ${product.name}`,
            description: `Customized version of ${product.name}`,
            image: product.image,
            product_type: "custom",
            selectedCalories: product.nutritional_value.calories,
            nutritional_value: {...product.nutritional_value},
            ingredients: product.ingredients.map(ing => ({
                id: ing.id,
                name: ing.name,
                weight_grams: ing.weight_grams,
                nutritional_value: {...ing.nutritional_value},
                price: ing.price
            }))
        },
        quantity: 1
    };
    // Сохранить новый customMealDraft
    storage.setCustomMealDraft(customMealDraft);

    // 3. Перейти на страницу создания custom meal
    window.location.href = '/custom-meal/';
}

function showDishDetails(product, modalBody, modal) {
    modalBody.innerHTML = `
        <div class="row mb-3">
            <div class="col-md-8">
                <h2>${product.name}</h2>
                <p>${product.description}</p>
            </div>
            <div class="col-md-4">
                <img src="${product.image}" class="img-fluid" alt="${product.name}">
            </div>
        </div>
        <table class="table table-bordered">
            <thead>
                <tr>
                    <th>kCal</th>
                    <th>Grams</th>
                    <th>Fat</th>
                    <th>Saturated Fats</th>
                    <th>Carbs</th>
                    <th>Sugar</th>
                    <th>Fiber</th>
                    <th>Protein</th>
                    <th>Price</th>
                    <th></th>
                </tr>
            </thead>
            <tbody id="nutritional_value">
                <!-- Nutritional info will be inserted here -->
            </tbody>
        </table>
        <div class="mt-3 d-flex justify-content-between">
            <button id="addToCart" class="btn btn-primary">Add to Cart</button>
        </div>
    `;

    const nutritionalValueBody = modalBody.querySelector('#nutritional_value');
    const addToCartButton = modalBody.querySelector('#addToCart');

    const editButton = document.createElement('button');
    editButton.className = 'btn btn-success ms-2';
    editButton.textContent = 'Edit';
    editButton.addEventListener('click', () => {
        const selectedCalories = parseInt(modalBody.querySelector('input[name="calorieOption"]:checked').value);
        editDish(product, selectedCalories);
    });
    addToCartButton.parentNode.insertBefore(editButton, addToCartButton.nextSibling);

    const nutritional_value = product.nutritional_value;
    if (nutritional_value) {
        const baseCalories = nutritional_value.calories;
        const calorieOptions = [400, 600, 800];

        calorieOptions.forEach((calories, index) => {
            const multiplier = calories / baseCalories;
            const row = nutritionalValueBody.insertRow();
            row.innerHTML = `
                <td>${calories}</td>
                <td>${(product.weight * multiplier).toFixed(1)}</td>
                <td>${(nutritional_value.fats * multiplier).toFixed(1)}</td>
                <td>${(nutritional_value.saturated_fats * multiplier).toFixed(1)}</td>
                <td>${(nutritional_value.carbohydrates * multiplier).toFixed(1)}</td>
                <td>${(nutritional_value.sugars * multiplier).toFixed(1)}</td>
                <td>${(nutritional_value.fiber * multiplier).toFixed(1)}</td>
                <td>${(nutritional_value.proteins * multiplier).toFixed(1)}</td>
                <td>${(product.price * multiplier).toFixed(0)} IDR</td>
                <td>
                    <input type="radio" name="calorieOption" value="${calories}" ${index === 0 ? 'checked' : ''}>
                </td>
            `;
        });
    }

    addToCartButton.addEventListener('click', () => {
        const selectedCalories = parseInt(modalBody.querySelector('input[name="calorieOption"]:checked').value);
        const multiplier = selectedCalories / nutritional_value.calories;
        const customProduct = {
            ...product,
            selectedCalories: selectedCalories,
            nutritional_value: {
                calories: selectedCalories,
                grams: product.weight * multiplier,
                fats: nutritional_value.fats * multiplier,
                saturated_fats: nutritional_value.saturated_fats * multiplier,
                carbohydrates: nutritional_value.carbohydrates * multiplier,
                sugars: nutritional_value.sugars * multiplier,
                fiber: nutritional_value.fiber * multiplier,
                proteins: nutritional_value.proteins * multiplier,
                price: product.price * multiplier
            }
        };
        addToCart(customProduct, 1);
        updateOrderSummary();
        modal.hide();
    });
}

function editDish(product, selectedCalories) {
    storage.clearCustomMealDraft();

    const baseCalories = product.nutritional_value.calories;
    const multiplier = selectedCalories / baseCalories;

    const customMealDraft = {
        product: {
            ...product,
            id: Date.now(),
            product_type: "custom",
            selectedCalories: selectedCalories,
            nutritional_value: {
                calories: selectedCalories,
                grams: Math.round(product.weight * multiplier),
                fats: Math.round(product.nutritional_value.fats * multiplier * 10) / 10,
                saturated_fats: Math.round(product.nutritional_value.saturated_fats * multiplier * 10) / 10,
                carbohydrates: Math.round(product.nutritional_value.carbohydrates * multiplier * 10) / 10,
                sugars: Math.round(product.nutritional_value.sugars * multiplier * 10) / 10,
                fiber: Math.round(product.nutritional_value.fiber * multiplier * 10) / 10,
                proteins: Math.round(product.nutritional_value.proteins * multiplier * 10) / 10,
                price: Math.round(product.price * multiplier)
            },
            ingredients: product.ingredients.map(ingredient => ({
                ...ingredient,
                weight_grams: Math.round(ingredient.weight_grams * multiplier)
            }))
        },
        quantity: 1
    };

    storage.setCustomMealDraft(customMealDraft);
    window.location.href = '/custom-meal/';
}


function showDrinkDetails(product, modalBody, modal) {
    modalBody.innerHTML = `
        <div class="row mb-3">
            <div class="col-md-8">
                <h2>${product.name}</h2>
                <p>${product.description}</p>
            </div>
            <div class="col-md-4">
                <img src="${product.image}" class="img-fluid" alt="${product.name}">
            </div>
        </div>
        <table class="table table-bordered">
            <thead>
                <tr>
                    <th>kCal</th>
                    <th>Fat</th>
                    <th>Saturated Fats</th>
                    <th>Carbs</th>
                    <th>Sugar</th>
                    <th>Fiber</th>
                    <th>Protein</th>
                    <th>Price</th>
                </tr>
            </thead>
            <tbody id="nutritional_value">
                <tr>
                    <td>${product.nutritional_value.calories}</td>
                    <td>${product.nutritional_value.fats}</td>
                    <td>${product.nutritional_value.saturated_fats}</td>
                    <td>${product.nutritional_value.carbohydrates}</td>
                    <td>${product.nutritional_value.sugars}</td>
                    <td>${product.nutritional_value.fiber}</td>
                    <td>${product.nutritional_value.proteins}</td>
                    <td>${product.price} IDR</td>
                </tr>
            </tbody>
        </table>
        <div class="mt-3">
            <button id="addToCart" class="btn btn-primary">Add to Cart</button>
        </div>
    `;

    const addToCartButton = modalBody.querySelector('#addToCart');

    addToCartButton.addEventListener('click', () => {
        const drinkProduct = {
            ...product,
            nutritional_value: {
                calories: product.nutritional_value.calories,
                fats: product.nutritional_value.fats,
                saturated_fats: product.nutritional_value.saturated_fats,
                carbohydrates: product.nutritional_value.carbohydrates,
                sugars: product.nutritional_value.sugars,
                fiber: product.nutritional_value.fiber,
                proteins: product.nutritional_value.proteins,
                price: product.price
            }
        };
        addToCart(drinkProduct, 1);
        updateOrderSummary();
        modal.hide();
    });
}

function addToCart(product, quantity) {
    storage.addItem(product, quantity);
    updateOrderSummary();
}

function updateOrderSummary() {
    const {officialMeals, customMeals} = storage.getCartItemsSet();
    const cartItems = [...officialMeals, ...customMeals];
    const summary = cartItems.reduce((acc, item) => {
        const nutritional_value = item.product.nutritional_value;
        acc.total += nutritional_value.price * item.quantity;
        acc.kcal += nutritional_value.calories * item.quantity;
        acc.fat += nutritional_value.fats * item.quantity;
        acc.saturatedFat += nutritional_value.saturated_fats * item.quantity;
        acc.carbs += nutritional_value.carbohydrates * item.quantity;
        acc.sugar += nutritional_value.sugars * item.quantity;
        acc.fiber += nutritional_value.fiber * item.quantity;
        acc.protein += nutritional_value.proteins * item.quantity;
        return acc;
    }, {total: 0, kcal: 0, fat: 0, saturatedFat: 0, carbs: 0, sugar: 0, fiber: 0, protein: 0});

    document.getElementById('totalPrice').textContent = summary.total.toFixed(0);
    document.getElementById('totalKcal').textContent = summary.kcal.toFixed(0);
    document.getElementById('totalFat').textContent = summary.fat.toFixed(1);
    document.getElementById('totalSaturatedFat').textContent = summary.saturatedFat.toFixed(1);
    document.getElementById('totalCarbs').textContent = summary.carbs.toFixed(1);
    document.getElementById('totalSugar').textContent = summary.sugar.toFixed(1);
    document.getElementById('totalFiber').textContent = summary.fiber.toFixed(1);
    document.getElementById('totalProtein').textContent = summary.protein.toFixed(1);

    // Обновление количества товаров в корзине в навигационной панели
    const cartItemCountElement = document.getElementById('cartItemCount');
    if (cartItemCountElement) {
        cartItemCountElement.textContent = cartItems.reduce((total, item) => total + item.quantity, 0);
    }

    // Обновление общей стоимости в навигационной панели
    const cartTotalElement = document.getElementById('cartTotal');
    if (cartTotalElement) {
        cartTotalElement.textContent = `${storage.getTotalPrice().toFixed(0)} IDR`;
    }
}

// Экспорт функций, если нужно использовать их в других модулях
export {addToCart, updateOrderSummary};