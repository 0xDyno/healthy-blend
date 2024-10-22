// cart.js

import storage from './storage.js';
import * as utils from './utils.js';

document.addEventListener('DOMContentLoaded', function () {
    updateCartUI();
    utils.updateOrderSummary();

    document.getElementById('checkoutButton').addEventListener('click', handleCheckout);
});

function updateCartUI() {
    const cartItemsContainer = document.getElementById('cartItems');
    const cartTotalElement = document.getElementById('cartTotalRes');

    cartItemsContainer.innerHTML = '';
    let total = 0;

    const {officialMeals, customMeals} = storage.getCartItemsSet();

    if (officialMeals.length === 0 && customMeals.length === 0) {
        cartTotalElement.textContent = ``;
        cartItemsContainer.innerHTML = '<p>Your cart is empty.</p>';
    } else {
        const table = document.createElement('table');
        table.className = 'table';
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Calories</th>
                    <th>Amount</th>
                    <th>Price</th>
                    <th>Total</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="cartTableBody"></tbody>
        `;
        cartItemsContainer.appendChild(table);

        const tableBody = document.getElementById('cartTableBody');

        officialMeals.forEach((item, index) => {
            const row = createTableRow(item, index, 'official');
            tableBody.appendChild(row);
            total += item.product.price * item.amount;
        });

        customMeals.forEach((item, index) => {
            const row = createTableRow(item, index, 'custom');
            tableBody.appendChild(row);
            total += item.product.price * item.amount;
        });

        addRemoveEventListeners();
        cartTotalElement.textContent = `Total: ${total.toFixed(0)} IDR`;
    }
    updateCartControls();
}

function createTableRow(item, index, type) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>
            ${item.product.name}
            ${type === 'custom' ? createIngredientsList(item.product.ingredients) : ''}
        </td>
        <td>${(item.product.nutritional_value.calories).toFixed(0)}</td>
        <td>${item.amount}</td>
        <td>${item.product.price.toFixed(0)} IDR</td>
        <td>${(item.product.price * item.amount).toFixed(0)} IDR</td>
        <td><button class="btn btn-sm btn-danger remove-from-cart" data-type="${type}" data-id="${item.product.id}" 
        data-calories="${item.product.nutritional_value.calories}">Remove</button></td>
    `;
    return row;
}

function createIngredientsList(ingredients) {
    if (!ingredients || ingredients.length === 0) return '';

    const ingredientsList = ingredients.map(ing => `<li>${ing.name}, ${utils.formatNumber(ing.weight_grams)}g</li>`).join('');
    return `
        <small class="d-block mt-1">
            Ingredients:
            <ul class="list-unstyled ml-3 mb-0">
                ${ingredientsList}
            </ul>
        </small>
    `;
}

function addRemoveEventListeners() {
    document.querySelectorAll('.remove-from-cart').forEach(button => {
        button.addEventListener('click', function () {
            const type = this.getAttribute('data-type');
            const id = this.getAttribute('data-id');
            const calories = this.getAttribute('data-calories');
            storage.removeItem(id, calories, type === 'custom');
            utils.updateOrderSummary();
            updateCartUI();
        });
    });
}

function handleCheckout() {
    const paymentType = document.getElementById('paymentType').value;

    if (!paymentType) {
        alert('Please select a payment type');
        return;
    }

    const {officialMeals, customMeals} = storage.getCartItemsSet();
    const totalPrice = storage.getTotalPrice();

    const cartData = {
        price: totalPrice,
        payment_type: paymentType,
        officialMeals: officialMeals.map(item => ({
            id: item.product.id,
            calories: item.product.nutritional_value.calories,
            amount: item.amount,
            price: item.product.price,
        })),
        customMeals: customMeals.map(item => ({
            ingredients: item.product.ingredients.map(ing => ({
                id: ing.id,
                weight: ing.weight_grams,
            })),
            amount: item.amount,
            price: item.product.price,
        }))
    };

    fetch('/checkout/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
        body: JSON.stringify(cartData),
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                storage.clearCart();
                updateCartUI();
                utils.updateOrderSummary();
                window.location.href = data.redirect_url;
            } else {
                alert(data.error);
            }
        })
        .catch(error => console.error('Error:', error));
}

function updateCartControls() {
    const paymentTypeSelect = document.getElementById('paymentType');
    const checkoutButton = document.getElementById('checkoutButton');
    const {officialMeals, customMeals} = storage.getCartItemsSet();

    if (officialMeals.length === 0 && customMeals.length === 0) {
        paymentTypeSelect.style.display = 'none';
        checkoutButton.disabled = true;
        checkoutButton.classList.add('btn-secondary');
        checkoutButton.classList.remove('btn-primary');
    } else {
        paymentTypeSelect.style.display = 'block';
        checkoutButton.disabled = false;
        checkoutButton.classList.add('btn-primary');
        checkoutButton.classList.remove('btn-secondary');
    }
}