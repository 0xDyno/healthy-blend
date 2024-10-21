// home.js

import storage from './storage.js';
import * as utils from './utils.js';

document.addEventListener('DOMContentLoaded', function () {
    const dishesList = document.getElementById('dishesList');
    const drinksList = document.getElementById('drinksList');

    // Загрузка продуктов с сервера
    fetch('/api/products/all_products/')
        .then(response => response.json())
        .then(products => {
            products.forEach(product => {
                console.log(JSON.stringify(products))
                const productElement = createProductElement(product);
                if (product.product_type === 'dish') {
                    dishesList.appendChild(productElement);
                } else if (product.product_type === 'drink') {
                    drinksList.appendChild(productElement);
                }
            });
        });

    utils.updateOrderSummary();
});

function createProductElement(product) {
    if (product.product_type === 'drink') {
        return createDrinkElement(product);
    }
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
    if (product.product_type === 'dish') {
        const modalElement = document.getElementById('productModal');
        const modal = new bootstrap.Modal(modalElement);
        const modalBody = modalElement.querySelector('.modal-body');
        showDishDetails(product, modalBody, modal);
        modal.show();
    }
}

function createDrinkElement(product) {
    const drinkDiv = document.createElement('div');
    drinkDiv.className = 'row mb-4 drink-item';

    // Shows ALL nutrition if they > 0
    let nutrientsHtml = '';
    for (const [key, value] of Object.entries(product.nutritional_value)) {
        if (typeof value === 'number' && value !== 0) {
            const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            nutrientsHtml += `<span>${formattedKey}: ${utils.formatNumber(value)}${key === 'calories' ? '' : 'g'}</span>`;
        }
    }
    drinkDiv.innerHTML = `
        <div class="col-md-3">
            <img src="${product.image}" class="img-fluid" alt="${product.name}">
        </div>
        <div class="col-md-9">
            <h5>${product.name}</h5>
            <p>${product.description}</p>
            <div class="nutrients">
                ${nutrientsHtml}
            </div>
            <div class="mt-2">
                <span class="price">${product.price} IDR</span>
                <button class="btn btn-primary btn-sm add-to-cart" data-product-id="${product.id}">Add to Cart</button>
            </div>
        </div>
    `;

    // Shows only indicated nutrition for Drinks

    // drinkDiv.innerHTML = `
    //     <div class="col-md-3">
    //         <img src="${product.image}" class="img-fluid" alt="${product.name}">
    //     </div>
    //     <div class="col-md-9">
    //         <h5>${product.name}</h5>
    //         <p>${product.description}</p>
    //         <div class="nutrients">
    //             <span>Calories: ${product.nutritional_value.calories}</span>
    //             <span>Fat: ${product.nutritional_value.fats}g</span>
    //             <span>Carbs: ${product.nutritional_value.carbohydrates}g</span>
    //             <span>Protein: ${product.nutritional_value.proteins}g</span>
    //         </div>
    //         <div class="mt-2">
    //             <span class="price">${product.price} IDR</span>
    //             <button class="btn btn-primary btn-sm add-to-cart" data-product-id="${product.id}">Add to Cart</button>
    //         </div>
    //     </div>
    // `;

    drinkDiv.querySelector('.add-to-cart').addEventListener('click', () => addToCart(product, 1));

    return drinkDiv;
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
                    <th>Calories</th>
                    <th>Grams</th>
                    <th>Fat</th>
                    <th>Sat. Fats</th>
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
        <div class="mt-3 d-flex justify-content-end">
            <button id="editButton" class="btn btn-success me-2">Customize</button>
            <button id="addToCart" class="btn btn-primary">Add to Cart</button>
        </div>
    `;

    const nutritionalValueBody = modalBody.querySelector('#nutritional_value');
    const addToCartButton = modalBody.querySelector('#addToCart');
    const editButton = modalBody.querySelector('#editButton');

    editButton.addEventListener('click', () => {
        const selectedCalories = parseInt(modalBody.querySelector('input[name="calorieOption"]:checked').value);
        editDish(product, selectedCalories);
    });

    const nutritional_value = product.nutritional_value;
    if (nutritional_value) {
        const baseCalories = nutritional_value.calories;
        const calorieOptions = [400, 600, 800];

        calorieOptions.forEach((calories, index) => {
            const multiplier = calories / baseCalories;
            const row = nutritionalValueBody.insertRow();
            row.innerHTML = `
                <td>${calories}</td>
<!--                <td>${(product.weight * multiplier).toFixed(0)}</td>-->
                <td>${utils.formatNumber(product.weight * multiplier)}</td>
                <td>${utils.formatNumber(nutritional_value.fats * multiplier)}</td>
                <td>${utils.formatNumber(nutritional_value.saturated_fats * multiplier)}</td>
                <td>${utils.formatNumber(nutritional_value.carbohydrates * multiplier)}</td>
                <td>${utils.formatNumber(nutritional_value.sugars * multiplier)}</td>
                <td>${utils.formatNumber(nutritional_value.fiber * multiplier)}</td>
                <td>${utils.formatNumber(nutritional_value.proteins * multiplier)}</td>
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
        console.log(multiplier)
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
        utils.updateOrderSummary();
        modal.hide();
    });
}

function editDish(product, selectedCalories) {
    storage.clearCustomMealDraft();

    const baseCalories = product.nutritional_value.calories;
    const multiplier = selectedCalories / baseCalories;
    console.log()

    const customMealDraft = {
        product: {
            ...product,
            id: Date.now(),
            product_type: "custom",
            selectedCalories: 0,
            nutritional_value: {},
            price: 0,
            ingredients: product.ingredients.map(ingredient => ({
                ...ingredient,
                weight_grams: (parseFloat((ingredient.weight_grams * multiplier).toFixed(1)))
            }))
        },
        quantity: 1
    };

    utils.recalculateCustomMealSummary(customMealDraft);
    storage.setCustomMealDraft(customMealDraft);
    window.location.href = '/custom-meal/';
}

function addToCart(product, quantity) {
    const customProduct = {
        ...product,
        selectedCalories: product.nutritional_value.calories,
        nutritional_value: {...product.nutritional_value},
        price: product.price
    };

    storage.addItem(customProduct, quantity);
    utils.updateOrderSummary();
}

// Экспорт функций, если нужно использовать их в других модулях
export {addToCart};