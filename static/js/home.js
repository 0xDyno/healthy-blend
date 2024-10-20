// home.js

import storage from './storage.js';
import { recalculateCustomMealSummary } from './utils.js';

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
        <div class="card h-100 product-card" data-product-id="${product.id}">
            <img src="${product.image}" class="card-img-top product-image" alt="${product.name}">
            <div class="card-body">
                <h5 class="card-title">${product.name}</h5>
                <p class="card-text">${product.description}</p>
            </div>
        </div>
    `;

    productDiv.querySelector('.product-card').addEventListener('click', () => showProductDetails(product));

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
            nutritional_value: Object.fromEntries(
                Object.entries(nutritional_value).map(([key, value]) => [key, typeof value === 'number' ? value * multiplier : value])
            ),
            price: product.price * multiplier,
            weight: product.weight * multiplier
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
            nutritional_value: {},
            price: 0,
            ingredients: product.ingredients.map(ingredient => ({
                ...ingredient,
                weight_grams: Math.round(ingredient.weight_grams * multiplier)
            }))
        },
        quantity: 1
    };

    recalculateCustomMealSummary(customMealDraft);
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
        addToCart(product, 1);
        updateOrderSummary();
        modal.hide();
    });
}

function addToCart(product, quantity) {
    const customProduct = {
        ...product,
        selectedCalories: product.nutritional_value.calories,
        nutritional_value: { ...product.nutritional_value },
        price: product.price
    };

    storage.addItem(customProduct, quantity);
    updateOrderSummary();
}

function updateOrderSummary() {
    const {officialMeals, customMeals} = storage.getCartItemsSet();
    const cartItems = [...officialMeals, ...customMeals];
    const summary = cartItems.reduce((acc, item) => {
        const nutritional_value = item.product.nutritional_value;
        acc.total += item.product.price * item.quantity;

        for (let nutrient in nutritional_value) {
            if (typeof nutritional_value[nutrient] === 'number') {
                if (!acc[nutrient]) acc[nutrient] = 0;
                acc[nutrient] += nutritional_value[nutrient] * item.quantity;
            }
        }

        return acc;
    }, {total: 0});

    // Обновление отображения суммарной информации
    for (let nutrient in summary) {
        const element = document.getElementById(`total${nutrient.charAt(0).toUpperCase() + nutrient.slice(1)}`);
        if (element) {
            if (nutrient === 'total') {
                element.textContent = `${summary[nutrient].toFixed(0)} IDR`;
            } else {
                element.textContent = summary[nutrient].toFixed(1);
            }
        }
    }

    // Обновление количества товаров в корзине в навигационной панели
    const cartItemCountElement = document.getElementById('cartItemCount');
    if (cartItemCountElement) {
        cartItemCountElement.textContent = cartItems.reduce((total, item) => total + item.quantity, 0);
    }

    // Обновление общей стоимости в навигационной панели
    const cartTotalElement = document.getElementById('cartTotal');
    const cartTotalElement2 = document.getElementById('totalPrice');
    if (cartTotalElement) {
        cartTotalElement.textContent = `${summary.total.toFixed(0)} IDR`;
        cartTotalElement2.textContent = `${summary.total.toFixed(0)} IDR`;
    }
}

// Экспорт функций, если нужно использовать их в других модулях
export {addToCart, updateOrderSummary};