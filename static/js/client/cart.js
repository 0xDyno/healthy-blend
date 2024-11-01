// cart.js

import storage from './storage.js';
import * as utils from './utils.js';

let currentDiscount = 0;
let maxDiscount = 0;

document.addEventListener('DOMContentLoaded', function () {
    updateCartUI();
    utils.updateOrderSummary();

    document.getElementById('checkoutButton').addEventListener('click', handleCheckout);
    document.getElementById('checkPromoButton').addEventListener('click', handlePromoCheck);
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

        // Calculate tax and service charge
        const serviceChargeRate = 0.01; // 1% service charge
        const taxRate = 0.07; // 7% tax rate

        // Новый расчет скидки с учетом максимального значения
        let discountAmount = total * currentDiscount;
        if (maxDiscount > 0 && discountAmount > maxDiscount) {
            discountAmount = maxDiscount;
            currentDiscount = maxDiscount / total; // Пересчитываем процент скидки
        }

        const subtotalAfterDiscount = total - discountAmount;
        const only_service = subtotalAfterDiscount * serviceChargeRate;
        const service_and_tax = (subtotalAfterDiscount + only_service) * taxRate;
        const totalPrice = subtotalAfterDiscount + only_service + service_and_tax;

        // Add row for subtotal
        const subtotalRow = document.createElement('tr');
        subtotalRow.innerHTML = `
            <td colspan="4" style="text-align: left;">Subtotal:</td>
            <td>${utils.formatNumber(total,0)} IDR</td>
            <td></td>
        `;
        tableBody.appendChild(subtotalRow);

        // Add row for discount if applicable
        if (currentDiscount > 0) {
            const discountRow = document.createElement('tr');
            discountRow.innerHTML = `
                <td colspan="4" style="text-align: left;">Discount:</td>
                <td>-${utils.formatNumber(discountAmount,0)} IDR</td>
                <td></td>
            `;
            tableBody.appendChild(discountRow);
        }

        // Add row for service charge
        const taxRow = document.createElement('tr');
        taxRow.innerHTML = `
            <td colspan="4" style="text-align: left;">Service (${utils.formatNumber(serviceChargeRate * 100, 0)}%):</td>
            <td>${utils.formatNumber(only_service,0)} IDR</td>
            <td></td>
        `;
        tableBody.appendChild(taxRow);

        const serviceRow = document.createElement('tr');
        serviceRow.innerHTML = `
            <td colspan="4" style="text-align: left;">Tax (${utils.formatNumber(taxRate * 100, 0)}%):</td>
            <td>${utils.formatNumber(service_and_tax,0)} IDR</td>
            <td></td>
        `;
        tableBody.appendChild(serviceRow);

        addRemoveEventListeners();
        cartTotalElement.textContent = `Total: ${utils.formatNumber(totalPrice, 0)} IDR`;
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

function handlePromoCheck() {
    const promoCode = document.getElementById('promoCode').value.trim();

    if (!promoCode) {
        alert('Please enter a promo code');
        return;
    }


    fetch(`/api/check/promo/${promoCode}/`)
        .then(response => response.json())
        .then(data => {
            if (data.messages) {
                MessageManager.handleAjaxMessages(data.messages);
            }

            if (data.is_active) {
                currentDiscount = data.discount;
                maxDiscount = data.max_discount || 0;
            } else {
                currentDiscount = 0;
                maxDiscount = 0;
            }
            updateCartUI();
        })
        .catch(error => {
            console.error('Error:', error);
            currentDiscount = 0;
            updateCartUI();
        });
}

function handleCheckout() {
    const paymentType = document.getElementById('paymentType').value;
    const promoCode = document.getElementById('promoCode').value.trim();

    if (!paymentType) {
        alert('Please select a payment type');
        return;
    }

    const {officialMeals, customMeals} = storage.getCartItemsSet();
    let nutritions = utils.calculateNutritionSummary([...officialMeals, ...customMeals])
    delete nutritions.total

    const rawPrice = storage.getRawPrice();
    const discountedPrice = rawPrice * (1 - currentDiscount);
    const serviceCharge = discountedPrice * 0.01;
    const tax = (discountedPrice + serviceCharge) * 0.07;
    const totalPrice = discountedPrice + serviceCharge + tax;

    const cartData = {
        base_price: rawPrice,
        final_price: totalPrice,
        payment_type: paymentType,
        promo_code: promoCode,
        nutritional_value: nutritions,
        official_meals: officialMeals.map(item => ({
            id: item.product.id,
            calories: item.product.nutritional_value.calories,
            amount: item.amount,
            price: item.product.price,
            weight: item.product.weight,
            do_blend: true,
        })),
        custom_meals: customMeals.map(item => ({
            ingredients: item.product.ingredients.map(ing => ({
                id: ing.id,
                weight: ing.weight_grams,
            })),
            amount: item.amount,
            price: item.product.price,
            weight: item.product.weight,
            do_blend: true,
        }))
    };

    fetch('/api/checkout/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
        body: JSON.stringify(cartData),
    })
        .then(async response => {
            const data = await response.json()
            if (response.ok) {
                storage.clearCart();
                updateCartControls()
                window.location.href = data.redirect_url;
            } else {
                if (data.messages) {
                    MessageManager.handleAjaxMessages(data.messages)
                }
            }
        })
        .catch(error => console.error('Error:', error));
}

function updateCartControls() {
    const paymentTypeSelect = document.getElementById('paymentType');
    const promoCodeContainer = document.getElementById('promoCodeContainer');
    const checkoutButton = document.getElementById('checkoutButton');
    const {officialMeals, customMeals} = storage.getCartItemsSet();

    if (officialMeals.length === 0 && customMeals.length === 0) {
        paymentTypeSelect.style.display = 'none';
        promoCodeContainer.style.display = 'none'; // Скрываем поле промокода
        checkoutButton.disabled = true;
        checkoutButton.classList.add('btn-secondary');
        checkoutButton.classList.remove('btn-primary');
    } else {
        paymentTypeSelect.style.display = 'block';
        promoCodeContainer.style.display = 'block'; // Показываем поле промокода
        checkoutButton.disabled = false;
        checkoutButton.classList.add('btn-primary');
        checkoutButton.classList.remove('btn-secondary');
    }
}